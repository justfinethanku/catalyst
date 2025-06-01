"""Search components module for the autonomous pipeline system."""
import streamlit as st


def render_quick_search():
    """Render the quick intelligence search and analytics."""
    st.header("Quick Intelligence Search")
    
    search_query = st.text_input("Search across all analyses")
    
    if search_query:
        with st.spinner("Searching..."):
            results = st.session_state.storage.search(
                query=search_query,
                n_results=5
            )
        
        if results:
            st.write(f"Found {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"{i}. {result['metadata'].get('client', 'Unknown')}"):
                    st.write("**Content:**")
                    st.write(result["content"][:200] + "...")
                    
                    st.write("**Metadata:**")
                    st.json(result["metadata"])
                    
                    relevance = (1 - result.get("distance", 1)) * 100
                    st.write(f"**Relevance:** {relevance:.1f}%")
        else:
            st.write("No results found")
    
    # Intelligence insights
    clients = st.session_state.storage.get_all_clients()
    if clients:
        st.header("Intelligence Insights")
        
        # Simple analytics
        industries = {}
        for client in clients:
            # Try to get industry from stored data
            client_results = st.session_state.storage.search(
                query=f"industry {client}",
                filter_client=client,
                n_results=1
            )
            
            if client_results:
                # TODO: extract actual industry from analysis results
                industry = client_results[0].get('metadata', {}).get('industry', 'Unknown')
                industries[client] = industry
        
        if industries:
            st.write("**Industries Analyzed:**")
            industry_counts = {}
            for industry in industries.values():
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
            
            for industry, count in industry_counts.items():
                st.write(f"• {industry}: {count} companies")