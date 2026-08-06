# The Transfer Tax

### Three transfers more than double the cost of a case. And the bar a single owner has to clear turns out to be one number you already measure.

---

Six days. Four owners. Twenty minutes of actual work.

A customer opens a case on a Tuesday morning. Front line works it for forty
minutes, decides it is a networking problem, and routes it. Networking picks it
up on Wednesday, spends an hour, and establishes it is not networking — it is
authentication. Identity gets it Thursday and narrows it to a certificate chain,
which belongs to the platform team. Platform resolves it in twenty minutes on
Monday afternoon.

That is the whole case. Now look at how it appeared in the operational review.
Four teams each recorded reasonable handle time. Every routing decision, taken
with the information available at the time, was defensible. Nobody missed an SLA
that belonged to them. **Every dashboard was green.**

The customer experienced six days of re-explaining their problem to strangers.

I have spent most of my career in and around large support organisations, and I
have come to believe the transfer is the most under-priced transaction in the
business. Not the most visible failure — the most under-priced. We measure handle
time, resolution time, backlog and utilisation with real rigour, and move cases
between teams thousands of times a day while measuring almost nothing about what
that movement costs.

So I tried to price it. What follows collapses, in the end, into one number most
of you already have in a report, and a bar lower than you would guess. The model,
the code and the bibliography are in a public repository, linked at the end — I
would rather you argued with the maths than took my word for it.

---

## The pin factory has a lot to answer for

Nearly every support organisation descends from a single 1776 paragraph. Adam
Smith watched ten men make pins. Working separately, he wrote, they "certainly
could not each of them have made twenty, perhaps not one" in a day. Divided into
about eighteen operations, those same ten men produced upwards of forty-eight
thousand a day. Around four thousand eight hundred each.

Specialisation works — it is why we have tier one and tier two, product queues,
escalation teams, and routing taxonomies that in most large organisations have
grown past a hundred destinations.

But notice what Smith's pin never did. It carried no context, so nothing was lost
when it moved between stations, and it did not become a worse pin for being handled
eighteen times. A support case is not a pin — it is *mostly* context. The moment the
thing moving down your line is made of information rather than brass, every handoff
becomes a lossy transmission — Coase's insight turned inward: a transaction you
package, transmit, verify and re-establish, and never book anywhere.

---

## Medicine actually measured this

Support operations has no randomised trials. Medicine has spent two decades on
exactly this problem, because in a hospital a bad handoff kills people.

The study I find hardest to argue with is Starmer and colleagues in the *New
England Journal of Medicine*, 2014: nine hospitals, 10,740 admissions, a
prospective before-and-after evaluation of a structured handoff bundle — a
mnemonic, a written template, training, a change to verbal practice. Not a
randomised trial, and not uniform: six of the nine sites showed significant
reductions on their own. But across the cohort, medical errors fell 23% and
preventable adverse events fell 30%.

Here is the line that convinced me it is signal, not noise: **non-preventable
adverse events did not move at all** — 3.0 per hundred admissions before, 2.8
after, p=0.79. Whatever else moved alongside the bundle, it touched precisely the
harm communication can touch and left the rest where it was.

Those doctors were excellent clinicians losing information at a boundary. So are
your engineers. The difference is that the hospital measured it.

---

## Pricing the handoff

The productive work a case needs — diagnosis, fix, verification — is
substantially a property of the case. Call it W. Everything your organisation adds
to move that case between people is overhead.

Each transfer costs three things: the handoff itself, h (summary, disposition,
routing form); requeue delay, q, while the case waits in the next queue; and
re-discovery — the new owner rebuilding what the last one knew, the term nobody
budgets for.

Suppose each handoff carries a fraction ρ of what the previous owner knew. After i
handoffs the surviving context is ρⁱ, and the cost of rebuilding what was lost is
proportional to that loss. Summing over n transfers gives a closed form:

> **Tax(n) = n·h + κ·( n − ρ(1−ρⁿ)/(1−ρ) )**, where κ is the cost of rebuilding a
> case from nothing.

Labour is W + Tax(n); elapsed time, the version the customer feels, adds n·q. The
n-th transfer costs h + κ(1−ρⁿ) — always positive, transfers always cost — and
each costs more than the one before, by κ·ρⁿ·(1−ρ): **the tax is convex.**

Run it with plausible numbers — 45 minutes of real work, a six-minute handoff, a
25-minute cold pickup, 75% context retention, four hours of requeue delay:

| Transfers | Context surviving | Labour | Elapsed |
|---|---|---|---|
| 0 | 100% | 45 min | 45 min |
| 1 | 75% | 57 min (1.3×) | 5 hours |
| 2 | 56% | 74 min (1.6×) | 9 hours |
| **3** | **42%** | **95 min (2.1×)** | **14 hours (18×)** |
| 4 | 32% | 118 min (2.6×) | 18 hours |

Three transfers more than double labour and multiply elapsed time eighteenfold.
Successive transfers cost 12.3, 16.9, 20.5 then 23.1 minutes, climbing toward an
asymptote of 31 — where a handoff transmits nothing and the case is simply
restarted.

One caution, because it changes the *size* of the number, not its direction: the
convex shape is an assumption, not a theorem. It holds if rebuilt context does not
re-enter the written record, so losses compound against the original. If every
receiver instead fully restores the case and hands on a complete summary, the tax
is *linear* — three transfers cost 1.82× rather than 2.10×. Which end you resemble
is empirical: whether your engineers write up what they learned or just resolve and
move on. The headline uses the convex form; the repository computes both.

---

## Specialisation manufactures its own transfers

Where does n come from? Mostly from us. Adding a specialist queue adds no
information at intake. A toy model: if a is the fraction of cases whose
destination is unambiguous on arrival, and the rest are spread across m queues,
first-touch success is roughly a + (1−a)/m. With 35% unambiguous, ten queues gives
about 41%; twenty-five gives about 38%.

Treat that as illustration — the real curve almost certainly falls faster, because
finer fragmentation reduces the share of unambiguous cases. What matters is the
loop: transfers get blamed on a skill gap; the fix for a skill gap is a more
specialised queue; that lowers first-touch resolution; which produces more
transfers. I have never once seen a support taxonomy get smaller.

---

## The second tax, which nobody books at all

There is a further cost, and this one is a theorem. Queueing theory's pooling
principle: for a fixed arrival and service rate, one pooled queue of c servers
strictly outperforms m separate queues of c/m servers at identical utilisation.
Halfin and Whitt's 1981 square-root staffing result gives the magnitude — safety
capacity scales with the square root of the number of fragments.

Crucially, this assumes **perfect routing** — it is not a misrouting penalty, but
purely the price of forbidding an idle agent from helping a waiting customer
labelled as somebody else's problem.

Take 120 agents and 100 Erlangs of demand. Hold headcount and utilisation
identical at 83.3% and change only where you draw the lines:

| Organisation | Agents per pool | Average wait |
|---|---|---|
| One pool | 120 | 0.05 min |
| Two pools | 60 | 0.35 min (7×) |
| Five pools | 24 | 2.2 min (45×) |
| Ten pools | 12 | 6.7 min (135×) |

Same people, same work, same utilisation — a hundred and thirty-five times the
wait, manufactured entirely by organisational boundaries. Put the other way: to
hold a fixed service level, ten specialist pools need 22.6% more headcount than one
pooled team, twenty-five pools 65% more.

One caveat, so you do not double-count. This waiting and the requeue delay q are
the same phenomenon — fragmentation-induced waiting — seen twice. The **staffing**
cost of fragmentation is genuinely additive to the case-level tax; the **waiting
time** is not. Do not add the pooling wait to the elapsed figures above and call
it two taxes.

---

## Somebody already tried this

In 2018 T-Mobile US dismantled the routing model. No IVR menus, no cold transfers:
every customer assigned to a dedicated *team* — "Team of Experts" — accountable for
a fixed book of accounts, co-located, with authority to finish the job. Matthew
Dixon documented it in *Harvard Business Review* that year. The period that
followed looked good — postpaid churn of 0.97% in Q3 2018, from the earnings
releases rather than a consultant's deck, and sharply lower attrition. But a
competitive carrier changes many things at once; I cannot attribute those numbers
to the operating model with any rigour, and offer them only as association. The
more dramatic figures that circulate I could not source; they sit in the repository
under claims I rejected.

A second example, from another industry, is Buurtzorg, the Dutch neighbourhood
nursing organisation founded by Jos de Blok in 2006: self-managing *teams* of ten
to twelve generalist nurses, each owning fifty to sixty patients end to end, no
specialisation layer, no handoffs. An Ernst & Young study in 2009 found it used
roughly 40% fewer care hours per client than conventional providers. Honesty
requires the other half: KPMG in 2015 confirmed Buurtzorg was genuinely low-cost,
and not because of an easier patient mix — but found that once hospital and
nursing-home costs were included, total per-patient cost sat around the Dutch
average. The generalist model was not free money; it was dramatically cheaper at
the layer where the handoffs used to be.

Neither is a controlled experiment, and both are survivorship-selected. What they
show is not that a lone generalist beats a specialist, but that stable, end-to-end
ownership by a small accountable unit can beat a chain of handoffs.

---

## The bar is exactly one number, and it is not the specialist's

Here is the question I wanted the model to answer: **how good does a single owner
have to be before owning the case end to end beats routing it?** It collapses into
three lines.

Under transfer-first, the first team to touch the case either finishes it — paying
no tax — or it enters the escalation chain. Under owner-first, the owner either
resolves it at first contact — paying no tax — or it enters *the same chain*.

Call the expected cost of that chain C. It does not matter what C is: it can fold
in routing accuracy that degrades with depth, correlated difficulty, any cost
function you like. Both designs pay zero on a first-touch success and C on a
first-touch failure. So transfer-first costs (1−α)·C, owner-first costs (1−p)·C,
and C cancels:

> **p\* = α**

where **α is your existing first-touch resolution rate** — the fraction of cases
finished by the team they were first assigned to, with no reassignment — and p is
the single owner's. In words, and this is the whole article:

**A single owner beats the routing model precisely when they resolve more cases at
first contact than your current front line already does.**

Two honest caveats. First, α is *first-touch resolution*, not routing accuracy — a
case can land in exactly the right queue and still be bounced. The measurable
quantity is the one that matters, and you can pull it this week. Second, C
cancelling assumes the chain is the same for both designs. It fails both ways:
cases that defeat a competent owner are genuinely hard (adverse selection pushes
break-even *above* α), while an owner's escalation carries real diagnostic work and
a reasoned referral rather than a bounce (pushing it *below*). I have modelled
neither; treat α as the neutral estimate.

The bar is set by your intake, not your specialists — and since first-touch
resolution falls as an organisation fragments, **the more specialist queues you run,
the lower the bar your generalist has to clear.** It is why T-Mobile and Buurtzorg
worked with no AI at all: they were not beating specialists, they were beating
intake.

---

## But breaking even is not a reason to reorganise

No executive restructures to break even; the question is magnitude. Here the
handoff parameters return — they set how much you win by, not whether. Working an
illustrative organisation whose measured α is around 38%:

| Owner's first-contact resolution | Labour saving | Elapsed-time saving |
|---|---|---|
| α (break-even) | 0% | 0% |
| 55% | 11% | 25% |
| 65% | 17% | 40% |
| 70% | 21% | 47% |
| 80% | 27% | 62% |

Note the ratio. **The customer-visible saving runs at roughly 2.3 times the cost
saving**, because requeue delay dominates elapsed time and is charged entirely to
the customer. For a serious result — a fifth off labour, nearly half off cycle
time — the owner needs to resolve about 70% of cases at first contact: well above
break-even, and above what an unaided generalist manages in a deep technical
domain. Precisely the gap that changed.

---

## What agentic AI actually changes, and what it does not

Getting an owner from something like 38% to ~70% is a big move — and, until
recently, an impossible one. The generalist model always had one fatal problem,
and it was epistemic: the specialist genuinely knows more, and depth was scarce,
slow to build, and could not be in two places at once. So we accepted the transfer
tax, because the alternative — a generalist who simply could not solve the hard
case — was worse. That is the constraint that just changed.

The best field evidence is Brynjolfsson, Li and Raymond, who studied 5,172 support
agents through a staggered rollout of a generative AI assistant (NBER; *Quarterly
Journal of Economics*). Average productivity rose 14–15% — but I will use that study
for its shape, not its number. It measured **issues resolved per hour**: throughput,
driven mostly by faster handling and higher concurrency, with only a small rise in
successful resolution. My model needs a change in the **probability of resolving a
case at first contact** — capability — and a 15% throughput gain is not a 15%
capability gain. What the study does establish is direction and distribution: the
gains concentrated among **less experienced and lower-skilled workers**, who
improved in both speed and quality, while the most experienced saw small *declines*
in quality. AI did not make specialists better; it made non-specialists behave more
like specialists — gap compression, the exact thing the single-owner model was
always missing.

And those were suggestion engines. An agent retrieves from the knowledge estate,
reads the telemetry, runs the diagnostic, drafts the change and checks the result
— depth at the moment of need without the case moving anywhere. State that
precisely, because the tempting overstatement is wrong: the case does not change
hands, so the transfer count is zero — no requeue, no human re-discovery — but zero
transfers is not lossless. Agentic systems truncate context, retrieve wrong
evidence, and fail at tool boundaries; that loss is real and, today, unmeasured.
Agentic AI drives *n* toward zero; it does not make ρ equal to one. Whether these
systems actually move a generalist from 38% to 70% is a bet — but on a mechanism we
have measured working in the right direction, on exactly the right people.

---

## What the model implies, and where it breaks

One human owns the customer's problem from first contact to resolution and does not
let go. Behind them sits an agentic bench supplying depth on demand — not the equal
of every specialist, but enough to lift first-contact resolution on the cases that
used to require a handoff, without a specialist's queueing behaviour. Human
specialists remain — as *consultants to the owner*, not destinations. They advise;
they do not receive.

Accountability cannot move, or the taxonomy regrows. The owner needs real authority
to spend, credit and escalate, because an owner who must ask permission is a router
with better branding. And you must measure transfers per case, which almost nobody
does.

The honest objections stand, and the first can sink the savings. My model treats W
as a property of the case. It is not, entirely: a specialist who has seen a failure
forty times needs less time than a generalist reasoning from scratch. If the owner
needs δ extra productive minutes on the average case, break-even is no longer α but
**p\* = α + δ/C**, where C is the escalation-chain cost, about 47 minutes at the
base parameters:

| Extra generalist minutes per case (δ) | Break-even first-contact resolution |
|---|---|
| 0 | 37.6% |
| 5 | 48.2% |
| 10 | 58.8% |
| 20 | 80.0% |

At ten extra minutes the owner must clear 59%; at twenty, the bar is 80% and the
argument is in trouble. The identity p\* = α survives — it never depended on W — but
only where the owner is as fast as the specialist on the work itself. Treat the
savings as an upper bound; δ is the number I would measure before betting a
reorganisation on any of this.

Second, some cases genuinely require a named human expert, and regulated or
safety-critical work may require a formal, documented handoff. The model does not
say never transfer — it says stop transferring by default, and price it when you do.

---

## The number I would change on Monday

Every support organisation I know can tell you its average handle time to the
second. Very few can tell you the average number of times a case changes hands.
That second number is where your cost, your cycle time and your customer effort
are hiding — and, I suspect though cannot prove, a fair amount of your attrition
too. It has been hiding there since 1776, protected by a genuinely brilliant idea
about pins.

I am not going to tell you that generalists are the most efficient support model;
the honest version is narrower and stronger. The bar a single owner has to clear
was always lower than anyone believed — because it was never the specialist's
competence, it was your own intake — and what was missing was a way to give an
ordinary owner the depth to clear it by a margin worth having. That is what
changed.

So: keep stable ownership of the customer's problem. Use specialists as consultants
rather than destinations wherever the work allows. And measure — actually measure —
whether AI is reducing your transfers without quietly degrading resolution quality.
None of those three requires you to believe my savings table; they require you to
believe a handoff costs something, and to start pricing it.

The model, the proof, the sensitivity analysis and the full bibliography —
including the widely-repeated statistics in this field that did not survive
fact-checking, one of which I had intended to build this article around — are here:

**github.com/akumarau/transfer-tax**

The defaults are illustrative. Yours are not. Three numbers you can measure this
quarter and probably do not: how much context survives a handoff, how long a cold
pickup takes to become productive, and what fraction of your cases are resolved by
the team they were first assigned to. That third is your α — and it is, it turns
out, the only bar your people have to clear.

Put your numbers in and tell me I am wrong. That is what it is there for.

---

*Anupam Kumar leads support engineering teams. Views are his own. The
model in this article is his; the errors, once someone finds them, will be in the
commit history.*
