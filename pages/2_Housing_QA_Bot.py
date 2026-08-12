import streamlit as st
from utils.auth import check_password
from utils.llm import ask_grounded_question

st.set_page_config(page_title="CPF Housing Q&A Bot", page_icon="💬")

if not check_password():
    st.stop()

st.title("CPF Housing Q&A Bot")
st.caption(
    "Pick a common scenario to start, or type your own question. "
    "Answers are grounded in a curated set of CPF Board, HDB, and MAS sources -- "
    "see the citation shown under each answer."
)

SCENARIOS = {
    "Why is there a limit on how much CPF I can use for my flat?": None,
    "What happens if my flat's remaining lease doesn't cover me to age 95?": None,
    "What's the difference between MSR and TDSR?": None,
    "If I use an HDB loan instead of a bank loan, does that change my CPF limit?": None,
    "What do I need to refund to CPF when I sell my flat?": None,
    "How much is Buyer's Stamp Duty for a $750,000 flat?": None,
}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.subheader("Common scenarios")
cols = st.columns(2)
for i, scenario in enumerate(SCENARIOS):
    if cols[i % 2].button(scenario, use_container_width=True):
        st.session_state.pending_question = scenario

st.divider()

for turn in st.session_state.chat_history:
    with st.chat_message(turn["role"]):
        if turn["role"] == "assistant" and turn.get("injection_flagged"):
            st.caption(
                "⚠️ This message contained wording commonly used to try to change "
                "an AI assistant's behaviour. It was still answered using only the "
                "app's fixed rules and cited sources."
            )
        if turn["role"] == "assistant" and turn.get("tool_used"):
            st.caption(f"🛠️ Used the {turn['tool_used']} calculator for an exact figure.")
        if turn["role"] == "assistant" and turn.get("was_revised"):
            st.caption("✏️ This answer was automatically corrected after a source-accuracy check.")
        st.markdown(turn["content"])
        if turn["role"] == "assistant" and turn.get("sources"):
            with st.expander("Sources used for this answer"):
                for src in turn["sources"]:
                    st.markdown(
                        f"**{src['topic']}** — {src['source_name']} "
                        f"(as of {src['last_verified']})\n\n"
                        f"[{src['source_url']}]({src['source_url']})"
                    )

typed_question = st.chat_input("Ask a follow-up question about CPF housing rules")
question_to_ask = st.session_state.pop("pending_question", None) or typed_question
if question_to_ask:
    # Same fix as the assistant's answers: Streamlit's markdown renderer can
    # misinterpret "$" (as LaTeX math delimiters, or otherwise), so any
    # dollar amount the user types is sanitized before it's ever displayed
    # or stored, keeping both the live view and future history replays clean.
    question_to_ask = question_to_ask.replace("$", "SGD ").replace("SGD  ", "SGD ")

if question_to_ask:
    prior_history = list(st.session_state.chat_history)  # snapshot before this turn
    st.session_state.chat_history.append({"role": "user", "content": question_to_ask})
    with st.chat_message("user"):
        st.markdown(question_to_ask)

    with st.chat_message("assistant"):
        with st.spinner("Checking the sources..."):
            result = ask_grounded_question(question_to_ask, chat_history=prior_history)
        if result.get("injection_flagged"):
            st.caption(
                "⚠️ This message contained wording commonly used to try to change "
                "an AI assistant's behaviour. It was still answered using only the "
                "app's fixed rules and cited sources."
            )
        if result.get("tool_used"):
            st.caption(f"🛠️ Used the {result['tool_used']} calculator for an exact figure.")
        if result.get("was_revised"):
            st.caption("✏️ This answer was automatically corrected after a source-accuracy check.")
        st.markdown(result["answer"])
        if result["sources"]:
            with st.expander("Sources used for this answer"):
                for src in result["sources"]:
                    st.markdown(
                        f"**{src['topic']}** — {src['source_name']} "
                        f"(as of {src['last_verified']})\n\n"
                        f"[{src['source_url']}]({src['source_url']})"
                    )

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "injection_flagged": result.get("injection_flagged", False),
            "tool_used": result.get("tool_used"),
            "was_revised": result.get("was_revised", False),
        }
    )

st.divider()
st.info(
    "This tool is for general education only and isn't personalised "
    "financial advice. For guidance on your situation, contact CPF Board, "
    "HDB, or your bank.",
    icon="ℹ️",
)
