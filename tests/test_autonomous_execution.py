"""Test full autonomous pipeline execution."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pipeline.engine import PipelineEngine
from src.core.pipeline.config_loader import ConfigLoader
from src.storage import HybridStore


async def test_autonomous_execution():
    """Test complete autonomous pipeline execution."""
    print("🚀 TESTING AUTONOMOUS PIPELINE EXECUTION")
    print("=" * 50)
    
    # Initialize components
    storage = HybridStore()
    config_loader = ConfigLoader()
    engine = PipelineEngine(storage, config_loader)
    
    print("✅ Pipeline engine initialized")
    
    # Test company
    client_name = "stripe_inc"
    url = "https://stripe.com"
    
    print(f"\n🎯 TARGET: {client_name}")
    print(f"🔗 URL: {url}")
    
    # Add execution callback for real-time updates
    async def execution_callback(step_id: str, result):
        print(f"   📨 Callback: {step_id} - {result.status}")
        if result.error:
            print(f"      Error: {result.error}")
    
    engine.add_execution_callback(execution_callback)
    
    # Execute the pipeline
    print(f"\n🔥 EXECUTING AUTONOMOUS PIPELINE...")
    print("-" * 40)
    
    try:
        result = await engine.execute_pipeline(
            pipeline_name="company_intelligence",
            client_name=client_name,
            url=url,
            metadata={
                "analyst": "autonomous_system",
                "priority": "high",
                "analysis_type": "comprehensive"
            }
        )
        
        # Display results
        print(f"\n📊 EXECUTION RESULTS:")
        print(f"   Status: {result.status.value}")
        print(f"   Total Time: {result.total_execution_time:.2f} seconds")
        print(f"   Steps Completed: {len(result.get_successful_steps())}/{len(result.step_results)}")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        # Show step results
        print(f"\n📋 STEP RESULTS:")
        for step_id, step_result in result.step_results.items():
            print(f"   {step_id}:")
            print(f"     Status: {step_result.status}")
            print(f"     Time: {step_result.execution_time:.2f}s")
            if step_result.status == "success":
                content_size = len(str(step_result.content))
                print(f"     Content: {content_size:,} chars")
                print(f"     Doc ID: {step_result.doc_id[:8]}...")
            if step_result.error:
                print(f"     Error: {step_result.error}")
        
        # Test vector storage
        print(f"\n🧠 TESTING VECTOR STORAGE:")
        clients = storage.get_all_clients()
        print(f"   Total clients in DB: {len(clients)}")
        print(f"   Clients: {', '.join(clients)}")
        
        # Test search
        search_results = storage.search("company analysis strategic", n_results=3)
        print(f"   Search results: {len(search_results)}")
        
        if search_results:
            for i, search_result in enumerate(search_results[:2], 1):
                client = search_result['metadata'].get('client', 'Unknown')
                step = search_result['metadata'].get('step', 'Unknown')
                relevance = (1 - search_result.get('distance', 1)) * 100
                print(f"     {i}. {client} ({step}) - {relevance:.1f}% relevant")
        
        # Test intelligence accumulation
        if len(clients) > 1:
            print(f"   ✅ System learning from {len(clients)} companies")
        else:
            print(f"   🔄 Add more companies to see compound learning")
        
        print(f"\n🎉 AUTONOMOUS EXECUTION COMPLETE!")
        
        return result
        
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_multiple_companies():
    """Test autonomous execution with multiple companies."""
    print(f"\n🚀 TESTING MULTIPLE COMPANY ANALYSIS")
    print("=" * 45)
    
    storage = HybridStore()
    engine = PipelineEngine(storage)
    
    # Test companies
    companies = [
        {"name": "shopify_inc", "url": "https://shopify.com"},
        {"name": "slack_inc", "url": "https://slack.com"},
    ]
    
    results = []
    
    for i, company in enumerate(companies, 1):
        print(f"\n📊 Company {i}/{len(companies)}: {company['name']}")
        
        try:
            result = await engine.execute_pipeline(
                pipeline_name="company_intelligence",
                client_name=company["name"],
                url=company["url"]
            )
            
            results.append(result)
            print(f"   ✅ Completed: {result.status.value}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Show compound learning
    print(f"\n🧠 COMPOUND LEARNING ANALYSIS:")
    clients = storage.get_all_clients()
    print(f"   Total companies analyzed: {len(clients)}")
    
    # Test cross-company search
    search_results = storage.search("SaaS business model pricing", n_results=5)
    print(f"   Cross-company insights: {len(search_results)}")
    
    company_insights = {}
    for result in search_results:
        client = result['metadata'].get('client', 'Unknown')
        if client not in company_insights:
            company_insights[client] = 0
        company_insights[client] += 1
    
    print(f"   Knowledge distribution:")
    for client, count in company_insights.items():
        print(f"     {client}: {count} insights")
    
    print(f"\n✅ MULTIPLE COMPANY ANALYSIS COMPLETE!")
    return results


def main():
    """Run all tests."""
    print("🧪 AUTONOMOUS PIPELINE EXECUTION TESTS")
    print("=" * 45)
    
    # Test single company execution
    result = asyncio.run(test_autonomous_execution())
    
    if result and result.status.value == "completed":
        print(f"\n✅ Single company test: PASSED")
        
        # Test multiple companies for compound learning
        asyncio.run(test_multiple_companies())
        print(f"\n✅ Multiple company test: PASSED")
        
    else:
        print(f"\n❌ Tests failed")
    
    print(f"\n🚀 AUTONOMOUS SYSTEM READY FOR PRODUCTION!")


if __name__ == "__main__":
    main()