"""PDF and briefing components module for the autonomous pipeline system."""
import streamlit as st
import asyncio
from textwrap import dedent
from src.ui.async_utils import run_async_safely


def render_briefing_section(selected_company):
    """Render the intelligence briefing generation section."""
    st.write("### Intelligence Briefing")
    col_brief1, col_brief2 = st.columns(2)
    
    with col_brief1:
        if st.button("Generate Intelligence Briefing", key=f"briefing_{selected_company}"):
            model_name = st.session_state.get('selected_model', 'configured model')
            with st.spinner(f"Generating comprehensive intelligence briefing with {model_name}..."):
                try:
                    # Get provider settings
                    provider = st.session_state.selected_provider
                    model = st.session_state.selected_model
                    
                    # Create async function to run briefing
                    async def run_briefing():
                        result = await st.session_state.briefing_generator.generate_briefing(
                            client_name=selected_company,
                            provider=provider,
                            model=model  # Changed from model_variant to model
                        )
                        return result
                    
                    # Execute briefing generation with proper async handling
                    briefing_result = run_async_safely(run_briefing())
                    
                    if briefing_result["status"] == "success":
                        briefing = briefing_result["briefing"]
                        
                        # Generate beautiful PDF
                        with st.spinner("Creating report..."):
                            pdf_path = st.session_state.briefing_pdf.generate_briefing_pdf(briefing)
                        
                        st.success("Intelligence Briefing Generated!")
                        
                        # Provide download
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="Download Beautiful Intelligence Briefing",
                                data=pdf_file.read(),
                                file_name=f"{selected_company}_intelligence_briefing.pdf",
                                mime="application/pdf",
                                help="Comprehensive AI-generated intelligence briefing with strategic insights and recommendations"
                            )
                        
                        
                    else:
                        st.error(f"Briefing generation failed: {briefing_result.get('error')}")
                
                except Exception as e:
                    st.error(f"Error generating briefing: {e}")
                    import traceback
                    st.text(traceback.format_exc())
    
    with col_brief2:
        # Space for future briefing controls or status
        pass


