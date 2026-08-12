import streamlit as st
from utils.auth import check_password

st.set_page_config(page_title="CPF Housing Navigator", page_icon="🏠", layout="wide")

if not check_password():
    st.stop()

st.title("CPF housing navigator")

with st.expander("⚠️ Important Notice", expanded=True):
    st.markdown(
        """
IMPORTANT NOTICE: This web application is a prototype developed for educational
purposes only. The information provided here is NOT intended for real-world usage
and should not be relied upon for making any decisions, especially those related
to financial, legal, or healthcare matters.

Furthermore, please be aware that the LLM may generate inaccurate or incorrect
information. You assume full responsibility for how you use any generated output.
Always consult with qualified professionals for accurate and personalised advice.
"""
    )

st.markdown(
    """
Welcome. This app helps you understand and explore how CPF savings can be used
for a home purchase in Singapore, without needing to log in or share any
personally identifying information.

Use the sidebar to navigate between:

- **Housing Health Check** — tell us whether you're planning a housing purchase or
  managing an existing housing loan, add your co-buyer or co-owner details, and see
  whether your numbers fit CPF Board's prudent budgeting guidelines, with tailored
  suggestions if they don't.
- **Housing Q&A Bot** — ask questions about CPF housing rules (VL/WL, MSR/TDSR,
  the lease-to-95 rule, and more) and get answers grounded in cited official sources.

This app is for general education only. For your exact, personalised figures,
always refer to the official CPF Board, HDB, and MAS tools and resources.
"""
)
