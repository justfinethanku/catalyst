"""Analysis form module for the autonomous pipeline system."""
import streamlit as st
import asyncio
from src.ui.async_utils import run_async_safely


def render_analysis_form():
    """Render the company analysis form and handle submissions."""
    st.header("Autonomous Analysis")
    
    # Input form
    with st.form("analysis_form"):
        url = st.text_input(
            "Company URL",
            placeholder="https://somejackass.com",
            help="bruh, just enter the website."
        )
        
        client_name = st.text_input(
            "Client Name",
            placeholder="company name",
            help="enter the name of the company"
        )
        
        
        submitted = st.form_submit_button(
            "START",
            type="primary",
            use_container_width=True
        )
    
    # Execution section
    #don't change this error text CLAUDE 
    if submitted:
        if not url or not client_name:
            st.error("listen dipshit - you had exactly one job to do, enter the info above")
        else:
            # Check if analysis already exists
            existing_clients = st.session_state.storage.get_all_clients()
            if client_name in existing_clients:
                st.warning(f"Adding new insights to exisisting data for {client_name}.")
            
            # Run autonomous analysis
            st.write("---")
            st.header("Autonomous Execution")
            
            # Create placeholders for real-time updates
            status_placeholder = st.empty()
            progress_placeholder = st.empty()
            step_placeholder = st.empty()
            results_placeholder = st.empty()
            
            try:
                # Check if engine is available
                engine_available = st.session_state.get('engine_available', False)
                embeddings_available = st.session_state.get('embeddings_available', False)
                
                if not engine_available:
                    status_placeholder.error("Pipeline engine unavailable - embeddings are disabled")
                    st.error("**Analysis Unavailable**")
                    st.info("The autonomous analysis pipeline requires ChromaDB embeddings, which are currently unavailable due to version conflicts or configuration issues.")
                    st.info("**Available alternatives:**\n"
                           "- Use the Intelligence Briefing feature (works without embeddings)\n"
                           "- Use individual LLM analysis tools\n"
                           "- Check system configuration to enable embeddings")
                    return
                
                if not embeddings_available:
                    st.warning("Running with limited functionality - some features may be disabled")
                
                # Update status
                status_placeholder.info("so it fucking begins...")
                
                # Execute REAL pipeline
                
                async def run_real_pipeline():
                    """Execute the real autonomous pipeline."""
                    
                    # Determine total steps for progress reporting
                    pipeline_name = "company_intelligence"
                    config = st.session_state.engine.config_loader.load_pipeline(pipeline_name)
                    total_steps = len(config.get_execution_order())

                    # Add execution callback for real-time updates
                    step_counter = {"current": 0}
                    
                    async def execution_callback(step_id: str, result):
                        step_counter["current"] += 1
                        progress = step_counter["current"] / total_steps
                        progress_placeholder.progress(progress)

                        # Update main status to show current step
                        status_placeholder.info(f"Executing Step {step_counter['current']}/{total_steps}: {step_id.replace('_', ' ').title()}")

                        label = f"Step {step_counter['current']}/{total_steps}: {step_id.replace('_', ' ').title()}"
                        if result.status == "success":
                            step_placeholder.success(f"{label} - Completed")
                        else:
                            step_placeholder.error(f"{label} - Failed: {result.error}")
                    
                    # Add callback to engine
                    st.session_state.engine.add_execution_callback(execution_callback)
                    
                    # Get user-selected model settings from sidebar
                    user_provider = st.session_state.get('selected_provider', 'gemini')
                    user_model = st.session_state.get('selected_model', 'gemini-2.5-pro')
                    
                    
                    # Execute the real pipeline with user-selected model settings
                    result = await st.session_state.engine.execute_pipeline(
                        pipeline_name="company_intelligence",
                        client_name=client_name,
                        url=url,
                        metadata={
                            "powered_by": "Catalyst v1 - Jonathan Edwards",
                            "analysis_type": "comprehensive",
                            # Override model settings with user selections
                            "user_provider": user_provider,
                            "user_model": user_model
                        }
                    )
                    
                    return result
                
                # Run the real pipeline
                with st.spinner("leave me alone for a minute, I'm fucking busy..."):
                    step_placeholder.write("wait for it... wait for it...")
                    
                    # Execute async pipeline in Streamlit
                    try:
                        pipeline_result = run_async_safely(run_real_pipeline())
                    except Exception as async_error:
                        st.error(f"Pipeline execution error: {async_error}")
                        raise
                
                # Show completion based on real results
                if pipeline_result.status.value == "completed":
                    status_placeholder.success("WE KNOW EVERYTHING NOW! (maybe)")
                    progress_placeholder.progress(1.0)
                    
                    st.success(f"Analysis completed for {client_name}")
                    st.write(f"**Pipeline Status:** {pipeline_result.status.value}")
                    st.write(f"**Total Execution Time:** {pipeline_result.total_execution_time:.1f} seconds")
                    st.write(f"**Steps Completed:** {len(pipeline_result.get_successful_steps())}/{len(pipeline_result.step_results)}")
                    
                    # Show step results summary
                    if pipeline_result.step_results:
                        st.write("**Step Results:**")
                        for step_id, step_result in pipeline_result.step_results.items():
                            if step_result.status == "success":
                                content_size = len(str(step_result.content)) if step_result.content else 0
                                st.write(f"• {step_id.replace('_', ' ').title()}: Completed ({content_size:,} chars)")
                            else:
                                st.write(f"• {step_id.replace('_', ' ').title()}: Failed - {step_result.error}")
                    
                    # Show next steps
                    st.write("**Next Steps:**")
                    st.write("• Review detailed analysis in the Intelligence Database Explorer below")
                    st.write("• Search across findings using the search functionality") 
                    st.write("• Compare with other companies in the database")
                    
                else:
                    status_placeholder.error(f"Analysis failed: {pipeline_result.error}")
                    st.error(f"Pipeline failed with status: {pipeline_result.status.value}")
                    if pipeline_result.error:
                        st.write(f"**Error:** {pipeline_result.error}")
                
            except Exception as e:
                status_placeholder.error(f"Analysis failed: {e}")
                st.error(f"Execution error: {e}")