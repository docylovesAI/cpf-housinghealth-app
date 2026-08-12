import streamlit as st
from utils.auth import check_password

st.set_page_config(page_title="About Us", page_icon="ℹ️")

if not check_password():
    st.stop()

st.title("About us")

st.subheader("Project scope")
st.markdown(
    """
This app helps members of the public in Singapore check whether their housing decision
-- whether an **intended purchase** or the **servicing of an existing housing loan** --
stays within CPF Board's prudent budgeting benchmarks for CPF savings.

It does not compute how much CPF a member is entitled to withdraw (e.g. Valuation Limit
or Withdrawal Limit figures) -- that remains the role of CPF Board's own official tools.
Instead, it takes a member's own figures (income, loan details, CPF balances) and checks
them against four of CPF Board's published rules of thumb for prudent budgeting, flagging
where a scenario falls short and why. It does **not** attempt to replace official CPF
Board, HDB, or MAS tools that use a member's real, logged-in account data (such as the
Home Purchase Planner, the Home Ownership Dashboard, or the Housing Usage Calculator) --
instead, it complements them as a no-login, exploratory literacy tool, and consistently
points users back to those official tools wherever a precise, personalised figure is
needed.
"""
)

st.subheader("Objectives")
st.markdown(
    """
1. **Consolidate** scattered CPF, HDB, and MAS housing rules into one place.
2. **Personalise** guidance based on a user's own (non-identifying) figures — income,
   age, property details — rather than generic advice.
3. **Enhance understanding** through interactive tools and a conversational assistant
   that explains the reasoning behind the rules, not just the numbers.
4. **Present information effectively**, combining forms, calculated results, plain-English
   explanations, and cited sources.
"""
)

st.subheader("Features")
st.markdown(
    """
### 1. CPF Housing Health Check
An interactive tool covering two scenarios — **Housing Purchase** (planning to buy) and
**Housing Loan** (already own, managing an existing mortgage). Users enter details about
themselves (up to 4 co-buyers/co-owners), their property, and their loan, and the tool:

- Auto-calculates the monthly instalment (amortization formula), Buyer's Stamp Duty
  (IRAS's official tiered schedule), and the CPF/cash split required for the downpayment,
  based on MAS's requirements
- Checks the scenario against four of CPF Board's own prudent budgeting rules of thumb —
  buying within 5x annual income, keeping the instalment within 25% of income, spending
  within monthly CPF contributions, and maintaining a 6-month CPF buffer — and flags when
  a result also breaches the actual statutory MSR ceiling (30%), not just the guideline
- Lets users model a CPF top-up, or (for buyers) selling an existing property, with a
  dedicated field to enter usable CPF refunds and cash proceeds
- Gives tailored, plain-English suggestions whenever a check needs attention

### 2. CPF Housing Q&A Bot
A conversational assistant, grounded in a curated set of CPF Board, MAS, and IRAS
sources. Rather than answering from general AI knowledge (which risks outdated or
incorrect figures), every answer is retrieved from this app's own dated, sourced
knowledge base first, and the underlying AI model is instructed to answer only using
that retrieved material — declining to answer, rather than guessing, if the knowledge
base doesn't cover a question. Every answer shows exactly which source(s) it drew from,
with a link and a "last verified" date.
"""
)

st.subheader("Data sources")
st.markdown(
    """
All factual content in this app is drawn from official government sources, each dated
and verifiable:

| Source | Used for |
|---|---|
| [CPF Board — How much CPF savings you can use for your home purchase](https://www.cpf.gov.sg/member/infohub/educational-resources/how-much-cpf-savings-you-can-use-for-your-home-purchase) | Valuation Limit / Withdrawal Limit, remaining lease and age-95 rule |
| [CPF Board — CPF refund when selling or transferring property](https://www.cpf.gov.sg/member/home-ownership/using-your-cpf-to-buy-a-home/cpf-refund-when-selling-or-transferring-property) | CPF refund and accrued interest mechanics |
| [CPF Board — Earning attractive interest](https://www.cpf.gov.sg/member/growing-your-savings/earning-higher-returns/earning-attractive-interest) | CPF Ordinary Account interest rates |
| [CPF Board — A guide to Enhanced CPF Housing and Proximity Grant](https://www.cpf.gov.sg/member/infohub/educational-resources/a-guide-to-enhanced-cpf-housing-and-proximity-grant) | CPF Housing Grants (EHG, PHG) |
| [CPF Board — What is the CPF Retirement Sum](https://www.cpf.gov.sg/member/infohub/educational-resources/what-is-the-cpf-retirement-sum) | Basic / Full / Enhanced Retirement Sums |
| [CPF Board — Quick tips to effectively manage your home budget](https://www.cpf.gov.sg/member/infohub/educational-resources/quick-tips-to-effectively-manage-your-home-budget) | The four prudent budgeting rules of thumb used in the Housing Health Check |
| [CPF Board — CPF Allocation Rates from 1 January 2026 (PDF)](https://www.cpf.gov.sg/content/dam/web/employer/employer-obligations/documents/CPFAllocationRatesfromJanuary2026.pdf) | Age-banded OA contribution and top-up allocation rates |
| [MAS — MSR and TDSR rules explainer](https://www.mas.gov.sg/regulation/explainers/new-housing-loans/msr-and-tdsr-rules) | Mortgage Servicing Ratio (30%) and Total Debt Servicing Ratio (55%) |
| [IRAS — Buyer's Stamp Duty](https://www.iras.gov.sg/taxes/stamp-duty/for-property/buying-or-acquiring-property/buyer%27s-stamp-duty-%28bsd%29) | The tiered BSD schedule used in the auto-calculation |

Every fact used from these sources has been individually fetched and paraphrased, with a
last-verified date, rather than reproduced word-for-word.
"""
)

st.subheader("Important disclaimer")
st.info(
    "This app is for general education only and is not personalised financial advice. "
    "For your exact figures, use the official CPF Board, HDB, and MAS tools, or speak "
    "with CPF Board, HDB, or your bank directly.",
    icon="ℹ️",
)
