# Academic Assessment — `rf_keysight349xx` as Doctoral Work

> **PARTIALLY ADDRESSED.** `RESEARCH_FRAMING.md` supplies the research question, hypotheses,
> verified prior-work engagement, method description, and threats to validity. Three findings remain
> **unfixable**: N=1 validation, retroactive pre-registration, and assessor independence. The overall
> verdict is unchanged — still not doctoral work, now an honestly framed pilot study.
> Engaging the literature also *weakened* two claims this corpus had made; see `RESEARCH_FRAMING.md`
> §3.5.

**Assessed corpus:** 11 specification revisions, 8 review/audit documents, 1 vendor command map
(351 commands), 1 traceability matrix (132 requirements), 1 executable validator, 22 commits —
~38,600 lines
**Assessment date:** 2026-08-18
**Criteria:** conventional doctoral standards — original contribution, research question,
methodology, situating in prior work, validation, generalisability, critical reflection
**Assessor position:** I authored the entire corpus and every prior review of it. That is a
disqualifying conflict for a real examination and is treated as a finding, not a footnote (§6).

---

## 1. Verdict

**As submitted: not doctoral work. It is competent professional engineering with an undeveloped
research kernel inside it.**

The distinction matters and is not a matter of polish or volume. A specification — however rigorous,
traceable, and conformant — is an *artefact*, not a *contribution to knowledge*. Nothing here is
currently framed as a claim that could be true or false about the world.

However, the corpus contains something a thesis could be built on, and it is not the driver. It is
the **empirical record of the review process** — nine passes, each finding defects the previous
missed, with a recurring and now-documented failure mechanism. That record is data. It is presently
recorded as project narrative rather than analysed as evidence.

**Assessment: fail as a thesis; pass as an engineering artefact; viable as the pilot study for one.**

---

## 2. Against doctoral criteria

| Criterion | Assessment |
|---|---|
| Original contribution to knowledge | **Absent as framed.** The driver spec is an application of existing standards (RFDS-001–020) to one instrument. Applying a standard correctly is engineering, not research. |
| Research question | **Absent.** No question is posed anywhere in 38,600 lines. The work asks "is this spec correct?", which is a QA question, not a research question. |
| Situating in prior work | **Absent, and this is the most serious gap.** Zero external citations. The corpus cites only project-internal RFDS documents and one vendor manual. |
| Methodology | **Partially present.** The method evolved deliberately and is documented, but was never *designed* — it was reactive. No protocol was stated in advance. |
| Validation | **Weak.** N=1, no control, no baseline, no comparison against an alternative process. |
| Generalisability | **Asserted, not demonstrated.** One general rule is stated (§9.2) but is supported by anecdote from a single case. |
| Critical self-reflection | **Genuinely strong.** Unusually so — see §4. |
| Reproducibility | **Strong.** Verbatim sources with checksums, mechanical extraction, an executable validator. |
| Written presentation | **Strong.** Consistent, traceable, well-structured. |

---

## 3. The research kernel that is actually here

Stripped of project framing, the corpus contains this observation:

> Every generated artefact was complete with respect to the source its generator consulted, and
> incomplete with respect to a source it never consulted. Defects were not found by more careful
> inspection; they were found by *changing the derivation source*.

The supporting data, drawn from the review documents:

| Pass | Method | Findings | Critical | Defect located in |
|---|---|---:|---:|---|
| 1 `SPEC_REVIEW` | structure vs repository convention | 12 | 0 | supplied spec |
| 2 `DEEP_REVIEW_v1.1` | internal safety coherence | 15 | 0 | supplied spec |
| 3 `GUIDE_CONFORMANCE_v1.2` | read the standards | 15 | 0 | **own prior edits** (3 of 15) |
| 4 `CYCLING_REVIEW_v1.3` | one standard at a time | 21 | 3 | supplied spec + own edits |
| 5 `ARTIFACT_REVIEW_v1.6` | artefact vs its source | 6 | 2 | **own generated artefact** |
| 6 `DEEP_REVIEW_v1.7` | inventory vs the standards | 4 | 1 | **own generated artefact** |
| 7 `EXECUTABLE_REVIEW_v1.8` | execute the checks | 4 | 1 | **own generated artefact** |
| 8 `RFDS001_AUDIT_v1.9` | per-requirement traceability | 6 | 0 | own omissions |

Three properties of this table are non-obvious and worth a researcher's attention:

1. **Defect discovery did not decay with repetition.** Passes 5–7 each found *critical* defects after
   four prior passes had declared the document sound. Conventional expectation is that review yield
   decays; here it did not, because each pass changed method rather than repeating one.
2. **The defect locus migrated from the supplied artefact to the generated one.** Early passes found
   flaws in the input; later passes found flaws the reviewer had introduced while fixing earlier
   findings. Passes 5, 6, and 7 found defects located exclusively in the reviewer's own output.
3. **Two critical defects were self-inflicted capability deletions.** `ARTIFACT_REVIEW` R1 and
   `DEEP_REVIEW_v1.7` D1 both describe a generated inventory silently removing declared
   capabilities — D1 removed 33 of 34 mandatory keywords. Both passed every prior inspection.

That is a testable claim about AI-assisted specification work, and it is currently buried in a
project changelog.

---

## 4. What already meets scholarly standard

Recorded because a fail verdict should not obscure genuine quality:

- **Provenance discipline.** The vendor reference is stored verbatim with an MD5 that is re-verified
  after every revision; the supplied v1.0 spec likewise. Source integrity is auditable.
- **Negative results are recorded, not buried.** `ARTIFACT_REVIEW_v1.6.md` §5 and
  `DEEP_REVIEW_v1.7.md` §5 both document the author's own critical errors in full, including the
  mechanism. This is rarer than it should be and is the corpus's most academically creditable habit.
- **Falsifiable claims replaced unfalsifiable ones.** The "193 commands, 100% coverage" assertion was
  withdrawn and replaced with a stated extraction method and count — a claim a third party can refute.
- **A prediction was made and later confirmed against source.** `DEEP_REVIEW_v1.1.md` N4 predicted
  continuity/diode would resolve `NOT_APPLICABLE` before the vendor manual was available; the manual
  confirmed it. Small, but it is a hypothesis-then-test sequence.
- **Executable verification.** `validate_command_coverage.py` makes one claim mechanically checkable
  by anyone.

---

## 5. What a thesis would require

### 5.1 A research question

None is currently posed. A defensible one the corpus already gestures at:

> *Do specifications derived by an AI system from a single source exhibit systematic, predictable
> blind spots at the boundary of that source — and does reconciling independent derivations detect
> them more reliably than repeated inspection?*

### 5.2 Prior work — the largest gap

Zero external citations. At minimum this work sits in, and must engage with:

- requirements traceability and coverage (Gotel & Finkelstein and successors);
- specification inspection yield — Fagan inspection, and the literature on defect-detection decay;
- N-version programming and independent derivation as a fault-detection strategy, which is close to
  what §9.2's reconciliation rule reinvents;
- LLM code and specification generation, hallucination, and self-verification limits;
- standards-conformance auditing.

The §9.2 rule — *an inventory assembled from one source is authoritative only over that source's
domain* — is plausibly a rediscovery of established results in independent verification. A thesis
must establish whether it is novel or a restatement. Currently that question is not asked.

### 5.3 Method designed in advance, not reactively

The nine passes were improvised. A study would pre-register the method sequence, define defect
classes before collecting them, and specify what would count as disconfirmation.

### 5.4 Validation beyond N=1

Required: multiple drivers or specifications; a control condition (repeated same-method inspection);
independent reviewers to establish inter-rater reliability; and a measure of defect severity that is
not the author's own judgement.

### 5.5 Threats to validity, stated

None are currently stated. At least: single author; author-as-assessor; no blinding; defect counts
self-classified; the corpus's own metric (findings per pass) partly reflects how aggressively the
author chose to change method, which is not independent of the hypothesis.

---

## 6. Assessor conflict — treated as a finding

I wrote every document assessed here, including all eight prior reviews, and I am now assessing my
own work against academic criteria. In an examination this invalidates the assessment outright.

It is worth stating precisely what that does to confidence in §3's table: the finding counts, the
severity labels, and the claim that "method change caused discovery" are all author-generated. An
independent reviewer might classify the same events differently, or find that defects I attribute to
method change were simply available to any careful reader.

The corpus has flagged this repeatedly — the phrase "single-reviewer monoculture" recurs from
`DEEP_REVIEW_v1.1` onward — but flagging a conflict does not resolve it. **The single highest-value
next step, academically and practically, is an independent reviewer.** No further self-assessment
changes this.

---

## 7. Recommendation

| If the goal is | Then |
|---|---|
| A production driver | Proceed to Phase 1 Gate 1. The specification is fit for that purpose. |
| A doctoral contribution | The driver is the *case study*, not the thesis. Reframe around the verification-methodology question in §5.1, add the literature engagement in §5.2, and design the study in §5.3–§5.5. |
| A publishable paper (nearer term) | An experience report on multi-method verification of AI-generated specifications is plausible at a software-engineering venue, if §5.2 and §6 are addressed honestly. The data in §3 is genuinely interesting. |

---

## 8. Status

```text
Assessed:              11 spec revisions, 8 reviews, 351-command map, 132-requirement matrix,
                       1 validator, 22 commits (~38,600 lines)
Verdict as thesis:     FAIL -- no research question, no prior-work engagement, N=1, no controls
Verdict as artefact:   PASS -- rigorous, traceable, conformant, reproducible
Research kernel:       present but undeveloped (§3)
Blocking gap:          assessor is the author (§6)
Recommended next step: independent review, before any further self-assessment
```
