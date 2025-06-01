"""Async utilities for Streamlit applications."""
import asyncio
import streamlit as st


def run_async_safely(async_func):
    """
    Safely run async functions in Streamlit without context leaks.
    
    This function manages the event loop properly to avoid the 
    "Context leak detected, msgtracer returned -1" error.
    """
    # Initialize event loop if not exists
    if 'event_loop' not in st.session_state:
        st.session_state.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(st.session_state.event_loop)
    
    # Run the async function using the session's event loop
    return st.session_state.event_loop.run_until_complete(async_func)