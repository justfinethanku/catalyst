"""Template rendering system for pipeline prompts."""
import re
from pathlib import Path
from typing import Dict, Any, Optional
import json


class TemplateRenderer:
    """Renders prompt templates with variable substitution and context building."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize template renderer."""
        self.templates_dir = Path(templates_dir)
        
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory not found: {templates_dir}")
    
    def render(self, 
               template_path: str, 
               variables: Dict[str, Any],
               context_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a template with variables and context.
        
        Args:
            template_path: Path to template relative to templates_dir
            variables: Variables to substitute in template
            context_data: Previous step results for context building
            
        Returns:
            Rendered template string
            
        Raises:
            FileNotFoundError: If template file not found
            ValueError: If template rendering fails
        """
        full_path = self.templates_dir / template_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Template not found: {full_path}")
        
        # Load template content
        with open(full_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Prepare rendering variables
        render_vars = variables.copy()
        
        # Add context data if provided
        if context_data:
            render_vars.update(context_data)
        
        try:
            # Render template with variables
            rendered = self._render_template(template_content, render_vars)
            
            # Post-process the rendered template
            rendered = self._post_process(rendered)
            
            return rendered
            
        except Exception as e:
            raise ValueError(f"Template rendering failed for {template_path}: {e}")
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Core template rendering logic."""
        rendered = template
        
        # 1. Handle context blocks ({{#context_key}} ... {{/context_key}})
        rendered = self._render_context_blocks(rendered, variables)
        
        # 2. Handle conditional blocks ({{#if condition}} ... {{/if}})
        rendered = self._render_conditional_blocks(rendered, variables)
        
        # 3. Handle simple variable substitution ({{variable_name}})
        rendered = self._render_variables(rendered, variables)
        
        # 4. Handle nested object access ({{object.property}})
        rendered = self._render_nested_variables(rendered, variables)
        
        return rendered
    
    def _render_context_blocks(self, template: str, variables: Dict[str, Any]) -> str:
        """Render context blocks that include previous step data."""
        # Pattern: {{#step_name}} content {{/step_name}}
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'
        
        def replace_context_block(match):
            context_key = match.group(1)
            block_content = match.group(2)
            
            # Check if we have data for this context
            if context_key in variables:
                context_data = variables[context_key]
                
                # If context data exists, render the block with that data
                if context_data:
                    return self._render_block_with_context(block_content, context_data)
                else:
                    return ""  # No data, remove block
            else:
                return ""  # No context available, remove block
        
        return re.sub(pattern, replace_context_block, template, flags=re.DOTALL)
    
    def _render_conditional_blocks(self, template: str, variables: Dict[str, Any]) -> str:
        """Render conditional if/else blocks."""
        # Pattern: {{#if condition}} content {{/if}}
        pattern = r'\{\{#if\s+(\w+(?:\.\w+)*)\}\}(.*?)\{\{/if\}\}'
        
        def replace_conditional(match):
            condition = match.group(1)
            block_content = match.group(2)
            
            # Evaluate condition
            condition_value = self._get_nested_value(variables, condition)
            
            if self._is_truthy(condition_value):
                return block_content
            else:
                return ""
        
        return re.sub(pattern, replace_conditional, template, flags=re.DOTALL)
    
    def _render_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Render simple variable substitutions."""
        # Pattern: {{variable_name}}
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_variable(match):
            var_name = match.group(1)
            
            if var_name in variables:
                value = variables[var_name]
                return self._format_value(value)
            else:
                return f"[{var_name} not found]"
        
        return re.sub(pattern, replace_variable, template)
    
    def _render_nested_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Render nested object variable access."""
        # Pattern: {{object.property.subproperty}}
        pattern = r'\{\{(\w+(?:\.\w+)+)\}\}'
        
        def replace_nested_variable(match):
            var_path = match.group(1)
            
            value = self._get_nested_value(variables, var_path)
            
            if value is not None:
                return self._format_value(value)
            else:
                return f"[{var_path} not found]"
        
        return re.sub(pattern, replace_nested_variable, template)
    
    def _render_block_with_context(self, block_content: str, context_data: Any) -> str:
        """Render a block with context data available."""
        if isinstance(context_data, dict):
            # For dict context, make all keys available as variables
            return self._render_template(block_content, context_data)
        elif isinstance(context_data, list):
            # For list context, render block for each item
            rendered_items = []
            for item in context_data:
                if isinstance(item, dict):
                    rendered_items.append(self._render_template(block_content, item))
                else:
                    # Simple list item
                    rendered_items.append(self._render_template(block_content, {"item": item}))
            return "\n".join(rendered_items)
        else:
            # Simple value context
            return self._render_template(block_content, {"value": context_data})
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dict using dot notation."""
        keys = path.split('.')
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except (KeyError, TypeError):
            return None
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy for conditional rendering."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (str, list, dict)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0
        return bool(value)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for template output."""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (list, dict)):
            # For complex objects, format as JSON if they're not too large
            try:
                json_str = json.dumps(value, indent=2)
                if len(json_str) > 1000:  # If too large, summarize
                    if isinstance(value, list):
                        return f"[{len(value)} items]"
                    else:
                        return f"{{{len(value)} fields}}"
                return json_str
            except (TypeError, ValueError):
                return str(value)
        else:
            return str(value)
    
    def _post_process(self, rendered: str) -> str:
        """Post-process rendered template."""
        # Remove empty lines that might have been created by conditional blocks
        lines = rendered.split('\n')
        processed_lines = []
        
        for line in lines:
            # Keep non-empty lines and lines with only whitespace if they have content
            if line.strip() or (processed_lines and processed_lines[-1].strip()):
                processed_lines.append(line)
        
        # Join and clean up excessive newlines
        result = '\n'.join(processed_lines)
        
        # Remove excessive consecutive newlines (more than 2)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def validate_template(self, template_path: str) -> Dict[str, Any]:
        """Validate a template file for syntax and structure."""
        full_path = self.templates_dir / template_path
        
        if not full_path.exists():
            return {
                "valid": False,
                "error": f"Template file not found: {full_path}"
            }
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for basic template syntax issues
            issues = []
            
            # Check for unmatched braces
            open_braces = content.count('{{')
            close_braces = content.count('}}')
            if open_braces != close_braces:
                issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
            
            # Check for unmatched conditional blocks
            if_blocks = len(re.findall(r'\{\{#if\s+\w+\}\}', content))
            endif_blocks = len(re.findall(r'\{\{/if\}\}', content))
            if if_blocks != endif_blocks:
                issues.append(f"Unmatched if blocks: {if_blocks} #if, {endif_blocks} /if")
            
            # Check for unmatched context blocks
            context_opens = len(re.findall(r'\{\{#(\w+)\}\}', content))
            context_closes = len(re.findall(r'\{\{/(\w+)\}\}', content))
            if context_opens != context_closes:
                issues.append(f"Unmatched context blocks: {context_opens} opens, {context_closes} closes")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "size": len(content),
                "variable_count": len(re.findall(r'\{\{(\w+(?:\.\w+)*)\}\}', content))
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Template validation error: {e}"
            }