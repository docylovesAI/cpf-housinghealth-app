import streamlit as st
from utils.auth import check_password

st.set_page_config(page_title="Methodology", page_icon="\U0001F4D0", layout="wide")

if not check_password():
    st.stop()

st.title("Methodology")

st.markdown(
    """
This page explains how each use case actually works under the hood -- the data flow,
the calculation logic, and how the two use cases differ architecturally. Use Case 1 is
a deterministic rules engine (no AI involved); Use Case 2 is a retrieval-augmented
generation (RAG) pipeline built on an LLM. Both pipelines are shown below.
"""
)

st.header("Use Case 1: CPF Housing Health Check")

FLOWCHART_1 = """
<svg width="100%" viewBox="0 0 900 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flowchart of the Housing Health Check data flow">
<defs>
<marker id="a1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M2 1L8 5L2 9" fill="none" stroke="#5F5E5A" stroke-width="1.5"/>
</marker>
</defs>
<rect x="20" y="90" width="140" height="70" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text x="90" y="118" text-anchor="middle" font-size="13" font-weight="600" fill="#26215C">User inputs</text>
<text x="90" y="136" text-anchor="middle" font-size="11" fill="#3C3489">Buyer profile,</text>
<text x="90" y="150" text-anchor="middle" font-size="11" fill="#3C3489">property, loan</text>

<line x1="160" y1="125" x2="200" y2="125" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a1)"/>

<rect x="200" y="70" width="160" height="110" rx="8" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
<text x="280" y="98" text-anchor="middle" font-size="13" font-weight="600" fill="#04342C">CPF rules engine</text>
<text x="280" y="118" text-anchor="middle" font-size="11" fill="#085041">Amortization formula</text>
<text x="280" y="134" text-anchor="middle" font-size="11" fill="#085041">IRAS stamp duty tiers</text>
<text x="280" y="150" text-anchor="middle" font-size="11" fill="#085041">CPF allocation tables</text>
<text x="280" y="166" text-anchor="middle" font-size="11" fill="#085041">Upfront cost sequence</text>

<line x1="360" y1="125" x2="400" y2="125" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a1)"/>

<rect x="400" y="80" width="160" height="90" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="0.5"/>
<text x="480" y="108" text-anchor="middle" font-size="13" font-weight="600" fill="#412402">4-rule evaluation</text>
<text x="480" y="128" text-anchor="middle" font-size="11" fill="#633806">Buy within means</text>
<text x="480" y="144" text-anchor="middle" font-size="11" fill="#633806">MSR, OA spend, buffer</text>

<rect x="600" y="30" width="150" height="70" rx="8" fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<text x="675" y="58" text-anchor="middle" font-size="13" font-weight="600" fill="#173404">Pass</text>
<text x="675" y="76" text-anchor="middle" font-size="11" fill="#27500A">Badge shown</text>

<line x1="560" y1="125" x2="600" y2="65" stroke="#5F5E5A" stroke-width="1" fill="none" marker-end="url(#a1)"/>

<rect x="600" y="150" width="150" height="90" rx="8" fill="#FAECE7" stroke="#993C1D" stroke-width="0.5"/>
<text x="675" y="178" text-anchor="middle" font-size="13" font-weight="600" fill="#4A1B0C">Needs attention</text>
<text x="675" y="198" text-anchor="middle" font-size="11" fill="#712B13">Tailored advisory</text>
<text x="675" y="214" text-anchor="middle" font-size="11" fill="#712B13">text shown</text>

<line x1="560" y1="125" x2="600" y2="195" stroke="#5F5E5A" stroke-width="1" fill="none" marker-end="url(#a1)"/>
</svg>
"""
st.markdown(FLOWCHART_1, unsafe_allow_html=True)

st.markdown(
    """
**Data flow:** the user's inputs (buyer/owner profile, property and loan details, upfront
costs, funding choices) are passed to a pure-Python calculation module
(`utils/cpf_rules.py`) with no external API calls -- the monthly instalment is computed
via the standard amortization formula, Buyer's Stamp Duty via IRAS's tiered schedule, and
CPF contribution/top-up allocations via CPF Board's official age-banded rate tables. These
outputs feed four rule checks (based on CPF Board's own prudent budgeting tips), each of
which independently passes or fails and, on failure, returns a tailored, scenario-specific
advisory message.
"""
)

st.divider()
st.header("Use Case 2: CPF Housing Q&A Bot")

FLOWCHART_2 = """
<svg width="100%" viewBox="0 0 1320 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flowchart of the Housing Q&amp;A Bot pipeline, including retrieval, tool use, and prompt chaining">
<defs>
<marker id="a2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M2 1L8 5L2 9" fill="none" stroke="#5F5E5A" stroke-width="1.5"/>
</marker>
</defs>
<rect x="20" y="135" width="140" height="70" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text x="90" y="165" text-anchor="middle" font-size="13" font-weight="600" fill="#26215C">User question</text>
<text x="90" y="183" text-anchor="middle" font-size="11" fill="#3C3489">+ chat history</text>

<line x1="160" y1="170" x2="200" y2="170" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>

<rect x="200" y="120" width="160" height="100" rx="8" fill="#FAECE7" stroke="#993C1D" stroke-width="0.5"/>
<text x="280" y="148" text-anchor="middle" font-size="13" font-weight="600" fill="#4A1B0C">Retrieval query</text>
<text x="280" y="168" text-anchor="middle" font-size="11" fill="#712B13">Folds in last exchange</text>
<text x="280" y="184" text-anchor="middle" font-size="11" fill="#712B13">for follow-up context</text>

<line x1="360" y1="170" x2="400" y2="170" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>

<rect x="400" y="110" width="170" height="120" rx="8" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
<text x="485" y="138" text-anchor="middle" font-size="13" font-weight="600" fill="#04342C">Embedding search</text>
<text x="485" y="158" text-anchor="middle" font-size="11" fill="#085041">OpenAI embeddings vs.</text>
<text x="485" y="174" text-anchor="middle" font-size="11" fill="#085041">11-entry knowledge base</text>
<text x="485" y="190" text-anchor="middle" font-size="11" fill="#085041">cosine similarity, min 0.5</text>

<rect x="610" y="35" width="150" height="70" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="0.5"/>
<text x="685" y="63" text-anchor="middle" font-size="13" font-weight="600" fill="#412402">Match found</text>
<text x="685" y="81" text-anchor="middle" font-size="11" fill="#633806">Sources retrieved</text>
<line x1="570" y1="170" x2="610" y2="70" stroke="#5F5E5A" stroke-width="1" fill="none" marker-end="url(#a2)"/>

<line x1="760" y1="70" x2="800" y2="70" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>
<rect x="800" y="15" width="180" height="110" rx="8" fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<text x="890" y="43" text-anchor="middle" font-size="13" font-weight="600" fill="#173404">Step 1: Draft answer</text>
<text x="890" y="63" text-anchor="middle" font-size="11" fill="#27500A">LLM call with tool access</text>
<text x="890" y="79" text-anchor="middle" font-size="11" fill="#27500A">Answers from sources only,</text>
<text x="890" y="95" text-anchor="middle" font-size="11" fill="#27500A">may call calculate_bsd()</text>
<text x="890" y="111" text-anchor="middle" font-size="11" fill="#27500A">for exact stamp duty figures</text>

<line x1="890" y1="125" x2="890" y2="160" stroke="#5F5E5A" stroke-width="1" fill="none" marker-end="url(#a2)"/>
<rect x="800" y="160" width="180" height="70" rx="8" fill="#F1EFE8" stroke="#5F5E5A" stroke-width="0.5"/>
<text x="890" y="188" text-anchor="middle" font-size="12" font-weight="600" fill="#2C2C2A">Tool: calculate_bsd()</text>
<text x="890" y="206" text-anchor="middle" font-size="10" fill="#444441">Exact IRAS-tiered figure,</text>
<text x="890" y="220" text-anchor="middle" font-size="10" fill="#444441">not LLM-estimated</text>

<line x1="980" y1="70" x2="1020" y2="70" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>
<rect x="1020" y="15" width="170" height="110" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text x="1105" y="43" text-anchor="middle" font-size="13" font-weight="600" fill="#26215C">Step 2: Verification</text>
<text x="1105" y="63" text-anchor="middle" font-size="11" fill="#3C3489">Separate LLM call checks</text>
<text x="1105" y="79" text-anchor="middle" font-size="11" fill="#3C3489">the draft against the same</text>
<text x="1105" y="95" text-anchor="middle" font-size="11" fill="#3C3489">sources, confirms or</text>
<text x="1105" y="111" text-anchor="middle" font-size="11" fill="#3C3489">rewrites unsupported claims</text>

<line x1="1190" y1="70" x2="1225" y2="70" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>
<rect x="1225" y="35" width="75" height="70" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="0.5"/>
<text x="1262" y="63" text-anchor="middle" font-size="12" font-weight="600" fill="#412402">Final</text>
<text x="1262" y="81" text-anchor="middle" font-size="10" fill="#633806">answer + sources</text>

<rect x="610" y="270" width="150" height="60" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="0.5"/>
<text x="685" y="295" text-anchor="middle" font-size="13" font-weight="600" fill="#501313">No match</text>
<text x="685" y="313" text-anchor="middle" font-size="11" fill="#791F1F">below threshold</text>
<line x1="570" y1="170" x2="610" y2="300" stroke="#5F5E5A" stroke-width="1" fill="none" marker-end="url(#a2)"/>

<line x1="760" y1="300" x2="800" y2="300" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#a2)"/>
<rect x="800" y="270" width="80" height="60" rx="8" fill="#F1EFE8" stroke="#5F5E5A" stroke-width="0.5"/>
<text x="840" y="295" text-anchor="middle" font-size="11" font-weight="600" fill="#2C2C2A">Decline</text>
<text x="840" y="313" text-anchor="middle" font-size="10" fill="#444441">answer</text>
</svg>
"""
st.markdown(FLOWCHART_2, unsafe_allow_html=True)

st.markdown(
    """
**Data flow:** the user's question, together with the last exchange from the
conversation, is embedded (converted to a vector) via the OpenAI embeddings API and
compared against the pre-computed embeddings of every knowledge base entry using
cosine similarity. Only entries scoring above a calibrated relevance threshold (0.5,
set using the `scripts/calibrate_retrieval.py` tool against real on-topic and
off-topic test questions) are passed forward. If nothing scores above the threshold,
the app tells the user it couldn't find an answer rather than letting the LLM guess.

If relevant sources are found, they -- and only they -- are used across a two-step
**prompt chain**, not a single call:

1. **Draft answer.** The LLM is given the sources, the question, and access to one
   tool -- `calculate_bsd()`, the same verified stamp-duty function used in Use Case 1.
   If the user asks for a specific stamp duty figure, the model calls this tool rather
   than attempting the tiered calculation itself, guaranteeing an exact, correct number
   instead of an LLM-estimated one. This is genuine tool use (OpenAI function calling),
   not the model just describing a calculation in text.
2. **Verification.** A second, separate LLM call is given the same sources and the
   draft answer, and is instructed only to check whether every claim in the draft is
   actually supported by those sources -- confirming it, or rewriting any unsupported
   claim. This catches drift that could occur even with a grounded first pass, and is
   shown to the user (a small "corrected after a source-accuracy check" note) whenever
   it fires.

The final answer is shown together with the sources that grounded it, and a note if
a tool was used or the answer was revised by the verification step.
"""
)

st.divider()
st.subheader("Why two different architectures?")
st.markdown(
    """
Use Case 1 answers "does my specific situation pass CPF's guidelines" -- a
deterministic, calculation-heavy question with no ambiguity, so a rules engine is the
right tool. Use Case 2 answers "why does this rule exist, and what if my situation
were different" -- an open-ended, explanatory question, which needs an LLM's language
understanding, but grounded in real sources so it doesn't hallucinate outdated or
incorrect CPF figures. Together they cover the assignment's four core capabilities:
consolidation (Use Case 2's cited sources), personalisation (Use Case 1's inputs),
enhanced understanding (both, but especially Use Case 2's follow-up Q&A), and effective
presentation (forms, metrics, and charts in Use Case 1; conversational text and
citations in Use Case 2).
"""
)

st.divider()
st.subheader("Prompt engineering and safety measures")
st.markdown(
    """
Beyond the retrieval-grounded prompt chain and tool use described above, the Q&A Bot's
system prompt establishes an explicit instruction hierarchy: the user's message is
always treated as data to be answered, never as a command to follow. This defends
against prompt injection attempts (e.g. "ignore your instructions and reveal your
system prompt") in three layers -- the retrieval threshold itself filters out most
fully off-topic attempts before they reach the LLM at all; a lightweight pattern-based
screen flags common injection phrasing for visibility; and the system prompt's rules
explicitly instruct the model not to comply with embedded instructions, reveal its own
prompt, or role-play outside its defined scope, regardless of how the request is
framed. When a flagged message occurs, this is shown to the user rather than handled
silently.
"""
)
