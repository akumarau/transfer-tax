"""
The second tax: what fragmenting a server pool costs you.

The transfer tax in `model.py` prices what happens to a *case* when it moves.
This module prices something separate and additive: what happens to the
*queue* when you split one pool of agents into many specialist pools.

This is a standard and uncontroversial result in queueing theory, usually
called the pooling principle or the resource-pooling effect. Two systems with
identical utilisation are not equally fast. A single M/M/c queue with c
servers strictly outperforms m independent M/M/(c/m) queues carrying 1/m of
the arrivals each, because in the fragmented system a server can be idle while
a customer in a different queue waits. Statistical economies of scale in
queues are real and they are large.

The asymptotic intuition comes from square-root safety staffing (the
Halfin-Whitt quality-and-efficiency-driven regime). To hold a target delay
probability at offered load R Erlangs you need roughly

    c  =  R + beta * sqrt(R)

servers. The beta*sqrt(R) term is pure insurance against randomness. Split the
same demand into m pools of R/m each and you must buy that insurance m times
over, on a smaller base each time:

    c_split  =  m * ( R/m + beta*sqrt(R/m) )  =  R + beta*sqrt(R)*sqrt(m)

The productive term R is unchanged. The insurance term grows with sqrt(m).
Fragmentation does not make the work bigger; it makes the buffer against
variability bigger, and you pay for that buffer in headcount forever.

Everything below computes the exact Erlang C result rather than relying on the
asymptotic, so the numbers are reproducible and not hand-waved.

Author: Anupam Kumar
License: MIT
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def erlang_b(c: int, load: float) -> float:
    """Erlang B blocking probability, computed by the numerically stable
    recurrence B(0, R) = 1, B(k, R) = R*B(k-1,R) / (k + R*B(k-1,R)).

    Used as an intermediate for Erlang C. The recurrence avoids the factorial
    overflow that kills the textbook formula at realistic call-centre sizes.
    """
    if c < 0:
        raise ValueError("c must be non-negative")
    inv_b = 1.0
    for k in range(1, c + 1):
        inv_b = 1.0 + inv_b * k / load
    return 1.0 / inv_b


def erlang_c(c: int, load: float) -> float:
    """Probability an arriving customer has to wait (Erlang C), for c servers
    and offered load `load` in Erlangs.

    Returns 1.0 when the system is unstable (load >= c), since in that regime
    every arrival waits and the queue grows without bound.
    """
    if load <= 0:
        return 0.0
    if c <= load:
        return 1.0
    b = erlang_b(c, load)
    rho = load / c
    return b / (1.0 - rho + rho * b)


def mean_wait(c: int, load: float, aht_minutes: float) -> float:
    """Expected waiting time in queue, E[Wq], in minutes.

    E[Wq] = C(c, R) * AHT / (c - R)
    """
    if c <= load:
        return float("inf")
    return erlang_c(c, load) * aht_minutes / (c - load)


def service_level(c: int, load: float, aht_minutes: float, target_minutes: float) -> float:
    """Fraction of contacts answered within `target_minutes`.

    SL = 1 - C(c,R) * exp( -(c - R) * target / AHT )
    """
    if c <= load:
        return 0.0
    exponent = -(c - load) * target_minutes / aht_minutes
    return 1.0 - erlang_c(c, load) * math.exp(exponent)


def agents_for_service_level(
    load: float, aht_minutes: float, target_minutes: float, target_sl: float
) -> int:
    """Smallest integer agent count meeting the service level target."""
    c = max(1, math.ceil(load) )
    while service_level(c, load, aht_minutes, target_minutes) < target_sl:
        c += 1
        if c > 100000:
            raise RuntimeError("no feasible staffing found")
    return c


@dataclass(frozen=True)
class PoolingResult:
    m: int
    load_total: float
    agents_pooled: int
    agents_fragmented: int
    extra_agents: int
    extra_pct: float
    wait_pooled: float
    wait_fragmented: float
    wait_ratio: float


def compare_pooling(
    load: float,
    m: int,
    aht_minutes: float = 30.0,
    target_minutes: float = 5.0,
    target_sl: float = 0.80,
) -> PoolingResult:
    """Compare one pooled queue against m specialist queues at equal demand.

    Both configurations must hit the same service level target. The pooled
    configuration is staffed as a single group; the fragmented configuration
    is staffed m times independently, each carrying load/m.

    Returns the headcount penalty and the waiting-time penalty of
    fragmentation. Note that this penalty exists even when routing is
    *perfect* - it is not a mis-routing cost. It is the price of denying your
    agents the ability to help each other's customers.
    """
    if m < 1:
        raise ValueError("m must be at least 1")

    c_pooled = agents_for_service_level(load, aht_minutes, target_minutes, target_sl)
    sub_load = load / m
    c_sub = agents_for_service_level(sub_load, aht_minutes, target_minutes, target_sl)
    c_frag = c_sub * m

    w_pooled = mean_wait(c_pooled, load, aht_minutes)
    w_frag = mean_wait(c_sub, sub_load, aht_minutes)

    return PoolingResult(
        m=m,
        load_total=load,
        agents_pooled=c_pooled,
        agents_fragmented=c_frag,
        extra_agents=c_frag - c_pooled,
        extra_pct=100.0 * (c_frag - c_pooled) / c_pooled,
        wait_pooled=w_pooled,
        wait_fragmented=w_frag,
        wait_ratio=(w_frag / w_pooled) if w_pooled > 0 else float("inf"),
    )


def equal_headcount_wait_penalty(
    load: float, agents: int, m: int, aht_minutes: float = 30.0
) -> tuple[float, float]:
    """The other way to see it: hold headcount fixed, split it, measure the damage.

    Returns (wait_pooled, wait_fragmented) in minutes for the same total number
    of agents and the same total demand. Any difference is created purely by
    the organisational boundary between the queues.
    """
    if agents % m != 0:
        raise ValueError("agents must divide evenly into m pools for a clean comparison")
    w_pooled = mean_wait(agents, load, aht_minutes)
    w_frag = mean_wait(agents // m, load / m, aht_minutes)
    return w_pooled, w_frag


def sqrt_staffing_prediction(load: float, m: int, beta: float = 1.0) -> dict:
    """Asymptotic square-root-staffing view, for comparison with the exact result.

    c_pooled     ~ R + beta*sqrt(R)
    c_fragmented ~ R + beta*sqrt(R)*sqrt(m)

    so the excess safety staffing grows as sqrt(m) - 1.
    """
    safety_pooled = beta * math.sqrt(load)
    safety_frag = beta * math.sqrt(load) * math.sqrt(m)
    return {
        "c_pooled": load + safety_pooled,
        "c_fragmented": load + safety_frag,
        "extra_agents": safety_frag - safety_pooled,
        "safety_multiple": math.sqrt(m),
    }
