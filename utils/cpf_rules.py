"""
Core calculation engine for the CPF Housing Health Check.

This module is intentionally framework-free (no Streamlit imports) so it
can be tested and reasoned about independently of the UI layer.
"""

from dataclasses import dataclass
from typing import Literal

OW_CEILING = 8000  # Ordinary Wage ceiling, per CPF Board, effective 2026

# CPF Board OA allocation rates by age, as a percentage of Ordinary Wage
# (subject to the OW ceiling). Source: CPF Board contribution & allocation
# rate tables, cross-checked against a third-party 2026 summary
# (cpfcalculatorsg.com/rates.html, last verified May 2026).
OA_ALLOCATION_BANDS = [
    (35, 0.23),
    (45, 0.21),
    (50, 0.19),
    (55, 0.15),
    (60, 0.12),
    (65, 0.035),
    (70, 0.01),
    (200, 0.01),  # above 70
]


def oa_allocation_pct(age: int) -> float:
    """Return the OA allocation percentage of Ordinary Wage for a given age."""
    for upper_bound, pct in OA_ALLOCATION_BANDS:
        if age <= upper_bound:
            return pct
    return OA_ALLOCATION_BANDS[-1][1]


# CPF Board OA allocation rates for a lump-sum top-up (Voluntary Contribution
# to the 3 CPF accounts), expressed as a ratio OF THE TOP-UP AMOUNT ITSELF --
# not as a percentage of wage. This is a different basis from
# OA_ALLOCATION_BANDS above and must not be confused with it: a top-up has no
# "wage" to apply a contribution rate against, so the ratio is applied
# directly to the dollar amount contributed.
#
# Source: CPF Board, "CPF Allocation Rates from 1 January 2026"
# (cpf.gov.sg/content/dam/web/employer/employer-obligations/documents/
# CPFAllocationRatesfromJanuary2026.pdf), fetched and verified directly.
# Confirmed to apply to voluntary top-ups (not just mandatory contributions)
# via CPF Board's own employer guidance page (cpf.gov.sg/employer/
# making-voluntary-contributions): "The allocation of VC to the three CPF
# accounts will follow the allocation rates for mandatory CPF contributions."
# Cross-checked against an independent worked example (a 40-year-old's
# $10,000 top-up split as $5,677/$1,891/$2,432 across OA/SA/MA), which
# matches this table exactly.
TOPUP_OA_ALLOCATION_BANDS = [
    (35, 0.6217),
    (45, 0.5677),
    (50, 0.5136),
    (55, 0.4055),
    (60, 0.353),
    (65, 0.14),
    (70, 0.0607),
    (200, 0.08),  # above 70
]


def topup_oa_allocation_pct(age: int) -> float:
    """
    Return the fraction of a lump-sum CPF top-up that actually lands in OA,
    for a given age -- the rest goes to SA/RA and MA. Use this for one-off
    top-up amounts; use oa_allocation_pct() for wage-based monthly inflow.
    """
    for upper_bound, pct in TOPUP_OA_ALLOCATION_BANDS:
        if age <= upper_bound:
            return pct
    return TOPUP_OA_ALLOCATION_BANDS[-1][1]


def monthly_oa_inflow(gross_monthly_income: float, age: int, manual_override: float | None = None) -> float:
    """
    Compute a member's monthly CPF OA inflow from salary.

    manual_override lets a user substitute their own figure (e.g. for
    variable income or non-standard employment arrangements) instead of
    the formula-derived estimate.
    """
    if manual_override is not None:
        return manual_override
    subject_ow = min(gross_monthly_income, OW_CEILING)
    return subject_ow * oa_allocation_pct(age)


def monthly_instalment(loan_amount: float, annual_rate_pct: float, tenure_years: int) -> float:
    """Standard amortization formula for a fixed monthly instalment."""
    r = annual_rate_pct / 100 / 12
    n = tenure_years * 12
    if n <= 0:
        return 0.0
    if r == 0:
        return loan_amount / n
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)


@dataclass
class Person:
    age: int
    gross_monthly_income: float
    annual_bonus: float = 0.0
    current_oa_balance: float = 0.0
    oa_inflow_override: float | None = None

    @property
    def monthly_oa_inflow(self) -> float:
        return monthly_oa_inflow(self.gross_monthly_income, self.age, self.oa_inflow_override)

    @property
    def combined_annual_income(self) -> float:
        return self.gross_monthly_income * 12 + self.annual_bonus


@dataclass
class RuleResult:
    key: str
    name: str
    detail: str
    passed: bool
    advisory: str = ""


ADVISORIES = {
    ("buy_within_means", "purchase"): (
        "This property's price is more than 5 times your combined annual income. "
        "You may want to look for a flat that better fits your budget — try the "
        "Home Purchase Planner, compare resale flat prices across locations, or "
        "refer to HDB InfoWEB."
    ),
    ("msr", "purchase"): (
        "Your instalment takes up a large share of your income. You may want to "
        "look for a flat that better fits your budget — try the Home Purchase "
        "Planner, compare resale flat prices across locations, or refer to HDB InfoWEB."
    ),
    ("msr", "loan"): (
        "Your instalment takes up a large share of your income. Consider adjusting "
        "your monthly instalment amount, or right-sizing to a more affordable property."
    ),
    ("oa_inflow", "purchase"): (
        "Your CPF-funded instalment is higher than what your monthly CPF "
        "contributions can cover. You could look for a flat that better fits your "
        "budget, use more cash instead of CPF savings by lowering your funding "
        "split, make an early cash top-up to your CPF account, or set up a "
        "recurring monthly cash top-up."
    ),
    ("oa_inflow", "loan"): (
        "Your CPF-funded instalment is higher than what your monthly CPF "
        "contributions can cover. Consider adjusting your monthly instalment, "
        "right-sizing your property, using more cash instead of CPF savings by "
        "lowering your funding split, or setting up a recurring monthly cash top-up."
    ),
    ("buffer", "purchase"): (
        "Your remaining CPF savings after this purchase would fall short of the "
        "recommended 6-month buffer. You could look for a flat that better fits "
        "your budget, use more cash instead of CPF savings by lowering your "
        "funding split, or make a one-off cash top-up to rebuild your buffer."
    ),
    ("buffer", "loan"): (
        "Your remaining CPF savings would fall short of the recommended 6-month "
        "buffer. Consider adjusting your monthly instalment, right-sizing your "
        "property, using more cash instead of CPF savings by lowering your "
        "funding split, or making a one-off cash top-up to rebuild your buffer."
    ),
}


def evaluate_rules(
    scenario: Literal["purchase", "loan"],
    people: list[Person],
    monthly_instalment_amount: float,
    cpf_pct_instalment: float,  # 0.0, 0.25, 0.5, 0.75, or 1.0
    purchase_price: float | None,
    net_remaining_oa: float | None,
) -> list[RuleResult]:
    """
    Run the four-rule evaluation matrix and return results with tailored,
    scenario-specific advisory text for any failed rule.

    All thresholds here (5x annual income, 25% MSR, 6-month buffer) are CPF
    Board's own prudent budgeting tips (see "Quick tips to effectively
    manage your home budget", CPF Board, 21 May 2025) -- not the statutory
    MSR (30%) / TDSR (55%) ceilings set by HDB/MAS.

    cpf_pct_instalment applies ONLY to the ongoing monthly instalment split
    (see "Monthly instalment funding" in the UI) -- upfront costs are
    handled separately in net_remaining_oa_after_upfront and are assumed
    CPF-funded by default.
    """
    combined_monthly_income = sum(p.gross_monthly_income for p in people)
    combined_annual_income = sum(p.combined_annual_income for p in people)
    combined_oa_inflow = sum(p.monthly_oa_inflow for p in people)
    cpf_portion_of_instalment = monthly_instalment_amount * cpf_pct_instalment

    results = []

    if scenario == "purchase" and purchase_price is not None:
        rule1_pass = purchase_price <= 5 * combined_annual_income
        results.append(RuleResult(
            key="buy_within_means",
            name="Buy within your means",
            detail="Purchase price within 5x combined annual income",
            passed=rule1_pass,
            advisory="" if rule1_pass else ADVISORIES[("buy_within_means", "purchase")],
        ))

    msr_ratio = (monthly_instalment_amount / combined_monthly_income * 100) if combined_monthly_income > 0 else 100
    rule2_pass = msr_ratio <= 25
    msr_advisory = ""
    if not rule2_pass:
        if msr_ratio > 30:
            msr_advisory = (
                "This exceeds not just CPF Board's prudent 25% guideline, but the "
                "statutory 30% Mortgage Servicing Ratio ceiling itself, set by MAS "
                "and HDB. " + ADVISORIES[("msr", scenario)]
            )
        else:
            msr_advisory = ADVISORIES[("msr", scenario)]
    results.append(RuleResult(
        key="msr",
        name="Keep MSR within 25%",
        detail=f"Instalment is {msr_ratio:.1f}% of combined monthly income (guideline: ≤25%)",
        passed=rule2_pass,
        advisory=msr_advisory,
    ))

    rule3_pass = cpf_portion_of_instalment <= combined_oa_inflow
    results.append(RuleResult(
        key="oa_inflow",
        name="Spend within OA contributions",
        detail=(
            f"CPF portion of instalment (\\${cpf_portion_of_instalment:,.0f}) vs. "
            f"monthly OA contribution (\\${combined_oa_inflow:,.0f})"
        ),
        passed=rule3_pass,
        advisory="" if rule3_pass else ADVISORIES[("oa_inflow", scenario)],
    ))

    if net_remaining_oa is not None:
        required_buffer = 6 * cpf_portion_of_instalment
        rule4_pass = net_remaining_oa >= required_buffer
        results.append(RuleResult(
            key="buffer",
            name="Maintain 6-month OA buffer",
            detail=f"Remaining OA (\\${net_remaining_oa:,.0f}) vs. 6-month buffer (\\${required_buffer:,.0f})",
            passed=rule4_pass,
            advisory="" if rule4_pass else ADVISORIES[("buffer", scenario)],
        ))

    return results


def topup_oa_credited(topups: list[tuple[float, int]]) -> float:
    """
    Compute the total OA-credited amount across multiple buyers, each
    making their own top-up.

    topups is a list of (amount, age) pairs -- one per buyer who is
    contributing. Since each buyer's own amount and age are known
    directly (rather than assumed to be an even split of one shared
    figure), this sums each person's own age-based allocation exactly,
    with no assumption about how a shared pool was divided.
    """
    return sum(amount * topup_oa_allocation_pct(age) for amount, age in topups)


def net_remaining_oa_after_upfront(
    initial_total_oa: float,
    oa_credited_topup: float,
    downpayment: float,
    stamp_duty: float,
    legal_fees: float,
    loan_type: str = "hdb",
    purchase_price: float = 0,
    usable_cpf_refund: float = 0.0,
    cash_proceeds: float = 0.0,
) -> float:
    """
    Apply the exact deduction sequence specified: initial OA, plus the
    OA-credited share of any one-off top-up and any usable CPF refund from
    selling an existing property, minus the CPF-funded share of
    downpayment, stamp duty, and legal fees (after any cash proceeds from
    a sale are applied first), in that order.

    Upfront costs (downpayment, Buyer's Stamp Duty, legal fees) are
    assumed to be paid via CPF wherever possible -- this matches how most
    buyers actually approach a purchase, maximizing CPF for the one-time
    upfront outlay to minimize cash needed on day one. The funding split
    the user chooses only applies to the ongoing monthly instalment (see
    evaluate_rules), which is a separate, recurring decision.

    For a bank loan, at least 5% of the purchase price must still be paid
    in cash regardless of this (per MAS/bank rules) -- so the CPF-funded
    portion of the downpayment is capped accordingly. For an HDB loan,
    the full downpayment is CPF-eligible with no mandatory cash component.

    oa_credited_topup is the OA-credited portion of any voluntary top-up,
    already computed by the caller (see topup_oa_credited()) -- this
    function doesn't need to know how many buyers contributed or how much
    each put in, only the resulting OA credit, keeping the "how do we
    compute this" and "how does it flow through the balance" concerns
    separate.

    usable_cpf_refund represents CPF becoming available from selling an
    existing property (e.g. via the CPF Home Ownership Dashboard) -- unlike
    a voluntary top-up, a refund credits fully to OA (for members below 55),
    so it's added here in full rather than proportionally split.

    cash_proceeds represents cash (non-CPF) proceeds from selling an
    existing property. Rather than adding to the OA balance directly, it
    offsets the total upfront cost bill BEFORE computing how much needs to
    come from CPF -- so cash proceeds genuinely reduce CPF usage, matching
    how a buyer would actually apply sale proceeds to a purchase.
    """
    total_upfront_costs = downpayment + stamp_duty + legal_fees
    cash_applied = min(cash_proceeds, total_upfront_costs)

    if total_upfront_costs > 0:
        downpayment_after_cash = downpayment - cash_applied * (downpayment / total_upfront_costs)
        stamp_duty_after_cash = stamp_duty - cash_applied * (stamp_duty / total_upfront_costs)
        legal_fees_after_cash = legal_fees - cash_applied * (legal_fees / total_upfront_costs)
    else:
        downpayment_after_cash = stamp_duty_after_cash = legal_fees_after_cash = 0

    if loan_type == "bank" and purchase_price > 0:
        mandatory_cash = 0.05 * purchase_price
        cpf_eligible_downpayment = max(downpayment_after_cash - mandatory_cash, 0)
    else:
        cpf_eligible_downpayment = downpayment_after_cash

    cpf_funded_downpayment = min(downpayment_after_cash, cpf_eligible_downpayment)

    balance = initial_total_oa
    balance += oa_credited_topup
    balance += usable_cpf_refund
    balance -= cpf_funded_downpayment
    balance -= stamp_duty_after_cash
    balance -= legal_fees_after_cash
    return balance


# BSD tiers as (upper bound of this tier, rate). Source: IRAS, residential
# BSD schedule effective 15 Feb 2023, unchanged as of 2026. ABSD is NOT
# included here -- it depends on citizenship/residency status and existing
# property count, which this app does not collect, so it must be entered
# manually if applicable.
BSD_TIERS = [
    (180_000, 0.01),
    (360_000, 0.02),
    (1_000_000, 0.03),
    (1_500_000, 0.04),
    (3_000_000, 0.05),
    (float("inf"), 0.06),
]


def calculate_bsd(purchase_price: float) -> float:
    """Compute Buyer's Stamp Duty using IRAS's progressive tiered schedule."""
    bsd = 0.0
    lower = 0
    for upper, rate in BSD_TIERS:
        if purchase_price <= lower:
            break
        taxable = min(purchase_price, upper) - lower
        bsd += taxable * rate
        lower = upper
    return round(bsd)


def explain_bsd_calculation(purchase_price: float) -> str:
    """
    Return a pre-computed, pre-formatted, tier-by-tier explanation of how
    the Buyer's Stamp Duty for a given purchase price is derived.

    This exists specifically so an LLM never has to reconstruct this
    tiered arithmetic itself when asked "how is this figure derived" --
    multi-step tiered tax arithmetic is exactly the kind of calculation
    language models get wrong even when instructed to be careful, and a
    second LLM-based verification pass doesn't reliably catch it either
    (both are text-based reasoning, not actual computation). Instead, the
    model is expected to relay this already-correct text, not generate
    its own breakdown.
    """
    lines = []
    lower = 0
    total = 0.0
    for upper, rate in BSD_TIERS:
        if purchase_price <= lower:
            break
        taxable = min(purchase_price, upper) - lower
        tax = taxable * rate
        total += tax
        if upper == float("inf"):
            lines.append(f"- Remaining amount above $3,000,000 (${taxable:,.0f}) at 6% = ${tax:,.0f}")
        else:
            lines.append(f"- ${taxable:,.0f} (from ${lower:,.0f} to ${upper:,.0f}) at {rate*100:.0f}% = ${tax:,.0f}")
        lower = upper

    total = round(total)
    breakdown = "\n".join(lines)
    return (
        f"For a purchase price of ${purchase_price:,.0f}, the Buyer's Stamp Duty "
        f"is calculated tier by tier:\n{breakdown}\nTotal Buyer's Stamp Duty = ${total:,.0f}"
    )
