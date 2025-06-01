"""Sidebar module for the autonomous pipeline system."""
import streamlit as st


def render_sidebar():
    """Render the sidebar with intelligence database, system status, and AI model settings."""
    with st.sidebar:
        st.header("Intelligence Database")
        
        clients = st.session_state.storage.get_all_clients()
        st.metric("Companies Analyzed", len(clients))
        
        if clients:
            st.write("**Recent Analyses:**")
            for client in clients[-5:]:  # Show last 5
                st.write(f"• {client}")
        
        # Show pipeline engine status only when actively running
        engine_available = st.session_state.get('engine_available', False)
        if engine_available and st.session_state.engine:
            current_execution = st.session_state.engine.get_current_execution()
            if current_execution:
                st.warning(f"Running: {current_execution.client_name}")
        elif not st.session_state.get('embeddings_available', False):
            st.warning("Pipeline engine disabled (embeddings unavailable)")
        
        # Model Provider Selection
        st.header("AI Model Settings")
        
        # Provider selection
        available_providers = st.session_state.get('available_providers', ['gemini'])
        # Ensure a default provider is set
        if 'selected_provider' not in st.session_state or st.session_state.selected_provider not in available_providers:
            st.session_state.selected_provider = available_providers[0]
        selected_provider = st.selectbox(
            "AI Provider",
            available_providers,
            index=available_providers.index(st.session_state.selected_provider),
            format_func=lambda x: {
                'openai': 'OpenAI (GPT-4)',
                'gemini': 'Google (Gemini)'
            }.get(x, x)
        )
        st.session_state.selected_provider = selected_provider

        # Model selection based on provider
        models = {}
        if selected_provider and st.session_state.multi_llm:
            models = st.session_state.multi_llm.get_provider_models(selected_provider) or {}
        model_options = list(models.keys())
        if model_options:
            # Ensure a default model is set
            if 'selected_model' not in st.session_state or st.session_state.selected_model not in model_options:
                st.session_state.selected_model = model_options[0]
            selected_model = st.selectbox(
                "Model",
                model_options,
                index=model_options.index(st.session_state.selected_model),
                format_func=lambda x: f"{x} → {models[x]}",
                help="Model from models.yaml configuration"
            )
            st.session_state.selected_model = selected_model
            
            # Show current selection summary
            st.caption(f"**Active:** {selected_provider} {selected_model}")
        else:
            st.warning("No models available for selected provider")
        
