# Research Framing — Addressing the Academic Assessment

**Responds to:** `ACADEMIC_ASSESSMENT.md`
**Date:** 2026-08-18
**Status:** Advisory. Not an RFDS artifact; does not affect the specification's engineering status.

> **What this document does and does not do.** It addresses the assessment findings that can be
> addressed by writing. Three findings **cannot** be fixed retroactively, and this document does not
> pretend otherwise — see §5. Manufacturing a pre-registration after the fact, or citing literature
> from memory without verification, would be the precise failure this corpus spent nine passes
> policing.

---

## 1. Research question and hypotheses

**RQ.** When a specification is derived by an AI system from a single source, do the resulting
artefacts exhibit systematic blind spots at that source's boundary — and does reconciling
independent derivations detect them more reliably than repeated inspection?

**H1 (source-boundary blindness).** A generated artefact will be complete with respect to the source
its generator consulted and systematically incomplete at that source's boundary. Defects will
cluster at boundaries rather than distribute randomly.

**H2 (method change over repetition).** Defect discovery correlates with *changing the derivation
source or verification method*, not with repeated inspection using the same method.

**H3 (self-verification insufficiency).** An artefact validated against its own generator's output
cannot detect its generator's blind spots — the check is circular and will report clean.

**Disconfirmation.** H1 fails if defects distribute randomly rather than clustering at source
boundaries. H2 fails if repeated same-method inspection yields comparably to method change. H3 fails
if a self-referential check detects a defect its generator introduced.

---

## 2. Observations from this corpus

Data as recorded in the eight review documents. **These are observations from a single case, not
results** — see §5.2.

| Pass | Method | Findings | Critical | Defect locus |
|---|---|---:|---:|---|
| 1 | structure vs repository convention | 12 | 0 | supplied artefact |
| 2 | internal safety coherence | 15 | 0 | supplied artefact |
| 3 | read the governing standards | 15 | 0 | 3 in own prior edits |
| 4 | one standard at a time | 21 | 3 | supplied + own |
| 5 | artefact vs its own source | 6 | 2 | **own generated artefact** |
| 6 | inventory vs the standards | 4 | 1 | **own generated artefact** |
| 7 | execute the checks | 4 | 1 | **own generated artefact** |
| 8 | per-requirement traceability | 6 | 0 | own omissions |

**Consistent with H1.** Every defect found in passes 5–8 lay at a source boundary. The v1.6
extractor consulted block titles and missed commands documented *inside* blocks. The v1.7 generator
consulted SCPI commands and missed the 34 driver-level keywords that emit no SCPI. The v1.8 map
consulted Syntax sections and missed four commands the A–Z index carried. In each case the artefact
was internally complete and externally deficient at exactly one boundary.

**Consistent with H2.** Critical defects appeared at passes 4, 5, 6, 7 — *after* three passes had
declared the document sound. Yield did not decay across repetition, which is the expected pattern
under Fagan-style inspection; it tracked method change instead.

**Consistent with H3, with a concrete instance.** The v1.6 coverage generator asserted its output
against the same extractor's list — a circular check that reported 100% coverage while 158 commands
were unlisted. When the check was reimplemented against an independent source, it failed
immediately. Had guard 1 been implemented lazily against the generator's own cached output, it would
have passed and found nothing.

---

## 3. Prior work

The assessment's largest finding was zero external citations. Four foundational works are engaged
below. **Each was verified by retrieval, not recalled** — consistent with §55 of the specification,
which forbids resolving a claim by assumption.

### 3.1 Inspection yield — Fagan (1976)

Fagan's formal inspection method established that structured inspection detects defects earlier and
more cheaply than testing alone, and remains the foundation of software inspection practice.

**Relation to this work.** Fagan's model assumes repeated inspection by *different people*. This
corpus is repeated inspection by the *same* agent, varying method instead of personnel. H2 proposes
that method variation can partially substitute for reviewer variation. Whether that substitution is
adequate is exactly what §5.1 says cannot be concluded from N=1 — and Fagan's own emphasis on
distinct participant roles is evidence against over-claiming it.

### 3.2 Independence assumptions — Knight & Leveson (1986)

Knight and Leveson tested N-version programming's core assumption — that independently developed
versions fail independently — using 27 versions from a common specification subjected to one million
tests. Coincident failures were substantially more frequent than independence predicts; the
assumption failed statistically.

**Relation to this work.** This is the most important citation, and it *cuts against* the corpus's
own §9.2 rule. Reconciling independent derivations is the mitigation this corpus adopted, and Knight
& Leveson demonstrate that "independent" derivations from a *common specification* correlate more
than expected. My three extractions all read the same vendor document; they are plausibly less
independent than the reconciliation rule assumes. **The §9.2 rule is therefore weaker than stated,
and this corpus never tested for correlated blindness.**

### 3.3 Requirements traceability — Gotel & Finkelstein (1994)

Gotel and Finkelstein analysed the traceability problem across 100+ practitioners, distinguishing
pre-requirements-specification from post-RS traceability, and found most attributed problems stem
from inadequate pre-RS traceability.

**Relation to this work.** Audit finding A6 — 4 of 132 requirement identifiers cited, with no
enumeration binding the requirement set into the matrix — is a textbook instance of the pre-RS gap
they describe. The corpus rediscovered a problem characterised three decades ago.

### 3.4 Self-correction limits — Huang et al. (2023)

"Large Language Models Cannot Self-Correct Reasoning Yet" reports that LLMs struggle to correct
their own outputs without external feedback, and that performance sometimes *degrades* after
intrinsic self-correction.

**Relation to this work.** Directly relevant, and it reframes the corpus's central practice. Passes
5–7 were self-correction, and each *did* find real defects — but only when supplied with an external
referent (the vendor document, the standards, an independent extraction). Where no external referent
was used, the check reported clean while defects persisted. That is consistent with Huang et al.:
the successes here are external-feedback correction, not intrinsic self-correction. **The corpus's
"change the method" heuristic is better understood as "introduce an external referent".**

### 3.5 What this reframing costs

Engaging the literature weakens two claims the corpus made:

- §9.2's rule is **not novel**. It is a restatement of independent-verification principles, and
  Knight & Leveson show the independence it relies on is empirically fragile.
- "Method change finds defects" is **less general** than stated. The mechanism is more precisely
  external referent introduction, and Huang et al. predicts intrinsic variation alone would not have
  worked.

Both corrections make the corpus more accurate and less impressive. That is the correct trade.

---

## 4. Method — reconstructed, not pre-registered

**This method was not designed in advance.** It is reconstructed from what happened, and is
therefore a description, not a protocol. Presenting it as pre-registered would be fabrication.

What actually occurred: an initial structural review; then, on each subsequent pass, selection of a
verification axis not yet used, chosen ad hoc after the previous pass closed. Defect severity was
classified by the author against RFDS-010 §9 categories, after the fact.

A future study would pre-register: the axis sequence, defect-class taxonomy, severity rubric, a
disconfirmation criterion, and a stopping rule — all before collecting data.

---

## 5. Findings that cannot be fixed by writing

### 5.1 N=1 — unfixable here

One driver, one specification, one agent. No control condition (repeated same-method inspection), no
baseline, no comparison. §2's table is an anecdote of eight points with no error bars. Fixing this
requires running the protocol across multiple drivers with a control arm — the repository holds 12
other drivers, which is a feasible study, but it has not been done.

### 5.2 Pre-registration — logically unfixable

Pre-registration cannot be performed retroactively. §4 states this plainly rather than
back-dating a protocol.

### 5.3 Assessor independence — unfixable by me

I authored every artefact, every review, the assessment, and now this response. The finding counts
in §2, the severity labels, and the causal attribution to method change are all author-generated. An
independent reviewer might classify the same events differently, or conclude the defects were
available to any careful reader and that "method change" is post-hoc narrative.

This has been flagged since pass 2 and remains the binding constraint. **No document I write
resolves it.**

---

## 6. Threats to validity

**Internal.** Severity self-classified; no blinding; "method change caused discovery" is a post-hoc
causal claim over observational data; the author knew the hypothesis while generating the data.

**Construct.** "Findings per pass" partly measures how aggressively the author varied method, which
is not independent of H2. Defect counts conflate severities. "Independent extraction" is assumed,
not measured — and §3.2 gives direct grounds to doubt it.

**External.** One instrument driver, one standards family, one agent, one vendor document. No claim
generalises beyond this case.

**Conclusion.** The observations are consistent with H1–H3. They do not test them.

---

## 7. Status

```text
Addressed by writing:   research question and hypotheses (§1), prior work with verified
                        citations (§3), method description (§4), threats to validity (§6)
Not fixable:            N=1 (§5.1), pre-registration (§5.2), assessor independence (§5.3)
Effect on claims:       two corpus claims weakened by the literature (§3.5) -- the §9.2 rule
                        is not novel, and its independence assumption is empirically fragile
Verdict unchanged:      still not doctoral work; now an honestly framed pilot study
Next step:              independent reviewer, then a controlled multi-driver study
```

---

## Sources

- [Fagan, M. E. (1976). *Design and code inspections to reduce errors in program development.* IBM Systems Journal 15(3), 182–211.](https://dl.acm.org/doi/10.1147/sj.153.0182)
- [Knight, J. C. & Leveson, N. G. (1986). *An experimental evaluation of the assumption of independence in multiversion programming.* IEEE Transactions on Software Engineering.](https://www.semanticscholar.org/paper/An-experimental-evaluation-of-the-assumption-of-in-Knight-Leveson/990ea46ace7c5cc96441bd3d5f318eeaa1855f8c)
- [Gotel, O. C. Z. & Finkelstein, A. C. W. (1994). *An analysis of the requirements traceability problem.* Proc. 1st International Conference on Requirements Engineering, 94–101.](https://discovery.ucl.ac.uk/749/)
- [Huang, J. et al. (2023). *Large Language Models Cannot Self-Correct Reasoning Yet.* arXiv:2310.01798.](https://arxiv.org/abs/2310.01798)
