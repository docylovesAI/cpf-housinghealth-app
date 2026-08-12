"""
Shared OpenAI client setup, used by both retrieval.py (embeddings) and
llm.py (answer generation), so the API key handling lives in one place.
"""

import os
import streamlit as st
from openai import OpenAI


def get_client() -> OpenAI:
    api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
    if not api_key:
        raise RuntimeError(
            "No OpenAI API key found. Add OPENAI_API_KEY to .streamlit/secrets.toml."
        )
    return OpenAI(api_key=api_key)
