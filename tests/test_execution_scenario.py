"""Test realistic autonomous execution scenario."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pipeline.config_loader import ConfigLoader
from src.core.pipeline.template_renderer import TemplateRenderer
from src.core.pipeline.context_builder import ContextBuilder, PipelineContext
from src.storage import HybridStore


async def test_realistic_execution_scenario():
    """Test a realistic autonomous execution scenario."""
    print("🧪 TESTING REALISTIC AUTONOMOUS EXECUTION SCENARIO")
    print("=" * 60)
    
    # Initialize all components
    loader = ConfigLoader()
    renderer = TemplateRenderer()
    store = HybridStore()
    context_builder = ContextBuilder(store)
    
    # Load pipeline
    config = loader.load_pipeline("company_intelligence")
    execution_order = config.get_execution_order()
    
    # Simulate autonomous execution for a company
    client_name = "acme_corp"
    url = "https://acme.com"
    
    print(f"\n🎯 TARGET COMPANY: {client_name}")
    print(f"🔗 URL: {url}")
    print(f"📋 PIPELINE: {config.name}")
    print(f"🔄 EXECUTION ORDER: {' → '.join(execution_order)}")
    
    # Initialize pipeline context
    pipeline_context = PipelineContext(
        client_name=client_name,
        url=url,
        metadata={
            "analysis_date": "2024-01-15",
            "analyst": "autonomous_system",
            "priority": "high"
        }
    )
    
    print(f"\n📊 SIMULATION: Autonomous Step-by-Step Execution")
    print("-" * 50)
    
    # Simulate each step execution
    for i, step_id in enumerate(execution_order, 1):
        step = config.get_step(step_id)
        
        print(f"\n{i}. EXECUTING: {step.name}")
        print(f"   Step ID: {step_id}")
        print(f"   Template: {step.template}")
        print(f"   Dependencies: {step.dependencies if step.dependencies else 'None'}")
        
        # Build context for this step
        step_context = await context_builder.build_step_context(
            step=step,
            pipeline_context=pipeline_context,
            config=config.settings
        )
        
        print(f"   Context variables: {len(step_context)} items")
        print(f"     - client_name: {step_context.get('client_name')}")
        print(f"     - url: {step_context.get('url')}")
        
        # Show dependency context
        if step.dependencies:
            print(f"     - Dependencies available:")
            for dep in step.dependencies:
                if dep in step_context:
                    print(f"       ✅ {dep}: Available")
                else:
                    print(f"       ❌ {dep}: Missing")
        
        # Render the prompt template
        try:
            rendered_prompt = renderer.render(
                template_path=step.template,
                variables=step_context
            )
            
            prompt_size = len(rendered_prompt)
            print(f"   ✅ Template rendered: {prompt_size:,} characters")
            
            # Show a sample of the rendered prompt
            sample = rendered_prompt[:200].replace('\n', ' ')
            print(f"   📝 Prompt preview: {sample}...")
            
        except Exception as e:
            print(f"   ❌ Template rendering failed: {e}")
            continue
        
        # Simulate LLM execution and result storage
        print(f"   🤖 [SIMULATED] LLM processing...")
        print(f"   🤖 [SIMULATED] Web search enabled: {step.config.get('web_search_queries', 'No')}")
        
        # Create mock result for this step
        mock_result = create_mock_step_result(step_id, client_name, url)
        
        # Store result in context
        pipeline_context.add_step_result(step_id, mock_result)
        
        # Simulate vector storage (store is sync, not async)
        doc_id = store.store(
            content=f"Mock {step_id} analysis for {client_name}",
            metadata={
                "client": client_name,
                "step": step_id,
                "pipeline": config.name,
                "url": url
            },
            client_name=client_name
        )
        
        print(f"   💾 Stored in vector DB: {doc_id[:8]}...")
        print(f"   ✅ Step completed successfully")
    
    print(f"\n🎉 AUTONOMOUS EXECUTION COMPLETE!")
    print("=" * 40)
    
    # Show execution summary
    all_results = pipeline_context.get_all_results()
    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Total steps executed: {len(all_results)}")
    print(f"   Client: {pipeline_context.client_name}")
    print(f"   Steps completed: {', '.join(all_results.keys())}")
    
    # Show what would happen next
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Generate final intelligence report")
    print(f"   2. Store complete analysis in vector DB")
    print(f"   3. Generate executive summary")
    print(f"   4. Export to PDF/JSON formats")
    print(f"   5. Ready for next company analysis")
    
    # Test cross-client intelligence
    print(f"\n🧠 TESTING CROSS-CLIENT INTELLIGENCE:")
    
    # Simulate another company to show compound learning
    clients = store.get_all_clients()
    if len(clients) > 1:
        print(f"   Database contains {len(clients)} clients: {', '.join(clients)}")
        
        # Test similarity search
        similar = store.search(
            query="company analysis business model",
            n_results=3
        )
        
        if similar:
            print(f"   Found {len(similar)} similar analyses:")
            for i, result in enumerate(similar[:2], 1):
                client = result['metadata'].get('client', 'Unknown')
                step = result['metadata'].get('step', 'Unknown')
                distance = result.get('distance', 1.0)
                relevance = (1 - distance) * 100
                print(f"     {i}. {client} ({step}) - {relevance:.1f}% relevant")
        
        print(f"   ✅ System learning from {len(clients)} companies")
    else:
        print(f"   Note: Need multiple companies to demonstrate compound learning")
    
    print(f"\n✅ REALISTIC EXECUTION SCENARIO COMPLETE!")


def create_mock_step_result(step_id: str, client_name: str, url: str) -> dict:
    """Create mock step results for testing."""
    base_result = {
        "step_id": step_id,
        "client_name": client_name,
        "url": url,
        "timestamp": "2024-01-15T10:00:00",
        "status": "completed"
    }
    
    # Step-specific mock data
    if step_id == "discovery":
        base_result.update({
            "company_name": client_name.replace("_", " ").title(),
            "industry": "Technology",
            "products_services": ["Software Platform", "API Services"],
            "business_model": "SaaS",
            "target_market": "Enterprise"
        })
    
    elif step_id == "market_position":
        base_result.update({
            "market_category": "Enterprise Software",
            "competitive_position": "Challenger",
            "key_differentiators": ["API-first", "Developer-friendly"],
            "market_size": "Large"
        })
    
    elif step_id == "audience_insights":
        base_result.update({
            "primary_audiences": ["CTOs", "Engineering Managers", "Developers"],
            "use_cases": ["System Integration", "Data Processing"],
            "buyer_personas": ["Technical Decision Maker", "Budget Approver"]
        })
    
    elif step_id == "competitive_landscape":
        base_result.update({
            "direct_competitors": ["Competitor A", "Competitor B"],
            "competitive_advantages": ["Better API", "Lower Cost"],
            "market_opportunities": ["Mobile Integration", "AI Features"]
        })
    
    elif step_id == "strategic_synthesis":
        base_result.update({
            "strategic_recommendations": ["Focus on API excellence", "Expand mobile offering"],
            "key_insights": ["Strong technical foundation", "Growth opportunity in SMB"],
            "priority_actions": ["Improve documentation", "Add mobile SDK"]
        })
    
    return base_result


def main():
    """Run the test scenario."""
    import asyncio
    asyncio.run(test_realistic_execution_scenario())


if __name__ == "__main__":
    main()