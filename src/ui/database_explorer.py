"""Database explorer module for the autonomous pipeline system."""
import streamlit as st


def render_company_explorer():
    """Render the Intelligence Database Explorer with all tabs."""
    clients = st.session_state.storage.get_all_clients()
    
    st.write("---")
    st.header("Intelligence Database Explorer")
    
    # Add tabs for different views
    tab1, tab2, tab3 = st.tabs(["All Companies", "Detailed Search", "Analytics"])
    
    with tab1:
        st.subheader("Complete Company Database")
        
        # Company selector
        selected_company = st.selectbox(
            "Select a company to explore:",
            options=[""] + list(clients),
            format_func=lambda x: x.replace("_", " ").title() if x else "Choose a company..."
        )
        
        if selected_company:
            # Header with delete button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"### {selected_company.replace('_', ' ').title()} Intelligence")
            with col2:
                # Initialize delete confirmation state
                delete_confirm_key = f"delete_confirm_{selected_company}"
                if delete_confirm_key not in st.session_state:
                    st.session_state[delete_confirm_key] = False
                
                if not st.session_state[delete_confirm_key]:
                    if st.button("Delete Client", key=f"delete_{selected_company}", type="secondary"):
                        st.session_state[delete_confirm_key] = True
                        st.rerun()
                else:
                    # Show confirmation buttons
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("Confirm", key=f"confirm_{selected_company}", type="primary"):
                            with st.spinner(f"Deleting all data for {selected_company}..."):
                                # Handle case where storage object doesn't have delete_client method (cached old version)
                                if not hasattr(st.session_state.storage, 'delete_client'):
                                    st.warning("Refreshing storage object...")
                                    from src.storage import HybridStore
                                    st.session_state.storage = HybridStore()
                                    st.info("Storage refreshed with delete functionality")
                                
                                result = st.session_state.storage.delete_client(selected_company)
                            
                            if result["status"] == "success":
                                st.success(f"{result['message']}")
                                st.info(f"Deleted {result['deleted_documents']} documents")
                                # Reset confirmation state
                                st.session_state[delete_confirm_key] = False
                                # Force page refresh to update client list
                                st.rerun()
                            else:
                                st.error(f"{result['message']}")
                                st.session_state[delete_confirm_key] = False
                    
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_{selected_company}", type="secondary"):
                            st.session_state[delete_confirm_key] = False
                            st.rerun()
                    
                    st.warning("This will permanently delete ALL data for this client!")
            
            # Get all data for this company
            company_data = st.session_state.storage.search(
                query="",
                filter_client=selected_company,
                n_results=20
            )
            
            if company_data:
                from src.ui.pdf_components import render_briefing_section
                
                # Intelligence Briefing Section
                render_briefing_section(selected_company)
                
                
                st.write("---")
                
                # Group by step
                steps = {}
                for item in company_data:
                    step = item['metadata'].get('step', 'unknown')
                    if step not in steps:
                        steps[step] = []
                    steps[step].append(item)
                
                # Show each step
                for step, items in steps.items():
                    with st.expander(f"{step.replace('_', ' ').title()}", expanded=False):
                        for idx, item in enumerate(items):
                            st.write("**Analysis Content:**")
                            content = item["content"]
                            if len(content) > 500:
                                st.write(content[:500] + "...")
                                if st.button(f"Show Full {step}", key=f"full_{selected_company}_{step}_{idx}"):
                                    st.write(content)
                            else:
                                st.write(content)
                            
                            st.write("**Metadata:**")
                            st.json(item["metadata"])
                            st.write("---")
    
    with tab2:
        st.subheader("Advanced Intelligence Search")
        
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            advanced_query = st.text_input(
                "Search Query",
                placeholder="e.g., 'competitive advantages', 'pricing model', 'target market'"
            )
        
        with col_b:
            result_count = st.slider("Results", 1, 20, 10)
        
        if advanced_query:
            search_results = st.session_state.storage.search(
                query=advanced_query,
                n_results=result_count
            )
            
            if search_results:
                st.write(f"Found **{len(search_results)}** results:")
                
                for i, result in enumerate(search_results, 1):
                    relevance = (1 - result.get("distance", 1)) * 100
                    client = result['metadata'].get('client', 'Unknown')
                    step = result['metadata'].get('step', 'Unknown')
                    
                    with st.expander(f"{i}. {client} - {step} (Relevance: {relevance:.1f}%)"):
                        st.write("**Content:**")
                        st.write(result["content"])
                        
                        st.write("**Metadata:**")
                        st.json(result["metadata"])
            else:
                st.write("No results found")
    
    with tab3:
        st.subheader("Database Analytics")
        
        # Company count by step
        step_counts = {}
        # Get all data (ChromaDB will return actual count available)
        all_data = st.session_state.storage.search("", n_results=100)
        
        for item in all_data:
            step = item['metadata'].get('step', 'unknown')
            step_counts[step] = step_counts.get(step, 0) + 1
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.write("**Analysis Steps Completed:**")
            for step, count in sorted(step_counts.items()):
                st.write(f"• {step.replace('_', ' ').title()}: {count}")
        
        with col_y:
            st.write("**Database Statistics:**")
            st.metric("Total Companies", len(clients))
            st.metric("Total Analyses", len(all_data))
            st.metric("Average per Company", f"{len(all_data)/len(clients):.1f}" if clients else "0")
            
        # Recent activity
        st.write("**Recent Analysis Activity:**")
        recent_data = sorted(all_data, key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)[:5]
        
        for item in recent_data:
            client = item['metadata'].get('client', 'Unknown')
            step = item['metadata'].get('step', 'Unknown')
            timestamp = item['metadata'].get('timestamp', 'Unknown')
            st.write(f"• {client} - {step} ({timestamp[:10]})")