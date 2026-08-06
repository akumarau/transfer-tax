# Research notes

Every source behind the article, with what it does and does not support.

This file exists because thought-leadership writing about support operations is
awash in numbers that nobody can trace. Several claims that are widely repeated
in this space turned out, on checking, to be misattributed or unverifiable. They
are listed at the bottom under **Claims deliberately not used**, along with the
reason. If you find an error anywhere in here, open an issue.

---

## 1. Handoffs destroy information, and the evidence is clinical

**Starmer AJ, Spector ND, Srivastava R, et al. "Changes in Medical Errors after
Implementation of a Handoff Program." *New England Journal of Medicine*
2014;371(19):1803–1812.** DOI: 10.1056/NEJMsa1405556

The strongest single citation in the whole argument. Prospective, nine
hospitals, 10,740 admissions. After implementing the I-PASS structured handoff
bundle:
- medical errors fell **23%** (24.5 → 18.8 per 100 admissions, p<0.001)
- preventable adverse events fell **30%** (4.7 → 3.3 per 100 admissions, p<0.001)
- non-preventable adverse events did not change (3.0 → 2.8, p=0.79)

That last line is the one that matters analytically. The intervention moved only
the harm that communication could touch and left the rest alone. That is about
as clean a demonstration of handoff-generated harm as an operational system will
ever give you.

Cite it precisely. It is a **prospective before/after study of a
multi-component bundle** — mnemonic, training, faculty development, sustainability
campaign — not a randomised controlled trial, and site-level reductions were
significant at six of the nine hospitals. It establishes a strong association in
a clinical setting. It is not direct evidence about support organisations, and
should not be presented as such.

### On the Joint Commission "80%" figure — deliberately not used

The claim that "communication failures during hand-offs contribute to
approximately 80% of serious medical errors" is ubiquitous in this literature
and was originally going to open the article.

It did not survive review. One verification pass located it in Sentinel Event
Alert Issue 58 (September 2017), attributing it to a Joint Commission Center for
Transforming Healthcare root-cause analysis rather than a direct count. A second,
independent pass went to the source and reported that Alert 58 does not state it,
and instead cites communication failures as a factor in roughly 30% of
malpractice claims over a five-year period.

I could not resolve the discrepancy to my own satisfaction. A public health
statistic in a public article is not the place to guess, so it is not in the
article. Starmer carries that section on its own and carries it better.

If you can settle the provenance definitively, please open an issue.

---

## 2. Coordination is not free

**Coase, R.H. "The Nature of the Firm." *Economica* 1937;4(16):386–405.**
Firms exist because transacting has costs — search, bargaining, enforcement —
and internal organisation can economise on them. Coase received the Nobel
Memorial Prize in Economic Sciences in **1991**.

**Williamson, O.E. *The Economic Institutions of Capitalism.* Free Press, 1985.**
Extends Coase into transaction cost economics proper: asset specificity,
bounded rationality, opportunism. Williamson received the Nobel in **2009**,
shared with Elinor Ostrom.

These are two different people with two different prizes, which is worth stating
because they are routinely conflated. The relevant point for support operations
is the one Coase makes and Williamson formalises: moving something across an
organisational boundary is itself a transaction, and transactions cost.

**Brooks, F.P. Jr. *The Mythical Man-Month.* Addison-Wesley, 1975.**
Communication channels in a fully connected group of n people: **n(n−1)/2**.
Adding the tenth person to a nine-person team does not add one channel, it adds
nine. Use it precisely — it counts channels, not cost.

**Gittell, J.H. "Supervisory Span, Relational Coordination, and Flight Departure
Performance." *Organization Science* 2001;12(4):468–483.**
**Gittell, J.H. "Coordinating Mechanisms in Care Provider Groups: Relational
Coordination as a Mediator and Input to Performance." *Management Science*
2002;48(11):1408–1426.**
**Gittell, J.H. *The Southwest Airlines Way.* McGraw-Hill, 2003.**
Relational coordination — frequent, timely, accurate, problem-solving
communication supported by shared goals, shared knowledge and mutual respect —
predicts operational performance in both airline turnarounds and hospital care.
Effect sizes vary by study and setting; quote the mechanism, not a headline
percentage, unless you have the specific table in front of you.

---

## 3. Customers experience transfers as effort, and effort as betrayal

**Dixon, M., Freeman, K. & Toman, N. "Stop Trying to Delight Your Customers."
*Harvard Business Review*, July–August 2010.**
Study of more than 75,000 customers. Introduces the Customer Effort Score.
Core finding: reducing effort predicts loyalty far better than exceeding
expectations does.

**Dixon, M., Toman, N. & DeLisi, R. *The Effortless Experience.* Portfolio /
Penguin, 2013.**
Note the author list — the book's third author is **Rick DeLisi**, not Karen
Freeman. Reports that 96% of customers in high-effort service interactions
showed increased disloyalty intent, against 9% in low-effort interactions, and
that 57% of customers who contacted service had to re-explain their problem to
a new agent.

**SQM Group** — annual first-contact-resolution benchmarking across North
American contact centres. Consistently reports an approximately 1:1 relationship
between FCR percentage points and customer satisfaction percentage points, with
a comparable effect on operating cost. Their reports are commercial rather than
peer-reviewed, and their published industry-average FCR figure moves year to
year, so cite the relationship rather than a specific benchmark number.

---

## 4. Fragmenting a pool is expensive even when routing is perfect

**Halfin, S. & Whitt, W. "Heavy-Traffic Limits for Queues with Many Exponential
Servers." *Operations Research* 1981;29(3):567–588.**
The square-root safety staffing regime: c ≈ R + β√R.

**Gans, N., Koole, G. & Mandelbaum, A. "Telephone Call Centers: Tutorial,
Review, and Research Prospects." *Manufacturing & Service Operations Management*
2003;5(2):79–141.**
The definitive review of call-centre queueing.

**Kleinrock, L. *Queueing Systems, Volume 1: Theory.* Wiley-Interscience, 1975.**
**Cachon, G. & Terwiesch, C. *Matching Supply with Demand.* McGraw-Hill.**

The pooling result is a theorem, not an observation. For fixed total arrival
rate and fixed per-server service rate, a single pooled M/M/c queue yields
strictly lower expected waiting time than m separate queues of c/m servers each
at identical total capacity and utilisation. In the square-root staffing regime
the safety capacity of m fragmented pools scales as O(√m) relative to the
pooled system.

`transfer_tax/pooling.py` computes the exact Erlang C result rather than the
asymptotic, so the figures quoted in the article are exact for the stated
parameters and reproducible.

---

## 5. Specialisation: the original case, and its limits

**Smith, A. *An Inquiry into the Nature and Causes of the Wealth of Nations.*
London, 1776. Book I, Chapter 1.**
Ten workers dividing pin-making into about **eighteen** distinct operations
produced upwards of **48,000 pins a day**, around 4,800 each. Working
separately, Smith says, they "certainly could not each of them have made twenty,
perhaps not one." Quote him precisely; the lower bound is essentially zero, not
one.

The argument in the article is not that Smith was wrong. It is that his pin
never had an opinion about how many hands touched it, and a customer does.

**Ton, Z. *The Good Jobs Strategy.* New Harvest / Houghton Mifflin Harcourt,
2014.**
Case studies of Costco, Trader Joe's, QuikTrip and Mercadona: cross-trained,
well-paid, broadly-scoped employees producing higher productivity and much lower
turnover. QuikTrip's revenue per labour hour roughly double competitors'; annual
turnover around 13% against an industry norm many times that. This is a
practitioner case-study book by an MIT Sloan researcher, not a controlled study.
Cite it as evidence that the model exists and works, not as causal proof.

**Ton, Z. & Huckman, R.S. "Managing the Impact of Employee Turnover on
Performance." *Organization Science* 2008;19(1):56–68.** — peer-reviewed
companion work.

---

## 6. Why fragmented work also breaks the people doing it

**Hackman, J.R. & Oldham, G.R. "Motivation through the Design of Work: Test of a
Theory." *Organizational Behavior and Human Performance* 1976;16(2):250–279.**
The Job Characteristics Model. **Task identity** — the degree to which a job
involves completing a whole, identifiable piece of work with a visible outcome —
is one of five core dimensions driving experienced meaningfulness, and through
it internal motivation and satisfaction. An agent who owns one slice of a
customer's problem and never sees the resolution has had task identity designed
out of their job.

**Darley, J.M. & Latané, B. "Bystander Intervention in Emergencies: Diffusion of
Responsibility." *Journal of Personality and Social Psychology*
1968;8(4):377–383.**
**Latané, B., Williams, K. & Harkins, S. "Many Hands Make Light the Work."
*Journal of Personality and Social Psychology* 1979;37(6):822–832.**
Responsibility diffuses as the number of people notionally responsible grows,
and individual effort falls. Used in the article as an analogy for what happens
to ownership along a transfer chain, not as a direct empirical finding about
support queues.

---

## 7. The corporate evidence

**Dixon, M. "Reinventing Customer Service." *Harvard Business Review*,
November–December 2018.**
The substantive published account of T-Mobile US's **Team of Experts**, launched
in 2018 under Callie Field with Mike Sievert. Customers assigned to a dedicated,
co-located team accountable for a fixed set of accounts; IVR routing menus and
cold transfers removed. Reports material improvements in customer metrics and a
large fall in agent attrition against a US contact-centre industry norm of
roughly 27% annual attrition.

**T-Mobile US quarterly earnings releases, 2018–2019** (investor.t-mobile.com).
Postpaid phone churn of 0.97% in Q3 2018, materially improved on prior years.
This is the primary-source, auditable version of the churn claim.

**Ernst & Young, Buurtzorg evaluation, 2009**, and **KPMG, *Buurtzorg Nederland:
Home Care Reinvented*, January 2015.**
Buurtzorg, founded 2006 by Jos de Blok, runs self-managing teams of 10–12 nurses
serving 50–60 patients per neighbourhood, with generalist nurses owning the
whole relationship. The widely-quoted finding that Buurtzorg uses roughly **40%
fewer care hours per client** comes from the **2009 E&Y study**, not from KPMG.
KPMG's 2015 study found Buurtzorg to be a low-cost home-care provider, not
explained by patient mix — but also found that once nursing home, physician and
hospital costs were included, **total per-patient cost was around the Dutch
average**. Both halves belong in an honest citation.

**Nohria, N. et al. *Buurtzorg: Humanity Above Bureaucracy.* Harvard Business
School Case 9-518-096, 2018.** — teaching case, useful context.

**Hsieh, T. *Delivering Happiness.* Business Plus, 2010.** — primary source for
the Zappos Customer Loyalty Team model: no scripts, no handle-time targets, no
transfer mandate. Practitioner evidence, not research.

USAA's empowered-representative model is consistently top-ranked in Forrester's
US Customer Experience Index and is used as a low-effort benchmark in Dixon et
al. (2013). There is no academic study of it. Treat as illustrative.

---

## 8. What changed: measured AI augmentation

**Brynjolfsson, E., Li, D. & Raymond, L.R. "Generative AI at Work." *NBER
Working Paper 31161*, April 2023; published version *Quarterly Journal of
Economics*, 2025.**
Staggered rollout of a generative AI conversational assistant across **5,172**
customer-support agents. Productivity, measured as issues resolved per hour,
rose **14%** in the original working paper and **15%** in the published version.

The distributional result is the one that matters for the argument here, and it
is explicit in the abstract: the gains were concentrated among **less
experienced and lower-skilled workers**, who improved in both speed and quality,
while **the most experienced and highest-skilled workers saw small gains in
speed and small declines in quality**.

That is the augmentation-yield parameter γ in `transfer_tax/model.py`, measured
in the field. AI does not make your best specialist much better. It makes the
person who is not a specialist behave much more like one. Which is precisely
what the single-owner model needs and precisely what it never had before.

**Chui, M., Hazan, E., Roberts, R., et al. "The Economic Potential of Generative
AI." McKinsey Global Institute, June 2023.** — consultancy research, directionally
consistent, cite as such.

---

## Claims deliberately not used

Each of these is widely repeated in support-operations writing. Each failed
verification. They are recorded here so nobody has to re-do the work.

| Claim | Why it is not in the article |
|---|---|
| Joint Commission "80% of serious medical errors involve handoff miscommunication" | Two independent verification passes disagreed on whether Sentinel Event Alert 58 actually states this. Unresolved provenance on a public health statistic. See §1. |
| T-Mobile "NPS up 56%" | NPS is an absolute score, not a percentage change, and no primary source confirms this figure. It circulates in decks without provenance. |
| T-Mobile "unresolved issues down 40%" | No traceable primary source. Consultancy folklore. |
| T-Mobile churn improvement as *caused by* Team of Experts | The 0.97% Q3 2018 postpaid churn figure is real and citable from the earnings release. Attributing it causally to the redesign is not supportable — there is no counterfactual. Stated as association only. |
| Buurtzorg "KPMG found 40% fewer care hours" | Misattribution. The 40% figure is E&Y 2009. KPMG 2015 found something materially different and less flattering. |
| "SQM: industry FCR is 68%" | SQM's published figure moves between editions and sectors. Quoting a single number as a stable benchmark is not defensible. |
| "Channel switching makes customers 4x more likely to be disloyal" | A summary restatement rather than a figure in the source. The 96% / 9% comparison is the directly attributable one. |
| USAA and Zappos as "studies" | Both are real and instructive. Neither is research. Labelled as practitioner evidence in the article. |
| Gartner's "$80bn contact-centre labour cost reduction by 2026" | A market projection, not a finding. |
| Any γ estimated from the Brynjolfsson 14–15% figure | That study measured issues resolved per hour, driven largely by handle time and concurrency. γ is a change in the probability of first-contact resolution. Different quantities. The study is used for the *direction and distribution* of the effect only, never for a magnitude. |

---

## On the model itself

The mathematics in this repository is mine, not borrowed, and it is a *model* —
a deliberately simple one. It rests on assumptions, all falsifiable, and three
independent reviews (Gemini 3.1 Pro, Grok 4.5, GPT-5.6) were run against it
before publication. Several of their findings are baked into what follows.

1. The productive work a case requires is a property of the case, not of the
   org. **This is the weakest assumption in the whole model.** A specialist
   plausibly needs less time than a generalist for the same case. If owner-first
   adds δ extra minutes, the break-even rises to α + δ/C — see
   `breakeven_with_owner_overhead`, and the table in the README. Twenty extra
   minutes and the argument is in real trouble.
2. Handoffs transmit a constant fraction ρ of accumulated context.
3. Re-discovery cost is proportional to context lost, and rebuilt context does
   *not* re-enter the transferable record. **Convexity follows from this second
   clause, not from lossy handoffs alone.** The charitable alternative — every
   receiver fully restores and retransmits — gives a linear tax and 1.82× rather
   than 2.10× at three transfers. `linear_transfer_tax` computes it.
4. The escalation chain is common to both designs. This is what makes the
   break-even identity work, and it is an economic assumption rather than a free
   lunch. Adverse selection pushes the true break-even above α; better handover
   quality from an owner pushes it below.
5. Routing accuracy degrades as the number of destinations grows. The
   `a + (1−a)/m` form is an explicitly labelled toy and should not be confused
   with the measurable quantity the theorem actually uses, which is first-touch
   *resolution*.

What survives all of that is the break-even identity itself, which depends on
none of ρ, κ, h or W — only on the chain being common and the tax being zero at
zero transfers. The magnitudes are model-dependent. The bar is not.

If you think an assumption is wrong, change it and rerun. The sensitivity
analysis in `scripts/run_scenarios.py` reports exactly where the conclusion
would fail.
