# The Transfer Tax

### Three transfers more than double the cost of a case. And the bar a single owner has to clear turns out to be one number you already measure.

> Published on LinkedIn:
> **https://www.linkedin.com/pulse/transfer-tax-anupam-kumar-girne/**
>
> This is the source text. The model, proof and sensitivity analysis behind
> every figure are in [README.md](README.md), and every source is in
> [RESEARCH.md](RESEARCH.md).

---

Six days. Four owners. Twenty minutes of actual work.

A customer opens a case on a Tuesday morning. Front line works it for forty
minutes. They decide it is a networking problem and route it. Networking picks
it up on Wednesday and spends an hour on it. They establish it is not
networking. It is authentication. Identity gets it on Thursday and narrows it to
a certificate chain. That belongs to the platform team. Platform resolves it in
twenty minutes on Monday afternoon.

That is the whole case. Now look at how it appeared in the operational review.
Four teams each recorded reasonable handle time. Every routing decision was
defensible, given what was known at the time. Nobody missed an SLA that belonged
to them. **Every dashboard was green.**

The customer spent six days explaining their problem to strangers.

I have spent most of my career in and around large support organisations. I have
come to believe the transfer is the most underpriced transaction in the
business. Not the most visible failure. The most underpriced. We measure handle
time, resolution time, backlog and utilisation with real rigour. We also move
cases between teams thousands of times a day. We measure almost nothing about
what that movement costs.

So I tried to price it. What follows collapses into one number. Most of you
already have it in a report. It sets a bar that is lower than you would guess.
The model, the code and the bibliography are in a public repository, linked at
the end. I would rather you argued with the maths than took my word for it.

---

## The pin factory has a lot to answer for

Nearly every support organisation descends from a single 1776 paragraph.

Adam Smith watched ten men make pins. Working separately, he wrote, they
"certainly could not each of them have made twenty, perhaps not one" in a day.
Then he divided the job into about eighteen operations. Those same ten men
produced upwards of 48,000 pins a day. Around 4,800 each.

Specialisation works. It is why we have tier one and tier two. It is why we have
product queues, escalation teams, and routing taxonomies that have grown past a
hundred destinations in most large organisations.

But notice what Smith's pin never did. It carried no context. Nothing was lost
when it moved between stations. It did not become a worse pin for being handled
eighteen times.

A support case is not a pin. A support case is mostly context. Once the thing
moving down your line is made of information rather than brass, every handoff
becomes a lossy transmission. This is Coase's insight turned inward. A handoff
is a transaction. You package it, transmit it, verify it and rebuild shared
understanding. Then you book it nowhere.

---

## Medicine actually measured this

Support operations has no randomised trials. Medicine does. It has spent two
decades on exactly this problem, because in a hospital a bad handoff kills
people.

The study I find hardest to argue with is Starmer and colleagues in the *New
England Journal of Medicine* in 2014. Nine hospitals. 10,740 admissions. They
evaluated a structured handoff bundle before and after: a mnemonic, a written
template, training, and a change to verbal practice.

It was not a randomised trial. It was not uniform either. Six of the nine sites
showed significant reductions on their own. But across the cohort, medical
errors fell 23%. Preventable adverse events fell 30%.

Here is the line that convinced me it is signal and not noise. **Adverse events
that were not preventable did not move at all.** They were 3.0 per hundred
admissions before and 2.8 after, at p=0.79. Whatever else changed alongside the
bundle, it touched precisely the harm that communication can touch. It left the
rest where it was.

Those doctors were excellent clinicians losing information at a boundary. So are
your engineers. The difference is that the hospital measured it.

---

## Pricing the handoff

The productive work a case needs is largely a property of the case. The
diagnosis, the fix, the verification. Call it W. Everything your organisation
adds in order to move that case between people is overhead.

Each transfer costs three things. There is the handoff itself, h. That is the
summary, the disposition, the routing form. There is requeue delay, q, while the
case waits in the next queue. And there is rediscovery. That is the new owner
rebuilding what the last one knew. It is the term nobody budgets for.

Suppose each handoff carries a fraction ρ of what the previous owner knew. After
i handoffs the surviving context is ρⁱ. The cost of rebuilding what was lost is
proportional to that loss. Summing over n transfers gives a closed form.

> **Tax(n) = n·h + κ·( n − ρ(1−ρⁿ)/(1−ρ) )**
>
> where κ is the cost of rebuilding a case from nothing.

Labour is W + Tax(n). Elapsed time is the version the customer feels, and it
adds n·q on top.

The nth transfer costs h + κ(1−ρⁿ). That is always positive, so transfers always
cost. And each one costs more than the one before it, by κ·ρⁿ·(1−ρ). **The tax
is convex.**

Run it with plausible numbers. Say 45 minutes of real work, a six minute
handoff, a 25 minute cold pickup, 75% context retention, and four hours of
requeue delay.

| Transfers | Context surviving | Labour | Elapsed |
|---|---|---|---|
| 0 | 100% | 45 min | 45 min |
| 1 | 75% | 57 min (1.3×) | 5 hours |
| 2 | 56% | 74 min (1.6×) | 9 hours |
| **3** | **42%** | **95 min (2.1×)** | **14 hours (18×)** |
| 4 | 32% | 118 min (2.6×) | 18 hours |

Three transfers more than double labour. They multiply elapsed time eighteenfold.
Successive transfers cost 12.3, 16.9, 20.5 then 23.1 minutes. They climb toward
an asymptote of 31. At that point a handoff transmits nothing and the case is
simply restarted.

One caution. It changes the size of the number, not its direction. The convex
shape is an assumption, not a theorem. It holds if rebuilt context never enters
the written record, so losses compound against the original. If every receiver
instead fully restores the case and hands on a complete summary, the tax is
linear. Then three transfers cost 1.82 times rather than 2.10 times. Which end
you resemble is an empirical question. It depends on whether your engineers
write up what they learned or just resolve and move on. The headline uses the
convex form. The repository computes both.

---

## Specialisation manufactures its own transfers

Where does n come from? Mostly from us.

Adding a specialist queue adds no information at intake. Here is a toy model.
Let a be the fraction of cases whose destination is obvious on arrival. Spread
the rest across m queues. Then first touch success is roughly a + (1−a)/m. With
35% obvious at intake, ten queues gives about 42%. Twenty five queues gives
about 38%.

Treat those numbers as illustrative rather than measured. The real curve almost
certainly falls faster, because finer fragmentation also reduces the share of
obvious cases.

What matters is the loop. Transfers get blamed on a skill gap. The fix for a
skill gap is a more specialised queue. That lowers first touch resolution. Which
produces more transfers.

I have never once seen a support taxonomy get smaller.

---

## The second tax, which nobody books at all

There is a further cost. This one is a theorem.

Queueing theory has a pooling principle. For a fixed arrival rate and service
rate, one pooled queue of c servers beats m separate queues of c/m servers at
identical utilisation. Halfin and Whitt's 1981 result on square root staffing
gives the magnitude. Safety capacity scales with the square root of the number
of fragments.

This assumes **perfect routing**. It is not a misrouting penalty. It is purely
the price of forbidding an idle agent from helping a waiting customer who has
been labelled as somebody else's problem.

Take 120 agents and 100 Erlangs of demand. Hold headcount fixed. Hold
utilisation fixed at 83.3%. Change only where you draw the lines.

| Organisation | Agents per pool | Average wait |
|---|---|---|
| One pool | 120 | 0.05 min |
| Two pools | 60 | 0.35 min (7×) |
| Five pools | 24 | 2.2 min (45×) |
| Ten pools | 12 | 6.7 min (135×) |

Same people. Same work. Same utilisation. A hundred and thirty five times the
wait, manufactured entirely by organisational boundaries.

Put it the other way. To hold a fixed service level, ten specialist pools need
22.6% more headcount than one pooled team. Twenty five pools need 65% more.

One caveat, so you do not double count. This waiting and the requeue delay q are
the same phenomenon seen twice. Both are waiting caused by fragmentation. The
**staffing** cost of fragmentation is genuinely additive to the case level tax.
The **waiting time** is not. Do not add the pooling wait to the elapsed figures
above and call it two taxes.

---

## Somebody already tried this

In 2018 T-Mobile US dismantled the routing model. No IVR menus. No cold
transfers. Every customer was assigned to a dedicated team, called Team of
Experts. That team was accountable for a fixed book of accounts. They sat
together. They had the authority to finish the job. Matthew Dixon documented it
in *Harvard Business Review* that year.

The period that followed looked good. Postpaid churn was 0.97% in Q3 2018, taken
from the earnings releases rather than a consultant's deck. Attrition fell
sharply. But a competitive carrier changes many things at once. I cannot
attribute those numbers to the operating model with any rigour. I offer them as
association only. The more dramatic figures that circulate about this programme
I could not source at all. They sit in the repository under claims I rejected.

A second example comes from another industry. Buurtzorg is a Dutch neighbourhood
nursing organisation, founded by Jos de Blok in 2006. It runs teams of ten to
twelve generalist nurses that manage themselves. Each team owns fifty to sixty
patients end to end. There is no specialisation layer and there are no handoffs.
An Ernst & Young study in 2009 found it used roughly 40% fewer care hours per
client than conventional providers.

Honesty requires the other half. KPMG confirmed in 2015 that Buurtzorg was
genuinely low cost, and that this was not explained by an easier patient mix.
But KPMG also found that once hospital and nursing home costs were included,
total cost per patient sat around the Dutch average. The generalist model was
not free money. It was dramatically cheaper at the layer where the handoffs used
to be.

Neither is a controlled experiment. Both were selected because they succeeded.
What they show is not that a lone generalist beats a specialist. It is that
stable ownership by a small accountable unit can beat a chain of handoffs.

---

## The bar is one number, and it is not the specialist's

Here is the question I wanted the model to answer. **How good does a single
owner have to be before owning the case end to end beats routing it?**

It collapses into three lines.

Under the routing model, the first team to touch the case either finishes it and
pays no tax, or it enters the escalation chain. Under the owner model, the owner
either resolves it at first contact and pays no tax, or it enters the same
chain.

Call the expected cost of that chain C. It does not matter what C is. It can
fold in routing accuracy that decays with depth. It can fold in correlated
difficulty, or any cost function you like. Both designs pay zero on a first
touch success. Both pay C on a first touch failure.

So the routing model costs (1−α)·C. The owner model costs (1−p)·C. And C
cancels.

> **p\* = α**

Here **α is your existing first touch resolution rate**. It is the fraction of
cases finished by the team they were first assigned to, with no reassignment.
And p is the single owner's rate.

In words, and this is the whole article:

**A single owner beats the routing model precisely when they resolve more cases
at first contact than your current front line already does.**

Two honest caveats. First, α is first touch resolution, not routing accuracy. A
case can land in exactly the right queue and still be bounced. The measurable
quantity is the one that matters, and you can pull it this week.

Second, C cancelling assumes the chain is the same for both designs. That fails
in both directions. Cases that defeat a competent owner are genuinely hard, and
that adverse selection pushes the break even above α. But an owner's escalation
carries real diagnostic work and a reasoned referral, rather than a bounce from
a team that only knows the case is not theirs. That pushes it below. I have
modelled neither. Treat α as the neutral estimate.

The bar is set by your intake, not by your specialists. And first touch
resolution falls as an organisation fragments. So **the more specialist queues
you run, the lower the bar your generalist has to clear.**

That is why T-Mobile and Buurtzorg worked with no AI at all. They were not
beating specialists. They were beating intake.

---

## But breaking even is not a reason to reorganise

No executive restructures a business to break even. The question is magnitude.
Here the handoff parameters return. They set how much you win by, not whether
you win. Take an illustrative organisation whose measured α is around 38%.

| Owner's first contact resolution | Labour saving | Elapsed time saving |
|---|---|---|
| α (break even) | 0% | 0% |
| 55% | 11% | 25% |
| 65% | 17% | 40% |
| 70% | 21% | 47% |
| 80% | 27% | 62% |

Note the ratio. **The saving the customer sees runs at roughly 2.3 times the
cost saving.** Requeue delay dominates elapsed time, and it is charged entirely
to the customer.

For a serious result you want a fifth off labour and nearly half off cycle time.
That needs the owner to resolve about 70% of cases at first contact. It is well
above break even. It is also above what an unaided generalist manages in a deep
technical domain.

That is precisely the gap that changed.

---

## What agentic AI changes, and what it does not

Getting an owner from something like 38% to 70% is a big move. Until recently it
was an impossible one.

The generalist model always had one fatal problem, and it was not
organisational. It was epistemic. The specialist genuinely knows more. Depth was
scarce, slow to build, and could not be in two places at once. So we accepted
the transfer tax, because the alternative was a generalist who simply could not
solve the hard case. That is the constraint that just changed.

The best field evidence is Brynjolfsson, Li and Raymond. They studied 5,172
support agents through a staggered rollout of a generative AI assistant,
published via the NBER and the *Quarterly Journal of Economics*. Average
productivity rose 14% to 15%.

I will use that study for its shape, not its number. It measured issues resolved
per hour. That is throughput. It came mostly from faster handling and higher
concurrency, with only a small rise in successful resolution. My model needs
something else. It needs a change in the probability of resolving a case at
first contact. That is capability. A 15% throughput gain is not a 15% capability
gain.

What the study does establish is direction and distribution. The gains
concentrated among **less experienced and lower skilled workers**. They improved
in both speed and quality. The most experienced agents saw small declines in
quality.

AI did not make the specialists better. It made the non specialists behave more
like specialists. That is gap compression. It is the exact thing the single
owner model was always missing.

And those were suggestion engines. An agent does more. It retrieves from the
knowledge estate, reads the telemetry, runs the diagnostic, drafts the change
and checks the result. It supplies depth at the moment of need, without the case
moving anywhere.

State that precisely, because the tempting overstatement is wrong. The case does
not change hands, so the transfer count is zero. There is no requeue and no
human rediscovery. But zero transfers is not lossless. Agentic systems truncate
context, retrieve wrong evidence, and fail at tool boundaries. That loss is
real, and today it is unmeasured. Agentic AI drives n toward zero. It does not
make ρ equal to one.

Whether these systems actually move a generalist from 38% to 70% is a bet. But
it is a bet on a mechanism we have measured working in the right direction, on
exactly the right people.

---

## What the model implies, and where it breaks

One human owns the customer's problem from first contact to resolution, and does
not let go. Behind them sits an agentic bench supplying depth on demand. It is
not the equal of every specialist. It only has to lift first contact resolution
on the cases that used to require a handoff, and it does so without a
specialist's queueing behaviour. Human specialists remain. They act as
consultants to the owner, not as destinations. They advise. They do not receive.

Accountability cannot move, or the taxonomy grows back. The owner needs real
authority to spend, to credit and to escalate. An owner who must ask permission
is a router with better branding. And you must measure transfers per case, which
almost nobody does.

The honest objections stand. The first one can sink the savings.

My model treats W as a property of the case. It is not, entirely. A specialist
who has seen a failure forty times needs less time than a generalist reasoning
from scratch. Suppose the owner needs δ extra productive minutes on the average
case. Then break even is no longer α. It is **p\* = α + δ/C**, where C is the
cost of the escalation chain, about 47 minutes at the base parameters.

| Extra generalist minutes per case (δ) | Break even first contact resolution |
|---|---|
| 0 | 37.6% |
| 5 | 48.2% |
| 10 | 58.8% |
| 20 | 80.0% |

At ten extra minutes the owner must clear 59%. At twenty the bar is 80% and the
argument is in trouble. The identity p\* = α survives, because it never depended
on W. But it only holds where the owner is as fast as the specialist on the work
itself. Treat the savings as an upper bound. δ is the number I would measure
before betting a reorganisation on any of this.

Second, some cases genuinely need a named human expert. Regulated work and
safety critical work may need a formal, documented handoff. The model does not
say never transfer. It says stop transferring by default, and price it when you
do.

---

## The number I would change on Monday

Every support organisation I know can tell you its average handle time to the
second. Very few can tell you the average number of times a case changes hands.

That second number is where your cost, your cycle time and your customer effort
are hiding. I suspect a fair amount of your attrition is hiding there too,
though I cannot prove it. It has been hiding there since 1776, protected by a
genuinely brilliant idea about pins.

I am not going to tell you that generalists are the most efficient support
model. The honest version is narrower and stronger. The bar a single owner has
to clear was always lower than anyone believed, because it was never the
specialist's competence. It was your own intake. What was missing was a way to
give an ordinary owner the depth to clear that bar by a margin worth having.
That is what changed.

So do three things. Keep stable ownership of the customer's problem. Use
specialists as consultants rather than destinations, wherever the work allows.
And measure, actually measure, whether AI is reducing your transfers without
quietly degrading resolution quality.

None of those three requires you to believe my savings table. They require you
to believe a handoff costs something, and to start pricing it.

The model, the proof, the sensitivity analysis and the full bibliography are
here. So are the widely repeated statistics in this field that did not survive
fact checking, including one I had intended to build this article around.

**github.com/akumarau/transfer-tax**

The defaults are illustrative. Yours are not. Here are three numbers you can
measure this quarter and probably do not. How much context survives a handoff.
How long a cold pickup takes to become productive. And what fraction of your
cases are resolved by the team they were first assigned to.

That third one is your α. It turns out to be the only bar your people have to
clear.

Put your numbers in and tell me I am wrong. That is what it is there for.

---

*Anupam Kumar leads support engineering teams. Views are his own. The model in
this article is his. The errors, once someone finds them, will be in the commit
history.*
