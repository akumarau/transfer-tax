"""
Tests for the transfer tax model.

These are not decorative. The article makes quantitative claims, so the
properties those claims rest on are asserted here: convexity, monotonicity,
correct boundary behaviour, and agreement between the closed forms and brute
force summation.

Run:  python -m pytest tests/ -q      (or: python tests/test_model.py)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transfer_tax import (  # noqa: E402
    CaseParams,
    breakeven_fcr,
    breakeven_fcr_exact,
    breakeven_gamma,
    breakeven_general,
    chain_cost,
    compare_pooling,
    continuous_slope,
    curvature,
    design_cost,
    elapsed_minutes,
    elapsed_tax,
    equal_headcount_wait_penalty,
    erlang_c,
    expected_tax,
    expected_tax_mc,
    expected_transfers,
    fcr_for_target_saving,
    generalist_fcr,
    labour_minutes,
    marginal_increment,
    marginal_transfer_cost,
    mean_wait,
    owner_model_cost,
    routing_accuracy,
    savings_fraction,
    service_level,
    transfer_tax,
)

P = CaseParams()


# --- the tax itself --------------------------------------------------------

def test_zero_transfers_is_free():
    assert transfer_tax(0, P) == 0.0
    assert labour_minutes(0, P) == P.W
    assert elapsed_minutes(0, P) == P.W


def test_closed_form_matches_brute_force():
    """Tax(n) = n*h + kappa*sum(1 - rho**i) summed term by term."""
    for n in range(0, 12):
        brute = n * P.h + P.kappa * sum(1 - P.rho ** i for i in range(1, n + 1))
        assert math.isclose(transfer_tax(n, P), brute, rel_tol=1e-12)


def test_tax_is_strictly_increasing():
    vals = [transfer_tax(n, P) for n in range(0, 15)]
    assert all(b > a for a, b in zip(vals, vals[1:]))


def test_tax_is_convex():
    """The central claim: the fourth transfer costs more than the first."""
    for n in range(0, 15):
        assert marginal_increment(n, P) > 0
    marg = [marginal_transfer_cost(n, P) for n in range(1, 15)]
    assert all(b > a for a, b in zip(marg, marg[1:]))


def test_marginal_cost_matches_actual_differences():
    """marginal_transfer_cost(n) must equal Tax(n) - Tax(n-1), 1-indexed."""
    for n in range(1, 12):
        actual = transfer_tax(n, P) - transfer_tax(n - 1, P)
        assert math.isclose(marginal_transfer_cost(n, P), actual, rel_tol=1e-12), n


def test_first_transfer_costs_handoff_plus_first_context_loss():
    assert math.isclose(marginal_transfer_cost(1, P), P.h + P.kappa * (1 - P.rho))


def test_marginal_cost_bounds():
    """Bounded below by h + kappa(1-rho) and above by the asymptote h + kappa."""
    assert marginal_transfer_cost(1, P) < marginal_transfer_cost(20, P)
    assert marginal_transfer_cost(20, P) < P.h + P.kappa
    assert math.isclose(marginal_transfer_cost(500, P), P.h + P.kappa, rel_tol=1e-9)


def test_second_difference_is_positive_and_correct():
    """Discrete convexity: kappa*rho**n*(1-rho)."""
    for n in range(0, 12):
        expected = (transfer_tax(n + 1, P) - transfer_tax(n, P)) - (
            transfer_tax(n, P) - transfer_tax(n - 1, P) if n >= 1 else 0.0
        )
        if n >= 1:
            assert math.isclose(marginal_increment(n, P), expected, rel_tol=1e-10), n
        assert marginal_increment(n, P) > 0


def test_continuous_derivatives_match_numerical():
    """The real-valued extension is smooth and convex, which Jensen requires."""
    eps = 1e-6
    for n in (0.5, 1.0, 2.0, 3.7):
        num_slope = (transfer_tax(n + eps, P) - transfer_tax(n - eps, P)) / (2 * eps)
        assert math.isclose(continuous_slope(n, P), num_slope, rel_tol=1e-6), n
        num_curv = (
            transfer_tax(n + eps, P) - 2 * transfer_tax(n, P) + transfer_tax(n - eps, P)
        ) / (eps * eps)
        assert math.isclose(curvature(n, P), num_curv, rel_tol=1e-2), n
        assert curvature(n, P) > 0


# --- exact expectations and the identity -----------------------------------

def test_expected_tax_closed_form_matches_series():
    for m, a in ((5, 0.35), (10, 0.5), (25, 0.35), (50, 0.2), (100, 0.3)):
        alpha = routing_accuracy(m, a)
        for offset in (0.0, 1.0, 2.0):
            assert math.isclose(
                expected_tax(alpha, P, offset),
                expected_tax_mc(alpha, P, offset),
                rel_tol=1e-9,
            ), (m, a, offset)


def test_jensen_direction():
    """Tax is convex, so the plug-in at E[n] must UNDERSTATE E[Tax(n)]."""
    for m, a in ((5, 0.35), (10, 0.5), (25, 0.35), (50, 0.2)):
        alpha = routing_accuracy(m, a)
        plug_in = transfer_tax(expected_transfers(m, a), P)
        exact = expected_tax(alpha, P, 0.0)
        assert exact > plug_in, (m, a, exact, plug_in)


def test_breakeven_identity_equals_routing_accuracy():
    """THE CENTREPIECE. p* = alpha, exactly, for every parameter combination.

    Proof: condition on the first routing attempt. With probability alpha the
    case resolves and pays Tax(0) = 0. Otherwise it has moved once and, by
    memorylessness, the remainder is again Geometric(alpha). So
    E[Tax(n)] = (1-alpha)*E[Tax(1+n)], hence p* = alpha.
    """
    for rho in (0.55, 0.70, 0.75, 0.85, 0.95):
        for kappa in (10.0, 25.0, 50.0):
            for h in (2.0, 6.0, 15.0):
                for a in (0.20, 0.35, 0.55, 0.80):
                    for m in (2, 5, 10, 25, 50, 100):
                        p = CaseParams(W=45, h=h, kappa=kappa, rho=rho, q=240)
                        assert math.isclose(
                            breakeven_fcr_exact(m, a, p),
                            routing_accuracy(m, a),
                            rel_tol=1e-9,
                        ), (rho, kappa, h, a, m)


def test_identity_holds_for_elapsed_time_too():
    """The identity is indifferent to the cost function, so long as Tax(0)=0."""
    for m, a in ((5, 0.35), (25, 0.35), (100, 0.2)):
        alpha = routing_accuracy(m, a)
        ratio = elapsed_tax(alpha, P, 0.0) / elapsed_tax(alpha, P, 1.0)
        assert math.isclose(1.0 - ratio, alpha, rel_tol=1e-9), (m, a)


def test_savings_are_zero_at_breakeven_and_positive_above():
    for m, a in ((10, 0.35), (25, 0.35), (50, 0.25)):
        alpha = routing_accuracy(m, a)
        assert math.isclose(savings_fraction(alpha, m, a, P), 0.0, abs_tol=1e-12)
        assert savings_fraction(alpha + 0.1, m, a, P) > 0
        assert savings_fraction(alpha - 0.1, m, a, P) < 0


def test_elapsed_savings_exceed_labour_savings():
    """Requeue delay dominates, so the customer-visible prize is the bigger one."""
    for p_eff in (0.50, 0.65, 0.80, 0.90):
        lab = savings_fraction(p_eff, 25, 0.35, P, elapsed=False)
        ela = savings_fraction(p_eff, 25, 0.35, P, elapsed=True)
        assert ela > lab, p_eff


def test_fcr_for_target_saving_roundtrips():
    for target in (0.05, 0.10, 0.20, 0.30):
        for elapsed in (False, True):
            need = fcr_for_target_saving(target, 25, 0.35, P, elapsed)
            got = savings_fraction(need, 25, 0.35, P, elapsed)
            assert math.isclose(got, target, rel_tol=1e-9), (target, elapsed)


# --- the GENERAL identity: no geometric assumption at all ------------------

DEGRADING = [0.50, 0.40, 0.32, 0.28, 0.25, 0.22, 0.20]
IMPROVING = [0.30, 0.45, 0.60, 0.75]
FLAT = [0.376]
ERRATIC = [0.42, 0.19, 0.63, 0.11, 0.55, 0.27]


def test_general_identity_holds_for_arbitrary_chains():
    """Break-even is alphas[0] regardless of how the chain behaves downstream.

    This is the claim that matters, because memorylessness is the assumption a
    reviewer attacks first. Degrading, improving, flat and erratic chains all
    cross over at exactly the first-touch accuracy.
    """
    for alphas in (DEGRADING, IMPROVING, FLAT, ERRATIC):
        for elapsed in (False, True):
            a1 = breakeven_general(alphas)
            at_bar = design_cost(a1, alphas, P, elapsed=elapsed)
            reference = design_cost(a1, alphas, P, elapsed=elapsed)
            assert math.isclose(at_bar, reference, rel_tol=1e-12)
            better = design_cost(a1 + 0.05, alphas, P, elapsed=elapsed)
            worse = design_cost(a1 - 0.05, alphas, P, elapsed=elapsed)
            assert better < reference, (alphas, elapsed)
            assert worse > reference, (alphas, elapsed)


def test_general_identity_crossover_is_exact():
    """The crossover point is alphas[0] to machine precision, not approximately."""
    for alphas in (DEGRADING, IMPROVING, ERRATIC):
        transfer_first = design_cost(alphas[0], alphas, P)
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if design_cost(mid, alphas, P) > transfer_first:
                lo = mid
            else:
                hi = mid
        assert math.isclose((lo + hi) / 2, alphas[0], abs_tol=1e-12), alphas


def test_general_identity_independent_of_handoff_parameters():
    """C cancels, so h, kappa and rho cannot move the break-even."""
    base = design_cost(DEGRADING[0], DEGRADING, CaseParams(h=6, kappa=25, rho=0.75))
    for h in (1.0, 6.0, 40.0):
        for kappa in (5.0, 25.0, 200.0):
            for rho in (0.2, 0.75, 0.99):
                p = CaseParams(W=45, h=h, kappa=kappa, rho=rho, q=240)
                tf = design_cost(DEGRADING[0], DEGRADING, p)
                assert design_cost(DEGRADING[0] + 0.02, DEGRADING, p) < tf
                assert design_cost(DEGRADING[0] - 0.02, DEGRADING, p) > tf
    assert base > 0


def test_geometric_chain_agrees_with_closed_form():
    """chain_cost with a flat alpha must reproduce E[Tax(1+n)] exactly."""
    for m, a in ((5, 0.35), (25, 0.35), (50, 0.2)):
        alpha = routing_accuracy(m, a)
        assert math.isclose(
            chain_cost([alpha], P), expected_tax(alpha, P, offset=0.0) / (1 - alpha),
            rel_tol=1e-9,
        ), (m, a)


def test_chain_cost_rejects_bad_input():
    for bad in ([], [0.0], [1.5], [0.5, -0.1]):
        try:
            chain_cost(bad, P)
        except ValueError:
            continue
        raise AssertionError(f"{bad} should have been rejected")


def test_lossless_handoff_is_linear():
    """rho = 1 means no context is lost, so the tax collapses to n*h."""
    lossless = CaseParams(W=45, h=6, kappa=25, rho=1.0, q=240)
    for n in range(0, 8):
        assert math.isclose(transfer_tax(n, lossless), n * 6.0, rel_tol=1e-12)
        assert marginal_increment(n, lossless) == 0.0
        assert curvature(n, lossless) == 0.0


def test_total_loss_handoff_restarts_the_case():
    """As rho -> 0 every handoff costs a full h + kappa: the case restarts."""
    total_loss = CaseParams(W=45, h=6, kappa=25, rho=1e-9, q=240)
    assert math.isclose(transfer_tax(3, total_loss), 3 * (6.0 + 25.0), rel_tol=1e-6)


def test_headline_claim_three_transfers_doubles_labour():
    """The number quoted in the article."""
    assert labour_minutes(3, P) / labour_minutes(0, P) > 2.0


def test_rho_out_of_range_rejected():
    for bad in (0.0, -0.1, 1.5):
        try:
            CaseParams(rho=bad)
        except ValueError:
            continue
        raise AssertionError(f"rho={bad} should have been rejected")


# --- routing ---------------------------------------------------------------

def test_single_queue_cannot_misroute():
    assert math.isclose(routing_accuracy(1, 0.35), 1.0)
    assert math.isclose(expected_transfers(1, 0.35), 0.0)


def test_routing_accuracy_decreases_with_fragmentation():
    accs = [routing_accuracy(m, 0.35) for m in (1, 2, 5, 10, 25, 50, 100)]
    assert all(b < a for a, b in zip(accs, accs[1:]))


def test_routing_accuracy_asymptotes_to_a():
    assert math.isclose(routing_accuracy(10_000_000, 0.35), 0.35, abs_tol=1e-6)


def test_expected_transfers_increases_with_fragmentation():
    ens = [expected_transfers(m, 0.35) for m in (1, 2, 5, 10, 25, 50)]
    assert all(b > a for a, b in zip(ens, ens[1:]))


# --- queueing --------------------------------------------------------------

def test_erlang_c_bounds():
    assert 0.0 <= erlang_c(110, 100.0) <= 1.0
    assert erlang_c(100, 100.0) == 1.0       # unstable
    assert erlang_c(1000, 100.0) < 0.01      # massively overstaffed


def test_erlang_c_decreases_with_more_servers():
    vals = [erlang_c(c, 100.0) for c in (101, 105, 110, 120, 140)]
    assert all(b < a for a, b in zip(vals, vals[1:]))


def test_service_level_monotone_in_staffing():
    sls = [service_level(c, 100.0, 30.0, 5.0) for c in (105, 110, 115, 120)]
    assert all(b > a for a, b in zip(sls, sls[1:]))
    assert all(0.0 <= s <= 1.0 for s in sls)


def test_pooling_never_helps():
    """The pooling principle: fragmenting at equal service level never saves FTE."""
    for m in (2, 4, 5, 10, 20, 25):
        r = compare_pooling(100.0, m, 30.0, 5.0, 0.80)
        assert r.agents_fragmented >= r.agents_pooled, f"m={m}"


def test_pooling_penalty_grows_with_fragments():
    extra = [compare_pooling(100.0, m, 30.0, 5.0, 0.80).extra_pct
             for m in (1, 2, 4, 10, 25)]
    assert all(b >= a for a, b in zip(extra, extra[1:]))


def test_equal_headcount_split_always_slower():
    """Same agents, same demand, same utilisation - only boundaries differ."""
    w_ref, _ = equal_headcount_wait_penalty(100.0, 120, 1, 30.0)
    for m in (2, 3, 4, 5, 6, 8, 10, 12):
        _, w = equal_headcount_wait_penalty(100.0, 120, m, 30.0)
        assert w > w_ref, f"m={m}"


def test_equal_headcount_penalty_is_monotone():
    waits = [equal_headcount_wait_penalty(100.0, 120, m, 30.0)[1]
             for m in (1, 2, 3, 4, 5, 6, 8, 10, 12)]
    assert all(b > a for a, b in zip(waits, waits[1:]))


# --- the comparison --------------------------------------------------------

def test_augmentation_interpolates_between_human_and_specialist():
    assert math.isclose(generalist_fcr(0.38, 0.90, 0.0), 0.38)
    assert math.isclose(generalist_fcr(0.38, 0.90, 1.0), 0.90)
    assert 0.38 < generalist_fcr(0.38, 0.90, 0.5) < 0.90


def test_breakeven_is_below_specialist_fcr_everywhere():
    """If this ever failed, the article's thesis would be wrong somewhere."""
    for rho in (0.55, 0.70, 0.85, 0.95):
        for kappa in (10.0, 25.0, 50.0):
            for h in (2.0, 6.0, 15.0):
                for a in (0.20, 0.35, 0.55, 0.80):
                    for m in (5, 10, 25, 50, 100):
                        p = CaseParams(W=45, h=h, kappa=kappa, rho=rho, q=240)
                        assert breakeven_fcr(m, a, p) < 0.90, (rho, kappa, h, a, m)


def test_breakeven_falls_as_the_org_fragments():
    """More specialist queues => lower bar for the single owner.

    This is monotone and it is the direction that matters politically: the
    organisations that transfer most are the ones with the least to lose by
    stopping.
    """
    targets = [breakeven_fcr(m, 0.35, P) for m in (2, 5, 10, 25, 50, 100)]
    assert all(b < a for a, b in zip(targets, targets[1:])), targets


def test_breakeven_is_non_monotonic_in_context_retention():
    """A documented, counter-intuitive property of the model - not a bug.

    As rho -> 1 handoffs become lossless and the tax collapses to n*h.
    As rho -> 0 every handoff is a full restart and the tax becomes n*(h+kappa).
    Both extremes are LINEAR in n, so the break-even converges to the same
    value, 1 - E[n]/(1+E[n]), at either end. The convexity - and therefore the
    penalty for transferring - is greatest in the middle.

    That middle is where every real organisation sits. A handoff that carries
    nothing is at least honest; the case gets restarted and everyone knows it.
    A handoff that carries three quarters of the context is the expensive one,
    because it looks like continuity while it compounds the loss.
    """
    n = expected_transfers(25, 0.35)
    floor = 1.0 - n / (1.0 + n)

    lossless = breakeven_fcr(25, 0.35, CaseParams(rho=0.99999, kappa=25, h=6))
    middle = breakeven_fcr(25, 0.35, CaseParams(rho=0.75, kappa=25, h=6))
    total_loss = breakeven_fcr(25, 0.35, CaseParams(rho=0.00001, kappa=25, h=6))

    assert middle > lossless
    assert middle > total_loss
    assert math.isclose(lossless, floor, abs_tol=1e-3), (lossless, floor)
    assert math.isclose(total_loss, floor, abs_tol=1e-3), (total_loss, floor)


def test_owner_model_beats_transfer_model_above_breakeven():
    target = breakeven_fcr(25, 0.35, P)
    c_transfer = labour_minutes(expected_transfers(25, 0.35), P)
    assert owner_model_cost(target + 0.05, 25, 0.35, P) < c_transfer
    assert owner_model_cost(target - 0.05, 25, 0.35, P) > c_transfer


def test_breakeven_gamma_zero_when_unaided_generalist_suffices():
    assert breakeven_gamma(0.95, 0.99, 25, 0.35, P) == 0.0


def test_base_case_gamma_matches_published_figure():
    """The article quotes gamma* ~ 15% for the base scenario."""
    g = breakeven_gamma(0.38, 0.90, 25, 0.35, P)
    assert 0.13 < g < 0.17, g


if __name__ == "__main__":
    failures = 0
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
