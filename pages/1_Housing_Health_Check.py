import streamlit as st
from utils.auth import check_password
from utils.cpf_rules import (
    Person, monthly_instalment, evaluate_rules, net_remaining_oa_after_upfront,
    calculate_bsd, topup_oa_credited,
)

st.set_page_config(page_title="CPF Housing Health Check", page_icon="🏠", layout="wide")

if not check_password():
    st.stop()

st.title("CPF Housing Health Check")
st.caption(
    "Check whether a housing purchase or an existing mortgage fits CPF Board's "
    "prudent budgeting guidelines, personalised to your co-buyer or co-owner profile."
)

MAX_PEOPLE = 4

if "scenario" not in st.session_state:
    st.session_state.scenario = "purchase"
if "num_people" not in st.session_state:
    st.session_state.num_people = 2

# ---------------------------------------------------------------------------
# Scenario toggle
# ---------------------------------------------------------------------------

st.subheader("I am enquiring on:")
col_a, col_b = st.columns(2)
if col_a.button("🏠 Housing purchase", use_container_width=True,
                 type="primary" if st.session_state.scenario == "purchase" else "secondary"):
    st.session_state.scenario = "purchase"
    st.rerun()
if col_b.button("🏦 Housing loan", use_container_width=True,
                type="primary" if st.session_state.scenario == "loan" else "secondary"):
    st.session_state.scenario = "loan"
    st.rerun()

scenario = st.session_state.scenario
is_purchase = scenario == "purchase"
person_noun = "buyer" if is_purchase else "owner"
person_noun_cap = "Buyer" if is_purchase else "Owner"
co_noun = "Co-buyer" if is_purchase else "Co-owner"

# ---------------------------------------------------------------------------
# Co-buyer / co-owner profiles (up to 4)
# ---------------------------------------------------------------------------

st.subheader(f"{person_noun_cap} profile")
c1, c2 = st.columns([4, 1])
c1.caption(f"Add up to {MAX_PEOPLE} {person_noun}s. Figures are not personally identifying.")
if c2.button(f"+ Add {co_noun.lower()}", disabled=st.session_state.num_people >= MAX_PEOPLE):
    st.session_state.num_people = min(MAX_PEOPLE, st.session_state.num_people + 1)
    st.rerun()

default_profiles = [
    {"age": 32, "income": 5500, "bonus": 8000},
    {"age": 31, "income": 4200, "bonus": 6000},
    {"age": 35, "income": 6000, "bonus": 10000},
    {"age": 29, "income": 3800, "bonus": 4000},
]

people = []
person_cols = st.columns(st.session_state.num_people)
for i in range(st.session_state.num_people):
    with person_cols[i]:
        st.markdown(f"**{person_noun_cap} {i+1}**")
        if i > 0 and st.button("Remove", key=f"remove_{i}"):
            st.session_state.num_people -= 1
            st.rerun()
        age = st.number_input("Age", 21, 70, default_profiles[i]["age"], key=f"age_{i}")
        income = st.number_input("Gross monthly income ($)", 0, 30000, default_profiles[i]["income"], step=100, key=f"income_{i}")
        oa_balance = st.number_input("Current CPF OA balance ($)", 0, 500000, 60000 - i * 20000, step=1000, key=f"oa_{i}")
        bonus = 0
        if is_purchase:
            bonus = st.number_input("Annual bonus / variable income ($)", 0, 200000, default_profiles[i]["bonus"], step=500, key=f"bonus_{i}")
        people.append(Person(
            age=age, gross_monthly_income=income, annual_bonus=bonus,
            current_oa_balance=oa_balance,
        ))

# ---------------------------------------------------------------------------
# Property / loan or mortgage parameters
# ---------------------------------------------------------------------------

st.subheader("Property and loan" if is_purchase else "Mortgage details")
c1, c2 = st.columns(2)

purchase_price = None
loan_amount = None
current_instalment_input = None

with c1:
    if is_purchase:
        purchase_price = st.number_input("Purchase price ($)", 100_000, 3_000_000, 600_000, step=10_000)
        default_loan_amount = int(round(0.75 * purchase_price))
        loan_amount = st.number_input(
            "Loan amount ($)", 50_000, 2_500_000, default_loan_amount, step=10_000,
            help="Defaults to 75% of purchase price (the current LTV cap) — edit directly if you have a different figure."
        )
    else:
        current_instalment_input = st.number_input("Current monthly instalment ($)", 100, 20_000, 2_278, step=10)

    loan_type = st.selectbox("Loan type", options=["hdb", "bank"], format_func=lambda x: "HDB loan (2.6% p.a.)" if x == "hdb" else "Bank loan")
    if is_purchase:
        if loan_type == "hdb":
            c1.caption(
                "Not sure how much to borrow? Check the CPF Home Purchase "
                "Planner for a budget estimate, or refer to your HDB Flat "
                "Eligibility (HFE) letter for your actual loan eligibility."
            )
        else:
            c1.caption(
                "Not sure how much to borrow? Check the CPF Home Purchase "
                "Planner for a budget estimate, or refer to the In-Principle "
                "Approval (IPA) letter from financial institutions for your "
                "actual loan eligibility."
            )

with c2:
    tenure_label = "Loan tenure (years)" if is_purchase else "Remaining loan tenure (years)"
    tenure = st.number_input(tenure_label, 1, 35, 25)
    if loan_type == "bank":
        rate = st.slider("Interest rate (% p.a.)", 1.0, 6.0, 3.5, step=0.1)
    else:
        rate = 2.6
        st.metric("Interest rate", "2.6% (fixed)")

if is_purchase:
    calculated_inst = monthly_instalment(loan_amount, rate, tenure)
    monthly_inst = st.number_input(
        "Monthly instalment ($)", 0, 20_000, int(round(calculated_inst)), step=10,
        help="Auto-calculated from loan amount, rate, and tenure — edit directly if you have a different figure."
    )
else:
    monthly_inst = current_instalment_input

# ---------------------------------------------------------------------------
# Upfront costs (purchase scenario only)
# ---------------------------------------------------------------------------

downpayment = stamp_duty = legal_fees = usable_cpf_refund = cash_proceeds = 0

if is_purchase:
    st.subheader("Upfront costs")
    c1, c2, c3 = st.columns(3)

    default_downpayment = purchase_price - loan_amount if purchase_price and loan_amount else 0
    downpayment = c1.number_input("Downpayment ($)", 0, 3_000_000, default_downpayment, step=1_000)
    if loan_type == "bank":
        mandatory_cash = 0.05 * purchase_price
        c1.caption(f"This assumes exactly \\${mandatory_cash:,.0f} (5% of purchase price) is paid in cash for a bank loan, with the rest of the downpayment assumed to come fully from CPF.")
    else:
        c1.caption("For an HDB loan, the full downpayment can come from CPF (subject to your OA balance).")

    calculated_bsd = calculate_bsd(purchase_price)
    bsd_used = c2.number_input(
        "Buyer's Stamp Duty ($)", 0, 500_000, int(round(calculated_bsd)), step=500,
        help="Auto-calculated using IRAS's tiered Buyer's Stamp Duty schedule — edit directly if you have a different figure."
    )
    absd = c2.number_input(
        "Additional Buyer's Stamp Duty, if applicable ($)", 0, 1_000_000, 0, step=1_000,
        help="Additional Buyer's Stamp Duty applies for second/subsequent properties, Permanent Residents, or foreign buyers. Not auto-calculated — enter your own figure if it applies to you."
    )
    stamp_duty = bsd_used + absd
    if absd > 0:
        c2.caption(f"Buyer's Stamp Duty: \\${bsd_used:,.0f} + Additional Buyer's Stamp Duty: \\${absd:,.0f} = \\${stamp_duty:,.0f} total")

    legal_fees = c3.number_input("Legal fees ($)", 0, 20_000, 3_000, step=100)
    c3.caption("Typical conveyancing fees range from \\$1,300 to \\$3,000.")

    st.subheader("Are you selling an existing property?")
    selling_choice = st.radio("Choose one", options=["No", "Yes"], horizontal=True, key="selling_existing_choice")
    if selling_choice == "Yes":
        c4, c5 = st.columns(2)
        usable_cpf_refund = c4.number_input("Usable CPF refunds ($)", 0, 2_000_000, 0, step=1_000)
        c4.caption(
            "Check your balance housing refunds amount on the CPF Home "
            "Ownership Dashboard (cpf.gov.sg) — this is the CPF you can "
            "reuse for your next purchase."
        )
        cash_proceeds = c5.number_input("Cash proceeds ($)", 0, 5_000_000, 0, step=1_000)
        c5.caption(
            "Cash left over from the sale after paying off your loan and CPF refund. "
            "This offsets your downpayment, stamp duty, and legal fees proportionally, "
            "reducing your total CPF draw before it's calculated."
        )

# ---------------------------------------------------------------------------
# Monthly instalment funding
# ---------------------------------------------------------------------------

st.subheader("Monthly instalment funding")
st.caption(
    "Upfront costs (downpayment, stamp duty, legal fees) are assumed "
    "CPF-funded, subject to cash-minimum rules — set your instalment "
    "split below."
)
split_label = st.select_slider(
    "Instalment payment split",
    options=["Fully cash", "Mostly cash", "Half CPF", "Mostly CPF", "Fully CPF"],
    value="Mostly CPF",
)
cpf_pct_instalment = {
    "Fully cash": 0.0,
    "Mostly cash": 0.25,
    "Half CPF": 0.5,
    "Mostly CPF": 0.75,
    "Fully CPF": 1.0,
}[split_label]

st.subheader("Projected Voluntary CPF Contribution")
topup_choice = st.radio("Choose one", options=["None", "Make a cash top-up"], horizontal=True)
oa_credited_topup = 0.0
if topup_choice == "Make a cash top-up":
    st.caption("Each buyer's own top-up is split into OA, SA/RA, and MA using their own age — no shared-pool assumption needed.")
    topup_cols = st.columns(len(people))
    topups = []
    for i, p in enumerate(people):
        amount = topup_cols[i].number_input(
            f"{person_noun_cap} {i+1} top-up amount ($)", 0, 200_000, 0, step=500, key=f"topup_{i}"
        )
        topups.append((amount, p.age))
    total_topup = sum(a for a, _ in topups)
    if total_topup > 0:
        oa_credited_topup = topup_oa_credited(topups)
        oa_pct_effective = oa_credited_topup / total_topup * 100
        st.caption(
            f"Combined top-up: \\${total_topup:,.0f}. Based on each buyer's own age, "
            f"about {oa_pct_effective:.0f}% (\\${oa_credited_topup:,.0f}) would land in "
            f"OA in total; the rest goes to SA/RA and MA."
        )

# ---------------------------------------------------------------------------
# Evaluate rules
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Results")

net_remaining_oa = None
if is_purchase:
    initial_total_oa = sum(p.current_oa_balance for p in people)
    net_remaining_oa = net_remaining_oa_after_upfront(
        initial_total_oa, oa_credited_topup, downpayment, stamp_duty, legal_fees,
        loan_type=loan_type, purchase_price=purchase_price,
        usable_cpf_refund=usable_cpf_refund, cash_proceeds=cash_proceeds,
    )
else:
    net_remaining_oa = sum(p.current_oa_balance for p in people) + oa_credited_topup

results = evaluate_rules(
    scenario=scenario,
    people=people,
    monthly_instalment_amount=monthly_inst,
    cpf_pct_instalment=cpf_pct_instalment,
    purchase_price=purchase_price,
    net_remaining_oa=net_remaining_oa,
)

for r in results:
    badge = "✅ Pass" if r.passed else "⚠️ Needs attention"
    with st.container(border=True):
        cols = st.columns([3, 1])
        cols[0].markdown(f"**{r.name}**")
        cols[0].caption(r.detail)
        cols[1].markdown(f"**{badge}**")
        if not r.passed:
            st.warning(r.advisory)

st.caption(
    "These checks use CPF Board's own prudent budgeting tips (25% MSR, 6-month OA "
    "buffer, price within 5x annual income) — stricter than the statutory 30% MSR "
    "and 55% TDSR ceilings set by HDB and MAS. Source: CPF Board, \"Quick tips to "
    "effectively manage your home budget\" (21 May 2025)."
)
