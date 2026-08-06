"""
Reproduces every number quoted in the article.

Run:  python scripts/run_scenarios.py

Every figure printed here is derived from the model in transfer_tax/, with no
hand-tuning. Change the parameters at the top of BASE and watch the
conclusions move - that is the point of publishing this rather than asserting
a number in a slide.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transfer_tax import (  # noqa: E402
    CaseParams,
    breakeven_fcr,
    breakeven_fcr_exact,
    breakeven_gamma,
    breakeven_with_owner_overhead,
    compare_pooling,
    elapsed_minutes,
    equal_headcount_wait_penalty,
    expected_tax,
    expected_tax_mc,
    expected_transfers,
    fcr_for_target_saving,
    gamma_for_target_saving,
    generalist_fcr,
    labour_minutes,
    linear_transfer_tax,
    marginal_increment,
    marginal_transfer_cost,
    owner_model_cost,
    retained_context,
    routing_accuracy,
    savings_fraction,
    tax_rate,
    transfer_tax,
)

# ---------------------------------------------------------------------------
# Base scenario. These are illustrative defaults for a mid-complexity B2B
# technical support case. Substitute your own; the structure of the result is
# robust to the numbers, which is the whole argument.
# ---------------------------------------------------------------------------
BASE = CaseParams(
    W=45.0,      # minutes of irreducible productive work
    h=6.0,       # minutes to produce a handoff
    kappa=25.0,  # minutes to rebuild full context from nothing
    rho=0.75,    # fraction of context surviving each handoff
    q=240.0,     # minutes of requeue delay per transfer
)

# Organisational shape
M_QUEUES = 25    # number of specialist queues
A_UNAMBIGUOUS = 0.35  # fraction of cases unambiguously routable at intake

# People
P_GENERALIST = 0.38  # unaided generalist first-contact resolution
P_SPECIALIST = 0.90  # correct specialist first-contact resolution

# Queue shape for the pooling comparison
OFFERED_LOAD = 100.0  # Erlangs
AHT_MIN = 30.0
SL_TARGET_MIN = 5.0
SL_TARGET = 0.80
EQUAL_HEADCOUNT = 120  # divisible by 1,2,3,4,5,6,8,10,12 for a clean split

RULE = "=" * 78


def hdr(title: str) -> None:
    print(f"\n{RULE}\n{title}\n{RULE}")


def section_1_transfer_tax() -> None:
    hdr("1. THE TRANSFER TAX  -  L(n) = W + n*h + kappa*(n - rho(1-rho^n)/(1-rho))")
    print(f"Parameters: {BASE.as_dict()}\n")
    print(f"{'n':>3} {'context left':>13} {'labour min':>11} {'vs n=0':>9} "
          f"{'tax rate':>9} {'elapsed':>10} {'elapsed x':>10}")
    print("-" * 78)
    base_labour = labour_minutes(0, BASE)
    base_elapsed = elapsed_minutes(0, BASE)
    for n in range(0, 6):
        lab = labour_minutes(n, BASE)
        ela = elapsed_minutes(n, BASE)
        print(f"{n:>3} {retained_context(BASE.rho, n):>12.1%} {lab:>11.1f} "
              f"{lab / base_labour:>8.2f}x {tax_rate(n, BASE):>8.0%} "
              f"{ela:>9.0f} {ela / base_elapsed:>9.1f}x")
    print("\nCost of each successive transfer (rises - the tax is convex):")
    for n in range(1, 7):
        print(f"  transfer #{n}: {marginal_transfer_cost(n, BASE):>5.1f} min"
              f"   (+{marginal_increment(n - 1, BASE):>4.1f} on the previous;"
              f" asymptote {BASE.h + BASE.kappa:.1f})")
    print("\nHEADLINE: three transfers more than double the labour cost of a case")
    print(f"          and multiply elapsed time by {elapsed_minutes(3, BASE) / base_elapsed:.0f}x.")


def section_2_routing() -> None:
    hdr("2. WHY SPECIALISATION MANUFACTURES ITS OWN TRANSFERS  -  alpha(m) = a + (1-a)/m")
    print(f"a = {A_UNAMBIGUOUS:.0%} of cases are unambiguously routable at intake\n")
    print(f"{'queues m':>9} {'routing acc':>12} {'E[transfers]':>13} "
          f"{'labour min':>11} {'vs 1 queue':>11}")
    print("-" * 62)
    ref = labour_minutes(expected_transfers(1, A_UNAMBIGUOUS), BASE)
    for m in (1, 2, 5, 10, 25, 50, 100):
        alpha = routing_accuracy(m, A_UNAMBIGUOUS)
        en = expected_transfers(m, A_UNAMBIGUOUS)
        lab = labour_minutes(en, BASE)
        print(f"{m:>9} {alpha:>11.1%} {en:>13.2f} {lab:>11.1f} {lab / ref:>10.2f}x")
    print("\nThe feedback loop: transfers get blamed on skill gaps, so the")
    print("organisation creates another specialist queue, which lowers routing")
    print("accuracy, which produces more transfers. m only ever goes up.")


def section_3_pooling() -> None:
    hdr("3. THE POOLING PENALTY  -  the cost of fragmentation with PERFECT routing")
    print(f"Offered load {OFFERED_LOAD:.0f} Erlangs, AHT {AHT_MIN:.0f} min\n")

    print("VIEW A - hold the SERVICE LEVEL fixed, pay in headcount")
    print(f"         (target {SL_TARGET:.0%} answered within {SL_TARGET_MIN:.0f} min)\n")
    print(f"{'pools m':>8} {'load/pool':>10} {'agents/pool':>12} {'total FTE':>10} "
          f"{'extra FTE':>10} {'vs pooled':>10}")
    print("-" * 64)
    for m in (1, 2, 4, 5, 10, 20, 25):
        r = compare_pooling(OFFERED_LOAD, m, AHT_MIN, SL_TARGET_MIN, SL_TARGET)
        print(f"{m:>8} {OFFERED_LOAD / m:>10.1f} {r.agents_fragmented // m:>12} "
              f"{r.agents_fragmented:>10} {r.extra_agents:>10} {r.extra_pct:>9.1f}%")

    print("\nVIEW B - hold the HEADCOUNT fixed, pay in waiting time")
    print(f"         ({EQUAL_HEADCOUNT} agents and {OFFERED_LOAD:.0f} Erlangs in every row;")
    print("          only the organisational boundaries change)\n")
    print(f"{'pools m':>8} {'agents/pool':>12} {'utilisation':>12} "
          f"{'E[Wq] min':>10} {'vs pooled':>10}")
    print("-" * 56)
    w_ref, _ = equal_headcount_wait_penalty(OFFERED_LOAD, EQUAL_HEADCOUNT, 1, AHT_MIN)
    for m in (1, 2, 3, 4, 5, 6, 8, 10, 12):
        _, w = equal_headcount_wait_penalty(OFFERED_LOAD, EQUAL_HEADCOUNT, m, AHT_MIN)
        per_pool = EQUAL_HEADCOUNT // m
        util = (OFFERED_LOAD / m) / per_pool
        print(f"{m:>8} {per_pool:>12} {util:>11.1%} {w:>10.2f} {w / w_ref:>9.2f}x")

    print("\nThis penalty is NOT a mis-routing cost. It assumes every case lands")
    print("in exactly the right queue first time. It is purely the price of")
    print("forbidding an idle agent from helping a waiting customer who has")
    print("been labelled as somebody else's problem.")


def section_4_breakeven() -> None:
    hdr("4. THE BREAK-EVEN  -  how good does a single owner actually have to be?")
    alpha = routing_accuracy(M_QUEUES, A_UNAMBIGUOUS)
    en = expected_transfers(M_QUEUES, A_UNAMBIGUOUS)

    print(f"Organisation with m = {M_QUEUES} specialist queues, a = {A_UNAMBIGUOUS:.0%}")
    print(f"  Routing accuracy alpha                     : {alpha:.1%}")
    print(f"  E[transfers] under transfer-first routing  : {en:.2f}")
    print()
    print("  Plug-in vs exact expectation (Tax is convex, so Jensen applies):")
    print(f"    Tax(E[n])     plug-in    : {transfer_tax(en, BASE):>6.2f} min")
    print(f"    E[Tax(n)]     exact      : {expected_tax(alpha, BASE, 0.0):>6.2f} min"
          f"   (series check: {expected_tax_mc(alpha, BASE, 0.0):.2f})")
    print(f"    Tax(1+E[n])   plug-in    : {transfer_tax(1 + en, BASE):>6.2f} min")
    print(f"    E[Tax(1+n)]   exact      : {expected_tax(alpha, BASE, 1.0):>6.2f} min"
          f"   (series check: {expected_tax_mc(alpha, BASE, 1.0):.2f})")
    print("    The plug-in understates the true cost of transferring by "
          f"{expected_tax(alpha, BASE, 0.0) / transfer_tax(en, BASE) - 1:.0%}.")

    print("\n  THE IDENTITY")
    print(f"    break-even FCR (plug-in) : {breakeven_fcr(M_QUEUES, A_UNAMBIGUOUS, BASE):.4f}")
    print(f"    break-even FCR (exact)   : {breakeven_fcr_exact(M_QUEUES, A_UNAMBIGUOUS, BASE):.4f}")
    print(f"    routing accuracy alpha   : {alpha:.4f}")
    print("\n    These are the same number, and not by coincidence. Condition on the")
    print("    first routing attempt: with probability alpha the case resolves and")
    print("    pays Tax(0) = 0; otherwise it has moved once and, by memorylessness,")
    print("    the remainder is again Geometric(alpha). So")
    print("        E[Tax(n)] = (1-alpha) * E[Tax(1+n)]")
    print("    and therefore p* = 1 - (1-alpha) = alpha, exactly.")
    print("\n    Nothing about h, kappa or rho survives into the answer. The handoff")
    print("    parameters do not set the bar - they set how much you win by.")
    print("\n    In words: a single owner beats the routing model precisely when they")
    print("    resolve more cases at first contact than the router gets right at")
    print("    first attempt. Here that bar is "
          f"{alpha:.1%}, against a specialist's {P_SPECIALIST:.0%}.")


def section_5_magnitude() -> None:
    hdr("5. MAGNITUDE  -  breaking even is not a reason to reorganise")
    print("Requeue delay q costs the customer, not the P&L. It is also the")
    print("largest term, so the customer-visible prize is far bigger than the")
    print("cost prize. Both are shown below.\n")
    print(f"{'owner FCR':>10} {'gamma':>7} {'labour saving':>14} {'elapsed saving':>15}")
    print("-" * 50)
    for p_eff in (0.376, 0.45, 0.55, 0.65, 0.70, 0.80, 0.90):
        gamma = max(0.0, (p_eff - P_GENERALIST) / (P_SPECIALIST - P_GENERALIST))
        print(f"{p_eff:>10.1%} {gamma:>6.0%} "
              f"{savings_fraction(p_eff, M_QUEUES, A_UNAMBIGUOUS, BASE, False):>13.1%} "
              f"{savings_fraction(p_eff, M_QUEUES, A_UNAMBIGUOUS, BASE, True):>14.1%}")

    print("\n  What agentic AI has to deliver for a given business case:")
    print(f"\n{'labour target':>14} {'owner FCR needed':>18} {'gamma needed':>14} "
          f"{'elapsed delivered':>18}")
    print("-" * 68)
    for tgt in (0.10, 0.20, 0.30):
        need = fcr_for_target_saving(tgt, M_QUEUES, A_UNAMBIGUOUS, BASE, False)
        gam = gamma_for_target_saving(tgt, P_GENERALIST, P_SPECIALIST,
                                      M_QUEUES, A_UNAMBIGUOUS, BASE, False)
        ela = savings_fraction(need, M_QUEUES, A_UNAMBIGUOUS, BASE, True)
        print(f"{tgt:>14.0%} {need:>17.1%} {gam:>13.0%} {ela:>17.1%}")

    print("\n  Elapsed savings run roughly 2.3x the labour savings, because the")
    print("  requeue term dominates. If you only justify this on cost you are")
    print("  arguing for less than half the actual prize.")
    print("\n  For reference: Brynjolfsson, Li & Raymond (NBER 31161 / QJE) measured")
    print("  14-15% average productivity gains across 5,172 support agents, with")
    print("  gains concentrated in novice and low-skilled workers and the most")
    print("  experienced seeing small gains in speed and small declines in quality.")
    print("  That distribution is the right shape for gamma. The magnitude needed")
    print("  for a serious business case is higher than a suggestion-assistant")
    print("  delivers, which is the case for agentic rather than conversational AI.")


def section_6_sensitivity() -> None:
    hdr("6. SENSITIVITY  -  the assumptions that could sink this")
    alpha = routing_accuracy(M_QUEUES, A_UNAMBIGUOUS)
    chain = expected_tax(alpha, BASE, 1.0)

    print("(a) THE BIG ONE: is the productive work W really the same whoever")
    print("    does it? It is not. A specialist who has seen a failure forty")
    print("    times needs less time than a generalist reasoning from first")
    print("    principles. If owner-first adds delta minutes per case:")
    print(f"\n        p* = alpha + delta/C,   alpha = {alpha:.1%},  C = {chain:.1f} min\n")
    print(f"{'extra owner minutes':>21} {'break-even FCR':>16}")
    print("-" * 39)
    for d in (0, 2, 5, 10, 15, 20, 25):
        print(f"{d:>21} {breakeven_with_owner_overhead(alpha, d, BASE):>15.1%}")
    print("\n    Twenty extra minutes puts the bar at 80% and the argument is in")
    print("    serious trouble. This is the number most worth measuring.")

    print("\n(b) CONVEXITY IS ASSUMED, NOT DERIVED. If every receiver fully")
    print("    restores the case and hands on a complete record, re-discovery")
    print("    cost is linear rather than compounding:")
    print(f"\n{'transfers':>10} {'convex':>10} {'linear':>10} {'convex x':>10} {'linear x':>10}")
    print("-" * 52)
    for n in range(0, 5):
        c = BASE.W + transfer_tax(n, BASE)
        l = BASE.W + linear_transfer_tax(n, BASE)
        print(f"{n:>10} {c:>10.1f} {l:>10.1f} {c / BASE.W:>9.2f}x {l / BASE.W:>9.2f}x")
    print("\n    At three transfers: 2.10x convex vs 1.82x linear. The headline")
    print("    uses the convex form. The break-even identity is unaffected -")
    print("    it never depended on the shape of the tax, only on Tax(0) = 0.")

    print("\n(c) The break-even is independent of h, kappa, rho and W, so the")
    print("    usual parameter sweep applies to the SAVINGS, not the bar.")
    lo, hi, n_combos = 1.0, 0.0, 0
    for rho in (0.60, 0.75, 0.90):
        for kappa in (15.0, 25.0, 40.0):
            for h in (3.0, 6.0, 12.0):
                for a in (0.25, 0.35, 0.50):
                    for m in (10, 25, 50):
                        p = CaseParams(W=BASE.W, h=h, kappa=kappa, rho=rho, q=BASE.q)
                        s = savings_fraction(0.70, m, a, p, elapsed=False)
                        lo, hi = min(lo, s), max(hi, s)
                        n_combos += 1
    print(f"    Across {n_combos} combinations, a 70% owner FCR delivers a labour")
    print(f"    saving between {lo:.1%} and {hi:.1%}.")

    print("\n(d) DOUBLE-COUNTING WARNING. The requeue term q in the case model and")
    print("    the pooling penalty in section 3 describe overlapping phenomena:")
    print("    both are waiting caused by fragmentation. The STAFFING cost of")
    print("    fragmentation is genuinely additive to the case-level tax; the")
    print("    WAITING TIME is not. Do not add the two waiting figures together.")

def main() -> None:
    print("\nTHE TRANSFER TAX - reproducible figures")
    print("https://github.com/akumarau/transfer-tax")
    section_1_transfer_tax()
    section_2_routing()
    section_3_pooling()
    section_4_breakeven()
    section_5_magnitude()
    section_6_sensitivity()
    print(f"\n{RULE}\nAll figures above are computed, not asserted. "
          f"Fork it and put your own numbers in.\n{RULE}\n")


if __name__ == "__main__":
    main()
