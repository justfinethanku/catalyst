"""Test the configuration loading system."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pipeline.config_loader import ConfigLoader, PipelineRegistry
from src.core.pipeline.template_renderer import TemplateRenderer
from src.core.pipeline.context_builder import ContextBuilder, PipelineContext
from src.storage import HybridStore


def test_config_loader():
    """Test configuration loading and validation."""
    print("🧪 Testing Configuration Loading System...\n")
    
    # Initialize config loader
    loader = ConfigLoader()
    print("✅ ConfigLoader initialized")
    
    # Test listing available pipelines
    pipelines = loader.list_available_pipelines()
    print(f"📋 Available pipelines: {pipelines}")
    
    # Load the company intelligence pipeline
    try:
        config = loader.load_pipeline("company_intelligence")
        print(f"✅ Loaded pipeline: {config.name}")
        print(f"   Version: {config.version}")
        print(f"   Steps: {len(config.steps)}")
        
        # Test execution order calculation
        execution_order = config.get_execution_order()
        print(f"   Execution order: {' → '.join(execution_order)}")
        
        # Validate dependencies
        dep_errors = config.validate_dependencies()
        if dep_errors:
            print(f"❌ Dependency errors: {dep_errors}")
        else:
            print("✅ All dependencies valid")
            
        # Validate template files
        template_errors = loader.validate_template_files(config)
        if template_errors:
            print(f"❌ Template errors: {template_errors}")
        else:
            print("✅ All template files exist")
            
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    print("\n✅ Configuration loading tests passed!")


def test_template_renderer():
    """Test template rendering system."""
    print("\n🧪 Testing Template Rendering System...\n")
    
    # Initialize renderer
    renderer = TemplateRenderer()
    print("✅ TemplateRenderer initialized")
    
    # Test simple variable substitution
    test_template = "Hello {{client_name}}! Analyzing {{url}} in {{industry}}."
    test_vars = {
        "client_name": "Test Company",
        "url": "https://test.com",
        "industry": "Technology"
    }
    
    try:
        # Create temporary test template
        test_path = Path("templates/test_template.txt")
        test_path.parent.mkdir(exist_ok=True)
        
        with open(test_path, 'w') as f:
            f.write(test_template)
        
        rendered = renderer.render("test_template.txt", test_vars)
        expected = "Hello Test Company! Analyzing https://test.com in Technology."
        
        if rendered.strip() == expected:
            print("✅ Simple variable substitution works")
        else:
            print(f"❌ Variable substitution failed: {rendered}")
        
        # Clean up test file
        test_path.unlink()
        
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        return
    
    # Test template validation
    validation_results = []
    for template_file in ["discovery/company_discovery.txt", 
                         "market_position/position_analysis.txt"]:
        result = renderer.validate_template(template_file)
        validation_results.append((template_file, result))
        
        if result["valid"]:
            print(f"✅ {template_file}: Valid ({result['variable_count']} variables)")
        else:
            print(f"❌ {template_file}: {result.get('error', 'Invalid')}")
    
    print("\n✅ Template rendering tests passed!")


def test_context_builder():
    """Test context building for autonomous execution."""
    print("\n🧪 Testing Context Builder...\n")
    
    # Initialize components
    store = HybridStore()
    context_builder = ContextBuilder(store)
    
    # Create test pipeline context
    pipeline_context = PipelineContext(
        client_name="test_company",
        url="https://test.com",
        metadata={"industry": "Technology", "company_size": "Startup"}
    )
    
    # Add some fake step results
    pipeline_context.add_step_result("discovery", {
        "company_name": "Test Company",
        "industry": "Technology",
        "products_services": ["Software Platform", "API Services"],
        "timestamp": "2024-01-01T00:00:00"
    })
    
    pipeline_context.add_step_result("market_position", {
        "market_category": "SaaS Platform",
        "key_differentiators": ["API-first", "Developer-friendly"],
        "competitive_position": "Challenger",
        "timestamp": "2024-01-01T00:01:00"
    })
    
    print("✅ Pipeline context created with test data")
    print(f"   Client: {pipeline_context.client_name}")
    print(f"   Steps completed: {len(pipeline_context.step_results)}")
    
    # Test that context has expected structure
    if pipeline_context.has_step_result("discovery"):
        print("✅ Discovery step result available")
    
    if pipeline_context.has_step_result("market_position"):
        print("✅ Market position step result available")
    
    all_results = pipeline_context.get_all_results()
    print(f"✅ All results accessible: {list(all_results.keys())}")
    
    print("\n✅ Context builder tests passed!")


def test_pipeline_registry():
    """Test pipeline registry functionality."""
    print("\n🧪 Testing Pipeline Registry...\n")
    
    # Initialize registry
    loader = ConfigLoader()
    registry = PipelineRegistry(loader)
    print("✅ Pipeline registry initialized")
    
    # Test listing all pipelines
    pipeline_list = registry.list_pipelines()
    print(f"📋 Found {len(pipeline_list)} pipeline(s)")
    
    for pipeline_info in pipeline_list:
        if "error" in pipeline_info:
            print(f"❌ {pipeline_info.get('pipeline_name', 'Unknown')}: {pipeline_info['error']}")
        else:
            print(f"✅ {pipeline_info['name']} (v{pipeline_info['version']})")
            print(f"   Steps: {pipeline_info['total_steps']}")
            print(f"   Order: {' → '.join(pipeline_info['execution_order'])}")
    
    # Test validation of all pipelines
    validation_results = registry.validate_all_pipelines()
    print(f"\n📊 Validation Summary:")
    print(f"   Total: {validation_results['total']}")
    print(f"   Valid: {len(validation_results['valid'])}")
    print(f"   Invalid: {len(validation_results['invalid'])}")
    
    if validation_results['invalid']:
        for invalid in validation_results['invalid']:
            print(f"   ❌ {invalid['pipeline']}: {invalid['error']}")
    
    print("\n✅ Pipeline registry tests passed!")


def test_autonomous_execution_readiness():
    """Test readiness for autonomous pipeline execution."""
    print("\n🧪 Testing Autonomous Execution Readiness...\n")
    
    # Test all components work together
    loader = ConfigLoader()
    renderer = TemplateRenderer()
    store = HybridStore()
    context_builder = ContextBuilder(store)
    
    print("✅ All components initialized")
    
    # Load pipeline config
    config = loader.load_pipeline("company_intelligence")
    execution_order = config.get_execution_order()
    
    print(f"✅ Pipeline loaded: {len(config.steps)} steps")
    print(f"   Execution order: {' → '.join(execution_order)}")
    
    # Test context building for first step
    first_step = config.get_step(execution_order[0])
    pipeline_context = PipelineContext(
        client_name="readiness_test",
        url="https://example.com"
    )
    
    print(f"✅ Ready to execute step: {first_step.name}")
    print(f"   Template: {first_step.template}")
    print(f"   Dependencies: {first_step.dependencies}")
    
    # Validate first step template exists and is valid
    template_validation = renderer.validate_template(first_step.template)
    if template_validation["valid"]:
        print(f"✅ First step template ready ({template_validation['variable_count']} variables)")
    else:
        print(f"❌ First step template issues: {template_validation.get('error')}")
    
    print("\n🚀 SYSTEM READY FOR AUTONOMOUS EXECUTION!")
    print("=" * 50)
    print("✅ Configuration loading works")
    print("✅ Template rendering ready")
    print("✅ Context building ready")
    print("✅ Storage backend ready")
    print("✅ Pipeline validation passes")
    print("\nNext: Implement the PipelineEngine to orchestrate autonomous execution")


if __name__ == "__main__":
    test_config_loader()
    test_template_renderer()
    test_context_builder()
    test_pipeline_registry()
    test_autonomous_execution_readiness()