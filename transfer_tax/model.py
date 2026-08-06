"""
The Transfer Tax: a case-level cost model for handoffs in support operations.

Core idea
---------
The productive work required to resolve a case, W, is a property of the case,
not of the organisation. Everything an organisation adds on top of W in order
to move that case between people is overhead. This module prices that overhead.

Each transfer costs three things:

  1. h      - handoff production: writing the summary, dispositioning, tagging.
  2. q      - requeue delay: the case goes back into a queue and waits.
  3. r_i    - re-discovery: the new owner rebuilds the context that was lost.

The third term is the one organisations never budget for, and it is the reason
the tax is convex rather than linear. Context is not fully transmitted across a
handoff. If a handoff carries a fraction rho of the accumulated context, then
after i handoffs the surviving context is rho**i, and the cost of rebuilding
what was lost is proportional to the loss:

    r_i = kappa * (1 - rho**i)

where kappa is the cost of reconstructing the case from nothing.

Summing over n transfers gives a closed form (geometric series):

    Tax(n) = n*h + kappa * ( n - rho*(1 - rho**n)/(1 - rho) )

    L(n)   = W + Tax(n)                       (labour minutes)
    E(n)   = L(n) + n*q                       (elapsed minutes to the customer)

Two properties matter.

    dL/dn   = h + kappa*(1 - rho**n)          > 0, strictly increasing
    d2L/dn2 = kappa * rho**n * ln(1/rho)      > 0 for rho < 1

The marginal cost of a transfer rises with the number of transfers already
made. The fourth transfer costs more than the first. In the limit each transfer
costs h + kappa, which is to say the case is restarted from scratch every time
it moves.

Author: Anupam Kumar
License: MIT
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CaseParams:
    """Parameters of a single support case and its handoff economics.

    All times are in minutes.

    Attributes
    ----------
    W : float
        Irreducible productive work required to resolve the case: the
        diagnosis, the fix, the verification. Independent of who does it.
    h : float
        Handoff production cost per transfer, borne by the sender. Summary
        notes, disposition codes, internal routing form.
    kappa : float
        Cost of reconstructing the full case context from nothing. The
        re-discovery cost of a total context loss.
    rho : float
        Context retention per handoff, in (0, 1]. rho = 1 means a handoff is
        lossless (no real organisation achieves this). rho = 0.75 means each
        handoff carries three quarters of what the previous owner knew.
    q : float
        Requeue delay per transfer: elapsed wall-clock time the case spends
        waiting in the next queue. Costs the customer, not the P&L, which is
        precisely why it is under-managed.
    """

    W: float = 45.0
    h: float = 6.0
    kappa: float = 25.0
    rho: float = 0.75
    q: float = 240.0

    def __post_init__(self) -> None:
        if not 0.0 < self.rho <= 1.0:
            raise ValueError("rho must be in (0, 1]")
        for name in ("W", "h", "kappa", "q"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    def as_dict(self) -> dict:
        return asdict(self)


def retained_context(rho: float, n: float) -> float:
    """Fraction of original context surviving after n handoffs: rho**n."""
    return rho ** n


def _geometric_sum(rho: float, n: float) -> float:
    """Sum_{i=1..n} rho**i, in closed form, valid for real n >= 0.

    For rho == 1 this degenerates to n.
    """
    if math.isclose(rho, 1.0):
        return n
    return rho * (1.0 - rho ** n) / (1.0 - rho)


def transfer_tax(n: float, p: CaseParams) -> float:
    """Overhead minutes added by n transfers. Tax(0) == 0.

    Tax(n) = n*h + kappa * ( n - sum_{i=1..n} rho**i )

    Accepts non-integer n so that expected transfer counts can be passed
    directly. The function is smooth and convex, so evaluating at E[n] is a
    conservative (under-, not over-, stating) approximation of E[Tax(n)] by
    Jensen's inequality: E[Tax(n)] >= Tax(E[n]).

    IMPORTANT - CONVEXITY IS AN ASSUMPTION, NOT A CONSEQUENCE.
    Lossy handoffs alone do not produce a convex tax. This form assumes that
    context a receiver rebuilds does NOT fully re-enter the transferable
    record, so losses accumulate against the ORIGINAL context and the surviving
    fraction is rho**i. If instead every receiver fully restores the case and
    hands on a complete record, each handoff loses the same 1-rho of a
    refreshed whole and the cost is linear: see `linear_transfer_tax`.

    Both are defensible readings of "a handoff transmits a fraction rho".
    Reality is somewhere between, and which one your organisation resembles is
    an empirical question about whether your engineers write up what they
    learned or merely resolve and move on. The convex form is the pessimistic
    one; the article's headline figures use it, and `linear_transfer_tax` is
    provided so the difference can be seen rather than argued about.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return n * p.h + p.kappa * (n - _geometric_sum(p.rho, n))


def linear_transfer_tax(n: float, p: CaseParams) -> float:
    """The non-convex alternative: every receiver fully restores and retransmits.

        Tax_linear(n) = n*h + n*kappa*(1 - rho)

    Each handoff loses the same fraction of a refreshed whole, so re-discovery
    cost is the same at every hop and the tax is linear in n. This is the
    charitable reading of the same verbal model, and it matters: at three
    transfers it gives 1.82x the single-owner labour cost rather than 2.10x.

    Note that the break-even identity is completely unaffected by this choice,
    because it never depended on the shape of the tax - only on Tax(0) = 0,
    which both forms satisfy. The choice changes the magnitude of the prize,
    not who wins.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return n * p.h + n * p.kappa * (1.0 - p.rho)


def labour_minutes(n: float, p: CaseParams) -> float:
    """Total human minutes consumed by a case that is transferred n times."""
    return p.W + transfer_tax(n, p)


def elapsed_minutes(n: float, p: CaseParams) -> float:
    """Wall-clock minutes from the customer's point of view."""
    return labour_minutes(n, p) + n * p.q


def tax_rate(n: float, p: CaseParams) -> float:
    """Transfer tax as a fraction of the irreducible work: Tax(n)/W."""
    return transfer_tax(n, p) / p.W


def marginal_transfer_cost(n: float, p: CaseParams) -> float:
    """Cost of the n-th transfer: Tax(n) - Tax(n-1) = h + kappa*(1 - rho**n).

    Note the indexing. n is 1-based here: marginal_transfer_cost(1) is the cost
    of the FIRST transfer, h + kappa*(1-rho), not h. A case that has never been
    transferred has paid nothing; the first move already costs a handoff plus
    the first slice of context loss.

    Rises monotonically from h + kappa*(1-rho) toward the asymptote h + kappa,
    at which point a handoff transmits nothing and the case is simply restarted.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return p.h + p.kappa * (1.0 - p.rho ** n)


def marginal_increment(n: float, p: CaseParams) -> float:
    """Second difference: how much more the (n+1)-th transfer costs than the n-th.

        Delta2(n) = [Tax(n+1) - Tax(n)] - [Tax(n) - Tax(n-1)]
                  = kappa * rho**n * (1 - rho)

    Strictly positive for rho < 1, which is the discrete statement of convexity
    and the one that matters, since n counts transfers and is an integer.
    """
    if math.isclose(p.rho, 1.0):
        return 0.0
    return p.kappa * (p.rho ** n) * (1.0 - p.rho)


def curvature(n: float, p: CaseParams) -> float:
    """Continuous second derivative, d2Tax/dn2, for the real-valued extension.

        dTax/dn   = h + kappa*(1 + rho**(n+1) * ln(rho)/(1-rho))
        d2Tax/dn2 = kappa * rho**(n+1) * ln(rho)**2 / (1-rho)     > 0

    Needed only to justify applying Jensen's inequality to a non-integer
    argument. For the discrete convexity claim use `marginal_increment`, which
    is cleaner and is what the article quotes.
    """
    if math.isclose(p.rho, 1.0):
        return 0.0
    return p.kappa * (p.rho ** (n + 1)) * (math.log(p.rho) ** 2) / (1.0 - p.rho)


def continuous_slope(n: float, p: CaseParams) -> float:
    """dTax/dn for the real-valued extension. Positive for all n >= 0."""
    if math.isclose(p.rho, 1.0):
        return p.h
    return p.h + p.kappa * (1.0 + (p.rho ** (n + 1)) * math.log(p.rho) / (1.0 - p.rho))


# ---------------------------------------------------------------------------
# Where transfers come from: routing accuracy under fragmentation
# ---------------------------------------------------------------------------

def routing_accuracy(m: int, a: float) -> float:
    """ILLUSTRATIVE model of how first-touch resolution degrades with fragmentation.

    READ THIS BEFORE USING IT. This function is a toy, and it is deliberately
    separate from the identity in `breakeven_general`. Two distinct quantities
    must not be confused:

      - P(correct queue)  - the router picks the right destination.
      - P(first-touch resolution) - the first team to touch the case actually
        finishes it.

    These are not the same. A case can land in exactly the right queue and still
    be bounced; a case can land in the wrong queue and be resolved anyway. The
    break-even identity is stated in terms of the SECOND quantity, which is
    directly measurable: the fraction of cases resolved by the team they were
    first assigned to, with no reassignment.

    What this function provides is only a story about why that second quantity
    is low in fragmented organisations. If `a` is the fraction of cases whose
    destination is unambiguous at intake, and the rest are effectively spread
    across m queues:

        alpha(m) = a + (1 - a)/m

    alpha(1) = 1 by construction. Strictly decreasing in m, asymptoting to a.

    A hostile operations researcher would make three fair objections, and they
    are all correct: `a` should itself fall as m rises, since finer
    fragmentation makes fewer cases unambiguous; misrouting is not uniform but
    concentrated among confusable neighbouring specialities; and landing in the
    right queue does not imply resolution. All three make the real curve fall
    FASTER than this one. The function is therefore optimistic about
    fragmentation, which is the safe direction for the argument being made.

    Prefer measuring your own first-touch resolution rate and passing it
    directly to `design_cost` / `breakeven_general`. Use this only for the
    comparative-statics story.
    """
    if m < 1:
        raise ValueError("m must be at least 1")
    if not 0.0 <= a <= 1.0:
        raise ValueError("a must be in [0, 1]")
    return a + (1.0 - a) / m


def expected_transfers(m: int, a: float) -> float:
    """E[n] under geometric re-routing: E[touches] = 1/alpha, E[n] = 1/alpha - 1."""
    return 1.0 / routing_accuracy(m, a) - 1.0


def plugin_case_cost(m: int, a: float, p: CaseParams) -> float:
    """Plug-in approximation Tax(E[n]), retained only for comparison.

    NOT an expected cost. Because Tax is convex, Jensen's inequality makes this
    strictly smaller than the true E[Tax(n)]. Use `transfer_model_cost_exact`.
    """
    return labour_minutes(expected_transfers(m, a), p)


# Deprecated alias: the old name misdescribed what this computes.
expected_case_cost = plugin_case_cost


# ---------------------------------------------------------------------------
# Exact expectations over the transfer distribution
#
# Evaluating Tax at the single point E[n] is not the same as E[Tax(n)], and
# because Tax is convex, Jensen's inequality guarantees Tax(E[n]) <= E[Tax(n)].
# The plug-in version therefore UNDERSTATES the true cost of transferring - it
# is conservative in the direction that hurts this article's argument, which is
# the right way round for a plug-in approximation to be wrong.
#
# But "conservative" is not the same as "correct", so the exact result is
# computed here in closed form and used for the headline break-even.
#
# With n ~ Geometric on {0,1,2,...}, P(n=j) = alpha*(1-alpha)^j:
#
#     E[n]        = (1-alpha)/alpha
#     E[rho^n]    = alpha / (1 - (1-alpha)*rho)
#
# so for an offset c (the number of transfers a case pays before entering the
# geometric chain):
#
#     E[Tax(c+n)] = h*(c + E[n])
#                   + kappa*( (c + E[n]) - (rho/(1-rho))*(1 - rho^c * E[rho^n]) )
# ---------------------------------------------------------------------------

def expected_tax(alpha: float, p: CaseParams, offset: float = 0.0) -> float:
    """E[Tax(offset + n)] in closed form, with n ~ Geometric(alpha) on {0,1,...}.

    offset = 0 : the transfer-first design, where a case is routed and re-routed
                 until it lands somewhere that can resolve it.
    offset = 1 : the owner-first design, where a case that the owner cannot
                 resolve pays one escalation and then enters the same chain.
    """
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    if alpha * p.rho >= 1.0 and math.isclose(alpha, 1.0):
        pass  # alpha == 1 handled naturally below

    e_n = (1.0 - alpha) / alpha

    if math.isclose(p.rho, 1.0):
        # Lossless handoffs: the tax is purely n*h and is linear, so the
        # plug-in and the exact expectation coincide.
        return p.h * (offset + e_n)

    e_rho_n = alpha / (1.0 - (1.0 - alpha) * p.rho)
    surviving = (p.rho ** offset) * e_rho_n
    return (
        p.h * (offset + e_n)
        + p.kappa * ((offset + e_n) - (p.rho / (1.0 - p.rho)) * (1.0 - surviving))
    )


def expected_tax_mc(alpha: float, p: CaseParams, offset: float = 0.0,
                    terms: int = 4000) -> float:
    """Brute-force check on expected_tax: sum the series term by term."""
    total = 0.0
    for j in range(terms):
        total += alpha * (1.0 - alpha) ** j * transfer_tax(offset + j, p)
    return total


def breakeven_fcr_exact(m: int, a: float, p: CaseParams) -> float:
    """Break-even FCR using exact expectations rather than the plug-in.

    Owner-first wins when (1 - p_eff) * E[Tax(1+n)] < E[Tax(n)], so

        p_eff*  =  1 - E[Tax(n)] / E[Tax(1+n)]

    THE IDENTITY
    ------------
    This evaluates to exactly alpha. Not approximately - exactly, and for any
    cost function whatsoever with Tax(0) = 0.

    Proof. Condition on the first routing attempt. With probability alpha it
    resolves, so n = 0 and the case pays Tax(0) = 0. With probability (1-alpha)
    it does not, the case has now been transferred once, and by memorylessness
    the remaining transfer count is again Geometric(alpha). Hence

        E[Tax(n)] = alpha*Tax(0) + (1-alpha)*E[Tax(1+n)]
                  = (1-alpha)*E[Tax(1+n)]

    and therefore

        p*  =  1 - E[Tax(n)]/E[Tax(1+n)]  =  1 - (1-alpha)  =  alpha.     QED

    Nothing about h, kappa or rho survives into the answer. Nor does the
    functional form of the tax: the same result holds for elapsed time, for
    cost in dollars, for customer effort, for any per-case penalty that is zero
    when the case never moves.

    WHAT IT MEANS
    -------------
    Both designs face an identical downstream chain. The only thing that
    differs between them is what happens at the first touch. So the entire
    comparison collapses to a single question:

        Is your single owner better at resolving a case at first contact than
        your routing model is at picking the right destination at first
        attempt?

    That is the whole thing. If your generalist resolves more cases on first
    contact than your router routes correctly on first attempt, owning beats
    routing - regardless of how expensive your handoffs are.

    The handoff parameters do not set the bar. They set how much you win or
    lose by, which is what `savings_fraction` is for.
    """
    alpha = routing_accuracy(m, a)
    if math.isclose(alpha, 1.0):
        return 0.0
    denom = expected_tax(alpha, p, offset=1.0)
    if denom <= 0:
        return 0.0
    return 1.0 - expected_tax(alpha, p, offset=0.0) / denom


def breakeven_gamma_exact(p_g: float, p_s: float, m: int, a: float,
                          p: CaseParams) -> float:
    """Minimum AI augmentation yield, using exact expectations."""
    target = breakeven_fcr_exact(m, a, p)
    if p_g >= target:
        return 0.0
    if math.isclose(p_s, p_g):
        return float("inf")
    return (target - p_g) / (p_s - p_g)


# ---------------------------------------------------------------------------
# The identity in its general form
#
# The geometric derivation above is a special case of something weaker and more
# robust. Stating it generally matters, because memorylessness is the first
# thing a reviewer attacks - and it turns out the identity never needed it.
#
# THEOREM (common continuation)
# -----------------------------
# Let alpha be the probability that the FIRST team to touch a case resolves it
# under the transfer-first design, and p the same probability under a single
# owner. Let C be the expected penalty borne by a case that fails at its first
# touch and enters the escalation chain, including the cost of that first move.
#
# If C is the same for both designs, then both have exactly two outcomes:
#
#     transfer-first : pays 0 with probability alpha, else pays C
#     owner-first    : pays 0 with probability p,     else pays C
#
# so expected penalties are (1-alpha)*C and (1-p)*C, and
#
#     owner-first is cheaper  <=>  (1-p)*C < (1-alpha)*C  <=>  p > alpha
#
# C cancels. The chain may have routing accuracy that degrades with depth,
# path dependence, absorbing states, correlated difficulty, any cost function
# at all. None of h, kappa, rho or W appears in the answer.
#
# WHAT THIS IS NOT
# ----------------
# This is not distribution-free cancellation. It is cancellation under a common
# continuation, which is an economic assumption and not a free lunch. Stating it
# any more strongly would be wrong. The assumption fails in both directions:
#
#   AGAINST owner-first (adverse selection). Cases that defeat a competent
#   owner are genuinely hard. Cases that a router misdirects are mostly average
#   cases sent to the wrong place. If owner-first failures are systematically
#   harder, C_owner > C_transfer and the true break-even sits ABOVE alpha.
#
#   FOR owner-first (context and labelling). An escalated case arrives carrying
#   the owner's diagnostic work and a named, reasoned referral, rather than a
#   bounce from a team that only knows the case is not theirs. Higher effective
#   rho and a better-aimed next hop mean C_owner < C_transfer and the true
#   break-even sits BELOW alpha.
#
# Both effects are real, they pull opposite ways, and neither is modelled here.
# alpha is the break-even under the neutral assumption that they cancel. An
# organisation that believes its escalations are badly selected should treat
# alpha as a floor; one that believes its owners hand over well should treat it
# as a ceiling.
#
# ALPHA MEANS FIRST-TOUCH RESOLUTION, NOT ROUTING ACCURACY
# --------------------------------------------------------
# The theorem is about the probability the first toucher FINISHES the case, not
# the probability the router picks the right queue. They differ: right queue and
# still bounced is common; wrong queue and resolved anyway happens too. Use the
# measurable quantity - the fraction of cases resolved by the team they were
# first assigned to, with no reassignment. See `routing_accuracy` for why that
# number falls as an organisation fragments, but do not substitute one for the
# other.
# ---------------------------------------------------------------------------

def chain_cost(alphas: "list[float]", p: CaseParams,
               max_transfers: int = 500, elapsed: bool = False) -> float:
    """C: expected penalty of a case that has failed its first touch.

    `alphas[k]` is the probability that the (k+1)-th routing attempt in the
    escalation chain resolves the case. The list may be any non-empty sequence;
    the last value is held for all deeper positions, so a degrading chain such
    as [0.5, 0.4, 0.32, 0.28, 0.25] is expressed directly.

    Deliberately does NOT assume a geometric distribution.
    """
    if not alphas:
        raise ValueError("alphas must be non-empty")
    if any(not 0.0 < x <= 1.0 for x in alphas):
        raise ValueError("every alpha must be in (0, 1]")

    def alpha_at(k: int) -> float:
        return alphas[min(k, len(alphas) - 1)]

    cost = (lambda n: transfer_tax(n, p) + p.q * n) if elapsed else (
        lambda n: transfer_tax(n, p))

    total = 0.0
    survive = 1.0  # P(still unresolved on arrival at chain position j)
    for j in range(1, max_transfers + 1):
        a_j = alpha_at(j)
        total += survive * a_j * cost(j)
        survive *= (1.0 - a_j)
        if survive < 1e-15:
            break
    return total


def design_cost(first_touch_success: float, alphas: "list[float]",
                p: CaseParams, elapsed: bool = False) -> float:
    """Expected penalty of a design whose first toucher succeeds with the
    given probability, where failures enter the common chain `alphas`."""
    return (1.0 - first_touch_success) * chain_cost(alphas, p, elapsed=elapsed)


def breakeven_general(alphas: "list[float]") -> float:
    """The break-even first-touch success rate: alphas[0], always.

    Provided only so the claim is executable rather than merely asserted. The
    test suite verifies that `design_cost` actually crosses over here, for
    arbitrary degrading chains and for both the labour and elapsed cost
    functions.
    """
    if not alphas:
        raise ValueError("alphas must be non-empty")
    return alphas[0]


def breakeven_with_owner_overhead(alpha: float, delta: float,
                                  p: CaseParams) -> float:
    """The break-even when a generalist owner needs delta EXTRA minutes per case.

    The clean identity assumes the productive work W is the same whoever does
    it. That is the single most generous assumption in the whole model, and it
    is not true: a specialist who has seen a failure forty times needs less time
    than a generalist reasoning from first principles.

    Suppose owner-first adds delta expected productive minutes to every case.
    Owner-first now costs W + delta + (1-p)*C against transfer-first's W + (1-a)*C,
    so it wins when

        delta + (1-p)*C  <  (1-alpha)*C
        p*  =  alpha + delta/C

    where C = E[Tax(1+n)] is the chain cost. The penalty is linear in delta and
    inversely proportional to how expensive your handoffs are: the worse your
    chain, the more generalist inefficiency you can absorb.

    At the base parameters (alpha = 37.6%, C = 47.2 min), every extra 5 minutes
    of generalist time raises the bar by about 10.6 points. Twenty extra minutes
    puts the bar at 80% and the argument is in serious trouble. This is the
    sensitivity that most deserves to be run against real data.
    """
    if delta < 0:
        raise ValueError("delta must be non-negative")
    chain = expected_tax(alpha, p, offset=1.0)
    if chain <= 0:
        return alpha
    return min(1.0, alpha + delta / chain)


def owner_model_cost_exact(p_g_eff: float, m: int, a: float, p: CaseParams) -> float:
    """Expected labour minutes under owner-first, using exact expectations."""
    alpha = routing_accuracy(m, a)
    return p.W + (1.0 - p_g_eff) * expected_tax(alpha, p, offset=1.0)


def transfer_model_cost_exact(m: int, a: float, p: CaseParams) -> float:
    """Expected labour minutes under transfer-first, using exact expectations."""
    alpha = routing_accuracy(m, a)
    return p.W + expected_tax(alpha, p, offset=0.0)


# ---------------------------------------------------------------------------
# The comparison that matters: transfer-first vs owner-first
# ---------------------------------------------------------------------------

def generalist_fcr(p_g: float, p_s: float, gamma: float) -> float:
    """First-contact resolution of an AI-augmented generalist.

    p_g   : unaided generalist FCR.
    p_s   : FCR of the correct specialist, i.e. the ceiling.
    gamma : augmentation yield - the fraction of the generalist's knowledge
            gap (p_s - p_g) that agentic AI closes. gamma = 0 is an unaided
            human; gamma = 1 is a human with a specialist permanently at their
            shoulder and no queue between them.
    """
    if not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma must be in [0, 1]")
    if p_s < p_g:
        raise ValueError("p_s must be >= p_g")
    return p_g + gamma * (p_s - p_g)


def owner_model_cost(p_g_eff: float, m: int, a: float, p: CaseParams) -> float:
    """Expected cost when one generalist owns the case end to end.

    With probability p_g_eff the case never moves and costs exactly W. With
    probability (1 - p_g_eff) it must escalate, and once escalated it enters
    the same specialist chain as everyone else - so it pays for the escalation
    hop plus the expected onward transfers, Tax(1 + E[n]).

    This is deliberately pessimistic toward the generalist model: it charges
    the residual cases the full chain cost with no credit for the context the
    owner has already built and retains.
    """
    n_chain = 1.0 + expected_transfers(m, a)
    return p.W + (1.0 - p_g_eff) * transfer_tax(n_chain, p)


def breakeven_fcr(m: int, a: float, p: CaseParams) -> float:
    """Minimum FCR at which owner-first beats transfer-first.

    Owner-first wins when

        (1 - p_g_eff) * Tax(1 + E[n])  <  Tax(E[n])

    so the threshold is

        p_g_eff*  =  1 - Tax(E[n]) / Tax(1 + E[n])

    The result is usually far below the specialist's FCR, which is the
    counter-intuitive heart of the argument: the single owner does not have to
    be as good as the specialist. They only have to be good enough that the
    transfers they avoid outweigh the ones they cause.
    """
    n = expected_transfers(m, a)
    tax_chain = transfer_tax(1.0 + n, p)
    if tax_chain <= 0:
        return 0.0
    return 1.0 - transfer_tax(n, p) / tax_chain


def breakeven_gamma(p_g: float, p_s: float, m: int, a: float, p: CaseParams) -> float:
    """Minimum AI augmentation yield for the single-touchpoint model to win.

    Returns 0.0 if an unaided generalist already clears the bar, and a value
    greater than 1.0 (i.e. unreachable) if no amount of augmentation suffices
    under these parameters.
    """
    target = breakeven_fcr(m, a, p)
    if p_g >= target:
        return 0.0
    if math.isclose(p_s, p_g):
        return float("inf")
    return (target - p_g) / (p_s - p_g)


# ---------------------------------------------------------------------------
# Breaking even is not a reason to reorganise. Magnitude is.
# ---------------------------------------------------------------------------

def elapsed_tax(alpha: float, p: CaseParams, offset: float = 0.0) -> float:
    """E[Tax(offset+n)] + q*E[offset+n]: the customer-visible penalty.

    Requeue delay q costs the customer rather than the P&L, which is exactly
    why it is under-managed. It is also, in most organisations, by far the
    largest term.
    """
    e_n = (1.0 - alpha) / alpha
    return expected_tax(alpha, p, offset) + p.q * (offset + e_n)


def savings_fraction(p_eff: float, m: int, a: float, ps: CaseParams,
                     elapsed: bool = False) -> float:
    """Fractional reduction in cost per case from owner-first vs transfer-first.

    Positive means owner-first is cheaper. Zero at p_eff == alpha, by the
    identity in breakeven_fcr_exact.

    Set elapsed=True for the customer-visible version, which includes requeue
    delay and is always the larger number.
    """
    alpha = routing_accuracy(m, a)
    tax = elapsed_tax if elapsed else (lambda al, q, o: expected_tax(al, q, o))
    t_transfer = tax(alpha, ps, 0.0)
    t_owner = (1.0 - p_eff) * tax(alpha, ps, 1.0)
    c_transfer = ps.W + t_transfer
    c_owner = ps.W + t_owner
    return (c_transfer - c_owner) / c_transfer


def fcr_for_target_saving(target: float, m: int, a: float, ps: CaseParams,
                          elapsed: bool = False) -> float:
    """The owner FCR needed to deliver a given fractional saving.

    Solving  (C_transfer - C_owner)/C_transfer = target  for p_eff:

        p_eff = 1 - (C_transfer*(1-target) - W) / E[Tax(1+n)]
    """
    alpha = routing_accuracy(m, a)
    tax = elapsed_tax if elapsed else (lambda al, q, o: expected_tax(al, q, o))
    c_transfer = ps.W + tax(alpha, ps, 0.0)
    t_owner_full = tax(alpha, ps, 1.0)
    if t_owner_full <= 0:
        return 0.0
    return 1.0 - (c_transfer * (1.0 - target) - ps.W) / t_owner_full


def gamma_for_target_saving(target: float, p_g: float, p_s: float, m: int,
                            a: float, ps: CaseParams,
                            elapsed: bool = False) -> float:
    """AI augmentation yield required to hit a given saving target.

    This is the number that actually matters for a business case. The
    break-even is where you stop losing money; this is where you start making
    enough of it to justify reorganising a support business.
    """
    needed = fcr_for_target_saving(target, m, a, ps, elapsed)
    if p_g >= needed:
        return 0.0
    if math.isclose(p_s, p_g):
        return float("inf")
    return (needed - p_g) / (p_s - p_g)
