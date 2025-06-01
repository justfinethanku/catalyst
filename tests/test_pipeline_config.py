"""Test pipeline configuration loading."""
import yaml
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_pipeline_config_loading():
    """Test loading and validating pipeline configuration."""
    print("🧪 Testing Pipeline Configuration...\n")
    
    # Load pipeline config
    config_path = Path("config/pipelines/company_intelligence.yaml")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Pipeline config loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Validate config structure
    pipeline = config.get('pipeline', {})
    print(f"📋 Pipeline: {pipeline.get('name')}")
    print(f"📋 Version: {pipeline.get('version')}")
    print(f"📋 Description: {pipeline.get('description')}")
    
    # Validate steps
    steps = pipeline.get('steps', [])
    print(f"\n📊 Found {len(steps)} pipeline steps:")
    
    for i, step in enumerate(steps, 1):
        step_id = step.get('id')
        step_name = step.get('name')
        dependencies = step.get('dependencies', [])
        template = step.get('template')
        
        print(f"  {i}. {step_id}: {step_name}")
        print(f"     Dependencies: {dependencies if dependencies else 'None'}")
        print(f"     Template: {template}")
        
        # Check if template file exists
        template_path = Path(f"templates/{template}")
        if template_path.exists():
            print(f"     ✅ Template file exists")
        else:
            print(f"     ❌ Template file missing")
        print()
    
    # Validate dependency order
    print("🔗 Dependency Validation:")
    step_ids = [step['id'] for step in steps]
    
    for step in steps:
        step_id = step['id']
        dependencies = step.get('dependencies', [])
        
        for dep in dependencies:
            if dep not in step_ids:
                print(f"❌ {step_id} depends on unknown step: {dep}")
            else:
                dep_index = step_ids.index(dep)
                step_index = step_ids.index(step_id)
                if dep_index > step_index:
                    print(f"❌ {step_id} depends on later step: {dep}")
                else:
                    print(f"✅ {step_id} → {dep} (valid dependency)")
    
    print("\n✅ Pipeline configuration test complete!")


def test_template_availability():
    """Test that all referenced templates exist."""
    print("\n🧪 Testing Template Availability...\n")
    
    # Get all template references from config
    config_path = Path("config/pipelines/company_intelligence.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    steps = config['pipeline']['steps']
    templates_found = 0
    templates_missing = 0
    
    for step in steps:
        template_ref = step.get('template')
        template_path = Path(f"templates/{template_ref}")
        
        if template_path.exists():
            templates_found += 1
            print(f"✅ {template_ref}")
            
            # Check template size (should be substantial)
            size = template_path.stat().st_size
            if size > 1000:  # At least 1KB
                print(f"   📏 Size: {size:,} bytes (good)")
            else:
                print(f"   ⚠️  Size: {size:,} bytes (might be too small)")
        else:
            templates_missing += 1
            print(f"❌ {template_ref} - FILE MISSING")
    
    print(f"\n📊 Template Summary:")
    print(f"   Found: {templates_found}")
    print(f"   Missing: {templates_missing}")
    print(f"   Total: {templates_found + templates_missing}")


if __name__ == "__main__":
    test_pipeline_config_loading()
    test_template_availability()