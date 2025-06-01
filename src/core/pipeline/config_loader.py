"""Configuration loading and validation for autonomous pipelines."""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class StepStatus(Enum):
    """Pipeline step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepConfig:
    """Configuration for a single pipeline step."""
    id: str
    name: str
    description: str
    template: str
    dependencies: List[str]
    config: Dict[str, Any]
    output_fields: List[str]
    status: StepStatus = StepStatus.PENDING
    
    def __post_init__(self):
        """Validate step configuration after initialization."""
        if not self.id:
            raise ValueError("Step ID cannot be empty")
        if not self.template:
            raise ValueError(f"Step {self.id} must have a template")
        if not isinstance(self.dependencies, list):
            raise ValueError(f"Step {self.id} dependencies must be a list")


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    name: str
    version: str
    description: str
    settings: Dict[str, Any]
    steps: List[StepConfig]
    execution: Dict[str, Any]
    output: Dict[str, Any]
    
    def get_step(self, step_id: str) -> Optional[StepConfig]:
        """Get step configuration by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_execution_order(self) -> List[str]:
        """Calculate execution order based on dependencies."""
        order = []
        remaining = {step.id: step for step in self.steps}
        
        while remaining:
            # Find steps with satisfied dependencies
            ready_steps = []
            for step_id, step in remaining.items():
                if all(dep in order for dep in step.dependencies):
                    ready_steps.append(step_id)
            
            if not ready_steps:
                remaining_ids = list(remaining.keys())
                raise ValueError(f"Circular dependencies detected in steps: {remaining_ids}")
            
            # Add ready steps to order (maintain config order for same-level steps)
            ready_steps.sort(key=lambda x: [s.id for s in self.steps].index(x))
            order.extend(ready_steps)
            
            # Remove processed steps
            for step_id in ready_steps:
                del remaining[step_id]
        
        return order
    
    def validate_dependencies(self) -> List[str]:
        """Validate all step dependencies exist."""
        errors = []
        step_ids = {step.id for step in self.steps}
        
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step '{step.id}' depends on unknown step '{dep}'")
        
        return errors


class ConfigLoader:
    """Loads and validates pipeline configurations."""
    
    def __init__(self, config_dir: str = "config/pipelines", templates_dir: str = "templates"):
        """Initialize configuration loader."""
        self.config_dir = Path(config_dir)
        self.templates_dir = Path(templates_dir)
        
        if not self.config_dir.exists():
            raise ValueError(f"Config directory not found: {config_dir}")
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory not found: {templates_dir}")
    
    def load_pipeline(self, pipeline_name: str) -> PipelineConfig:
        """
        Load and validate a pipeline configuration.
        
        Args:
            pipeline_name: Name of the pipeline config file (without .yaml)
            
        Returns:
            Validated PipelineConfig object
            
        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If config file not found
        """
        config_file = self.config_dir / f"{pipeline_name}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Pipeline config not found: {config_file}")
        
        # Load YAML configuration
        with open(config_file, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        if 'pipeline' not in raw_config:
            raise ValueError("Configuration must have 'pipeline' section")
        
        pipeline_data = raw_config['pipeline']
        
        # Parse and validate configuration
        try:
            config = self._parse_pipeline_config(pipeline_data)
            self._validate_configuration(config)
            return config
        except Exception as e:
            raise ValueError(f"Invalid pipeline configuration: {e}")
    
    def list_available_pipelines(self) -> List[str]:
        """List all available pipeline configurations."""
        pipelines = []
        for config_file in self.config_dir.glob("*.yaml"):
            pipelines.append(config_file.stem)
        return sorted(pipelines)
    
    def validate_template_files(self, config: PipelineConfig) -> List[str]:
        """Validate that all referenced template files exist."""
        missing_templates = []
        
        for step in config.steps:
            template_path = self.templates_dir / step.template
            if not template_path.exists():
                missing_templates.append(f"Template not found for step '{step.id}': {step.template}")
        
        return missing_templates
    
    def get_pipeline_summary(self, pipeline_name: str) -> Dict[str, Any]:
        """Get summary information about a pipeline."""
        try:
            config = self.load_pipeline(pipeline_name)
            execution_order = config.get_execution_order()
            
            return {
                "name": config.name,
                "version": config.version,
                "description": config.description,
                "total_steps": len(config.steps),
                "execution_order": execution_order,
                "settings": config.settings,
                "steps_summary": [
                    {
                        "id": step.id,
                        "name": step.name,
                        "dependencies": step.dependencies,
                        "output_fields_count": len(step.output_fields)
                    }
                    for step in config.steps
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "pipeline_name": pipeline_name
            }
    
    def _parse_pipeline_config(self, pipeline_data: Dict[str, Any]) -> PipelineConfig:
        """Parse raw pipeline data into PipelineConfig object."""
        # Parse steps
        steps = []
        for step_data in pipeline_data.get('steps', []):
            step = StepConfig(
                id=step_data['id'],
                name=step_data['name'],
                description=step_data.get('description', ''),
                template=step_data['template'],
                dependencies=step_data.get('dependencies', []),
                config=step_data.get('config', {}),
                output_fields=step_data.get('output_fields', [])
            )
            steps.append(step)
        
        return PipelineConfig(
            name=pipeline_data['name'],
            version=pipeline_data['version'],
            description=pipeline_data.get('description', ''),
            settings=pipeline_data.get('settings', {}),
            steps=steps,
            execution=pipeline_data.get('execution', {}),
            output=pipeline_data.get('output', {})
        )
    
    def _validate_configuration(self, config: PipelineConfig) -> None:
        """Validate pipeline configuration."""
        # Check for duplicate step IDs
        step_ids = [step.id for step in config.steps]
        if len(step_ids) != len(set(step_ids)):
            duplicates = [sid for sid in set(step_ids) if step_ids.count(sid) > 1]
            raise ValueError(f"Duplicate step IDs found: {duplicates}")
        
        # Validate dependencies
        dependency_errors = config.validate_dependencies()
        if dependency_errors:
            raise ValueError(f"Dependency errors: {'; '.join(dependency_errors)}")
        
        # Validate execution order (will raise if circular dependencies)
        try:
            config.get_execution_order()
        except ValueError as e:
            raise ValueError(f"Cannot determine execution order: {e}")
        
        # Validate template references
        template_errors = self.validate_template_files(config)
        if template_errors:
            raise ValueError(f"Template errors: {'; '.join(template_errors)}")


class PipelineRegistry:
    """Registry for managing multiple pipeline configurations."""
    
    def __init__(self, config_loader: ConfigLoader):
        """Initialize pipeline registry."""
        self.loader = config_loader
        self._cached_configs: Dict[str, PipelineConfig] = {}
    
    def get_pipeline(self, pipeline_name: str, use_cache: bool = True) -> PipelineConfig:
        """Get pipeline configuration, with optional caching."""
        if use_cache and pipeline_name in self._cached_configs:
            return self._cached_configs[pipeline_name]
        
        config = self.loader.load_pipeline(pipeline_name)
        
        if use_cache:
            self._cached_configs[pipeline_name] = config
        
        return config
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all available pipelines with summary information."""
        pipeline_summaries = []
        
        for pipeline_name in self.loader.list_available_pipelines():
            summary = self.loader.get_pipeline_summary(pipeline_name)
            pipeline_summaries.append(summary)
        
        return pipeline_summaries
    
    def validate_all_pipelines(self) -> Dict[str, Any]:
        """Validate all available pipeline configurations."""
        results = {
            "valid": [],
            "invalid": [],
            "total": 0
        }
        
        for pipeline_name in self.loader.list_available_pipelines():
            results["total"] += 1
            try:
                self.loader.load_pipeline(pipeline_name)
                results["valid"].append(pipeline_name)
            except Exception as e:
                results["invalid"].append({
                    "pipeline": pipeline_name,
                    "error": str(e)
                })
        
        return results
    
    def clear_cache(self) -> None:
        """Clear cached configurations."""
        self._cached_configs.clear()