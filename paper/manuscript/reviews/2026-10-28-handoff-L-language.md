# Independent L-axis review

Scope: requested English files only; read only expert-language.md as the reviewer rule source. No other expert rules, reviews or handoff reports consulted. Source files unchanged. Locations below are source lines as read. Mathematical truth, numeric reproducibility and source-content verification are outside this language-only review; a clean citation scan means correct placement, not verification of the cited paper. User's direct declarative style is retained: none of the proposed repairs adds rhetorical transitions or ornamental vocabulary.

The paragraph is the unit. Sentence sequences list grades in reading order, including prose resumed after displays as part of its initiating paragraph. Mathematical displays are assessed only for language surrounding them. Sections are functional classifications, not merely printed headings. `0 claims` means no prevalence, deliberate external use or external provenance claim was detected. Self-reports of this study are not external attribution claims. A theoretical derivation is treated as Methods/theory; present-tense mathematical statements are admissible, unlike present-tense narration of a completed test programme.

## Highest-priority repairs

| Location | Trimmed sentence | Grade | Axis | Named defect and evidence | Executable repair |
|---|---|---|---|---|---|
| sections/00-related-work.tex:15, sentence 3 | representation and successive recovery “belong to classical two-port analysis and Cauer synthesis” | D | L1 | External provenance has no citation in this sentence; neighbouring citations do not license it (ER-T08, ER-T17, ER-T21). | Attach the verified primary synthesis/analysis citation to this sentence. Do not attach a source merely because it is already in the preceding sentence; check that it supports this representation/extraction attribution. |
| sections/02a-general-order-theory.tex:28–33, sentences 2–3 | “Cauer continued-fraction form”; “is the classical RC ladder extraction” | D | L1 | Explicit external provenance without a same-sentence citation (ER-T08). | Cite a checked primary source after “form” and after the classical-extraction statement, or combine those statements into one cited sentence. |
| sections/03a-dynamic-ratio-and-transient-leakage.tex:113, sentence 6 | “absolute tracking errors were -161.01 and -255.79 Ω” | B | L3/L5 | “Absolute” and negative signed values conflict. This is a lexical defect, not a request to alter numbers. | Replace “absolute tracking errors” with “signed tracking errors”; likewise use “signed tracking error” in the last sentence if the distinction is signed error versus current-history difference. |
| sections/03a-dynamic-ratio-and-transient-leakage.tex:115, sentence 3 | “signed first-moment residual RMS” | B | L5 | A modifier attached to a nonnegative RMS obscures whether residuals or RMS are signed. | Use “RMS of the first-moment prediction residual divided by the RMS of the exact error”. |
| sections/03a-dynamic-ratio-and-transient-leakage.tex:115, sentence 5 | “Keeping both ... explains the leading residual” | C | L7 | The paragraph's claim is reported test discrepancies; this sentence introduces causal interpretation within Results (§2e). | Move this explanation to Discussion; keep the reduced residual values and stated comparison conditions in Results. |
| sections/04a-noise-and-pairing.tex:53, sentence 2 | “... multiplies ... by m^4, explaining the high-frequency rejection floor” | C | L7 | The paragraph combines the algebraic perturbation mechanism, results of the AC suite and manufacturing interpretation. Its “explaining” clause is an explicit Discussion move (§2e, §2 paragraph function). | Separate the scaling identities as theory, and put the explanation/limits on manufacturing comparison in Discussion. No need to rewrite the identities. |

## Paragraph verdicts

For accepted paragraphs, evidence is the sentence itself and the applicable language axes; no named rule fires. `A×n` records every sentence as A. A/B counts below are paragraph counts, not invented word-level precision. The classifications intentionally do not penalize compact mathematical exposition for lacking a rhetorical contrast sentence.

| Unit/location | Functional section | Class; sentence grades | Citation scan | Opening scan | Paragraph note/repair |
|---|---|---|---|---|---|
| main.tex:27 abstract | Abstract | A; A×15 | clean (not applicable: abstract, ER-T19) | clean (“Terminal loading and direct-current calibration” names subject) | Scope includes exact complete responses, ideal models and checked frequency; direct style admissible. |
| 00-related-work:5 | Introduction | A; A×5 | clean (2 external attribution claims, both cited) | clean (“Differential measurement” names subject) | Prior work develops into loading question. |
| 00-related-work:7 | Introduction | A; A×6 | clean (3 external attribution claims, all cited) | clean (“The complex gain” has prior differential-gain context) | Limits of magnitude-only rejection close the paragraph. |
| 00-related-work:10 | Introduction | A; A×5 | clean (1 external attribution claim cited) | clean (“Casas and Pallàs-Areny” names subject) | Topology-to-specific-network move is clear; no editorial rewrite requested. |
| 00-related-work:12 | Introduction | A; A×5 | clean (1 external attribution claim cited) | clean (“Impedance balance” names subject) | Clear terminal-loading question. |
| 00-related-work:15 | Introduction | D; A,A,D,A,A | absent on provenance: “belong to classical ... Cauer synthesis” | clean (“Guillemin” names subject) | Attach verified source to sentence 3, as above. |
| 00-related-work:17 | Introduction | A; A×6 | clean (3 external attribution claims, all cited) | clean (“Component realization and sensitivity” names subject) | Ends on evaluation criterion. |
| 00-related-work:20 | Introduction | A; A×4 | clean (0 external claims; “supplies” states the present calculation's use, not external priority) | clean (“The present study” names subject) | Contribution scope remains bounded. |
| 00-related-work:22 | Introduction | A; A×4 | clean (1 external attribution claim cited) | clean (“The cancellation statements” refers to the preceding contribution) | Explicitly connects noise scope to added calculation. |
| 01-introduction:3 | Introduction | A; A×4 | clean (1 external attribution claim cited) | clean (“A differential filter” names subject) | Self-contained opening. |
| 01-introduction:5 | Introduction | A; A×4 | clean (1 external attribution claim cited) | clean (“The relevant matching quantities” refers to preceding transfer matching) | Load mechanism and need are explicit. |
| 01-introduction:7 | Introduction | A; A×4 | clean (0 external provenance/prevalence claims) | clean (“In a buffered resistive-sensor interface” establishes model) | Analytical motivation within declared configuration. |
| 01-introduction:9 | Introduction | A; A×4 | clean (0 external claims; present-study use of extraction) | clean (“The objective of this study” names purpose) | Concise scope and route. |
| 02a:6–16 | Methods/theory | A; A×7 | clean (0 external claims) | clean (“Consider a branch” defines subject) | Model, recurrence and consequences belong together. |
| 02a:18–24 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“The open-circuit transfer” refers to defined branch) | Output-impedance purpose closes derivation. |
| 02a:28–33 | Methods/theory | D; A,D,D,A | absent on provenance: “Cauer”, “classical RC ladder extraction” | clean (“With the source shorted” refers to defined circuit) | Same-sentence citations required. |
| 02a:35–44 | Methods/theory | A; A×6 | clean (0 external claims) | clean (“The last-stage values” refers to defined ladder) | Recoveries and positivity are precisely described. |
| 02a:46 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“Conversely, start with real polynomials” identifies inverse direction) | Conditional realization test retains its conditions. |
| 02a:48 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“The forward map” refers to recurrence) | Locality is retained. |
| 02a:52 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“Hold one reference branch fixed” states condition) | Distinguishes uniform scaling from family. |
| 02a:54 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“At a specified g>0” states condition) | Raw-gain convention explicit. |
| 02a:56–60 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“Direct-current calibration” is explicit contrast with raw matching) | Normalized criterion and example share a subject. |
| 02a:62–66 | Methods/theory | A; A×3 | clean (0 external claims) | clean (“For N=2, branch P” defines example) | Raw versus calibrated difference closes example. |
| 02a:83–88 | Methods/theory | A; A×5 | clean (0 external claims) | clean (“At two distinct positive conductances” states condition) | Complete complex response condition is explicit. |
| 02a:90 | Methods/theory | A; A×6 | clean (0 external claims) | clean (“Two normalized resistive-load responses” names subject) | Exact result separated from noisy estimator. |
| 02a:94–107 | Methods/theory | A; A×8 | clean (0 external claims) | clean (“A known rational load” defines subject) | Conditions on coprimality, degree and positivity retained. |
| 02a:109 | Methods/theory | A; A×3 | clean (0 external claims) | clean (“Table ... applies Eq.” explicit comparator) | Load distinctions stated directly. |
| 02a:128 | Methods/theory | A; A×5 | clean (0 external claims) | clean (“Two distinct known rational admittances” names subject) | Raw matching qualifier avoids scope drift. |
| 02a:132–140 | Methods/theory | A; A×5 | clean (0 external claims) | clean (“For independent branches” states model) | Defined differences carry through prose. |
| 02a:142–143 | Discussion/theory limitation | A; A×8 | clean (0 external claims) | clean (“Exact identifiability and measurement conditioning” names distinction) | Normalization caveat and estimator limitation are explicit. Split into two paragraphs before the long coefficient-map sentence if desired; not required by a rule. |
| 03a:4 | Methods/theory | A; A×5 | clean (0 external claims) | clean (“The buffered front end of Section...” provides antecedent) | Prehistory and nonzero denominator properly stated. |
| 03a:13–22 | Methods/theory | A; A×6 | clean (0 external claims) | clean (“For GP=GN” states condition) | Exact identity then exponential example; no lost hedge. |
| 03a:24–34 | Methods/theory | A; A×6 | clean (0 external claims) | clean (“The nodal state matrix” refers to specified ladder) | Positivity supports stated bound; startup caveat closes. |
| 03a:39–68 | Methods/theory | A; A×14 | clean (0 external claims) | clean (“For different normalized kernels” states case) | Dense but coherent derivation; order, denominator and smoothness qualifications are explicit. |
| 03a:70–74 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“For unit-component ladders” states condition) | Loaded scaling effects retained. |
| 03a:81–86 | Methods/theory | A; A×7 | clean (0 external claims) | clean (“The calibrated readout” has defined antecedent) | Necessary/sufficient criterion and raw-gain caveat close. |
| 03a:91 | Methods/theory | A; A×5 | clean (0 external claims) | clean (“Each branch” refers to model) | Repeated-product-pole caveat is direct. |
| 03a:93–99 | Methods/theory | A; A×7 | clean (0 external claims) | clean (“For branches matched at g0” states case) | Step versus impulse quantity distinguished explicitly. |
| 03a:101–105 | Results/theoretical evaluation | A; A×5 | clean (0 external claims) | clean (“For P/T in Table...” provides reference) | Numerical peak, settling thresholds and ideal-edge comparison bounded. |
| 03a:113 | Results | B; A,A,A,A,A,B,A,B | clean (0 external claims) | clean (“Six baseline ... cases” names tests) | Replace both uses of “absolute tracking error” with “signed tracking error”; one repeated lexical correction. |
| 03a:115 | Results | C; A,A,B,A,C,A,A,A | clean (0 external claims) | clean (“Two constant-resistance cases” names tests) | Clarify RMS wording; move explanatory sentence to Discussion. |
| 03a:119 | Results/theoretical evaluation | A; A×5 | clean (0 external claims) | clean (“For a current step ...” states condition) | Fast-edge validity condition is clear. “Final crossings” can optionally become “last crossings below”; current wording understandable. |
| 03a:121 | Discussion/model limitations | A; A×7 | clean (0 external claims) | clean (“The ratio model” has defined antecedent) | Declared physical boundary and necessary model extensions are explicit. |
| 04a:6–11 | Methods/theory | A; A×7 | clean (1 named external relation cited) | clean (“With the input voltage source shorted...” establishes condition) | All-resistor temperature and finite band explicit. |
| 04a:29 | Methods/noise interpretation | A; A×4 | clean (0 external claims) | clean (“The last column” points to immediately preceding table) | Bit comparison explicitly distinguished from converter ENOB. |
| 04a:31–37 | Methods/theory | A; A×4 | clean (0 external claims) | clean (“For small additive output fluctuations” states approximation) | Covariance and independent-noise caveats retained. |
| 04a:41 | Results | A; A×5 | clean (0 external claims) | clean (“For the P/Q pair at g=0.1” defines comparison) | Absolute residual accompanies CMRR. |
| 04a:43 | Discussion/model limits | A; A×5 | clean (0 external claims) | clean (“As g→∞” names limit) | Detectability conditional on experimental terms. |
| 04a:49 | Methods | A; A×6 | clean (0 external claims) | clean (“Three synthetic populations” defines subject) | Population definitions include component range caveat. |
| 04a:51 | Results | A; A×4 | clean (0 external claims) | clean (“For 5000 samples per population” points to defined populations) | Nominal rejection and ideal-trimming limitation clear. |
| 04a:53 | Mixed theory/Discussion | C; A,C,A,A,A,A | clean (0 external claims) | clean (“Same-direction scaling” has antecedent) | Separate scaling formulae from explanatory/manufacturing interpretation as above. |
| 05-discussion:3 | Discussion | A; A×5 | clean (0 external claims) | clean (“The operating termination and calibration convention” names subject) | Read “two distinct known terminations” under preceding raw convention; add “under raw matching” if avoiding any ambiguity. No mandatory language defect. |
| 05-discussion:5 | Discussion/design implication | A; A×5 | clean (0 external claims) | clean (“The coefficient representation” refers to theory) | Direct imperative sequence suits design implication. |
| 05-discussion:7 | Discussion | A; A×4 | clean (2 external attribution claims, both cited) | clean (“Casas and Pallàs-Areny” names subject) | Literature comparison remains bounded to topology. |
| 05-discussion:9 | Discussion | A; A×5 | clean (0 external claims) | clean (“Strict component positivity” names condition) | Example illustrates stated loss of identification. |
| 05-discussion:13 | Discussion | A; A×4 | clean (0 external claims) | clean (“Direct-current calibration” names subject) | Criterion distinction explicit. |
| 05-discussion:15 | Discussion | A; A×5 | clean (0 external claims) | clean (“For changing resistance” names case) | Same bounded design objectives throughout. |
| 05-discussion:17 | Discussion | A; A×4 | clean (0 external claims) | clean (“The two-load result” points to derived result) | Conditional experimental implication. |
| 05-discussion:21 | Discussion/limitations | A; A×2 | clean (0 external claims) | clean (“The evidence in this paper” names subject) | Long list is concrete and parallel. |
| 05-discussion:23 | Discussion/limitations | A; A×2 | clean (0 external claims) | clean (“Dynamic validation additionally” has bench-validation antecedent) | Requirements and detection limit stated directly. |
| 06-conclusions:3 | Conclusions | A; A×6 | clean (0 external claims; own use of extraction) | clean (“Using classical ... we classified” identifies study action) | Exact-response restriction survives summary. |
| 06-conclusions:5 | Conclusions | A; A×5 | clean (0 external claims) | clean (“For calibrated ratio measurements” names case) | No new future-work claim. |
| fig11-en.tex:4 caption | Figure caption | A; A×3 | clean (0 external claims) | clean (“Signal flow for the buffered ratio model” names subject) | Model plane and source amplitude stated directly. |
| fig12-en.tex:4 caption | Figure caption | A; A×3 | clean (0 external claims) | clean (“Two consequences of channel differences” names subject) | Language admissible. Prefer math notation $\ast$ and $\hat R$ over literal “*”/“R_est” if they match displayed figure; no language downgrade. |
| fig13-en.tex:5 caption | Figure caption | A; A×4 | clean (0 external claims) | clean (“Synthetic pairing populations at g=0.1” names subject) | Population conditions and plotted summaries explicit. |
| fig14-en.tex:5 caption | Figure caption | A; A×4 | clean (0 external claims) | clean (“Termination sweep of the P/Q construction” names subject) | Infinite-CMRR omission and attenuation caveat explicit. |

Share: A 61 · B 1 · C 2 · D 2 (66 paragraph/caption units); A|B = 93.94%. A/B units ship; the four C/D units require repair and re-review. Numerical sentence counts are reading aids, not quantitative gate results.

Ceiling note: veto / slot-gaps not available; lint gate not run by this reviewer. Missing same-sentence provenance citations and Results/Discussion mixing are semantic checks, so no mechanized detection is claimed.

Old unchanged issues: none elevated to a mandatory new repair on this axis. Numerical equality, estimator validity, bit-reference planes and whether primary texts support historical synthesis attributions require the other relevant verification process; this report does not silently grade those facts as externally verified.

Unresolved: the section standards are calibrated to empirical geotechnical papers. Applying “Methods must not claim a result” literally to theorem/proof paragraphs would prohibit their basic function; this review treats exact derivation as theoretical exposition and applies the Results/Discussion boundary to reported evaluations, where it has an observable criterion. This interpretation is stated rather than used as an unstated taste rule.

## Repair re-review — current verdict supersedes the initial defects above

Scope limited as requested to the original B/C/D units, their relocated text, and the two revised abstract sentences. Current source was reread; no source files changed. The reported lexical gate (493 sentences, zero hits) was not used as a substitute for review. Lee provenance is assessed against the parent-supplied verified abstract description: classical continued-fraction synthesis/chain-matrix decomposition; no RC-specific theorem or full-text priority claim is inferred.

| Unit/current location | Functional section | Current class; sentence grades | Citation scan | Opening scan | Re-review finding |
|---|---|---|---|---|---|
| 00-related-work.tex:15 | Introduction | B; A,A,A,B,A | clean (3 external provenance/attribution sentences, all carry citations, including lee1978chain on the tools statement) | clean (“Guillemin” names subject) | Original D fixed. Surface antecedent remains after replacement: “We use that representation” now follows two named tools rather than a named representation. Change to “We use these tools” or “We use a chain-matrix representation”. This is B, not a claim correction (L6 anaphora). |
| 02a-general-order-theory.tex:28–33 | Methods/theory | A; A×4 | clean (both continued-fraction provenance statements carry lee1978chain in the same sentence) | clean (“With the source shorted” refers to defined circuit) | Original D fixed. The present RC coordinate expression is identified as this work's expression of the synthesis approach. No unsupported RC-specific historical theorem is stated. |
| 03a-dynamic-ratio-and-transient-leakage.tex:113 | Results | A; A×8 | clean (0 external provenance/prevalence claims) | clean (“Six baseline ... cases” names tests) | Original B fixed: “signed tracking errors” is consistent with negative values; closing sentence now uses the same term. |
| 03a-dynamic-ratio-and-transient-leakage.tex:115 | Results | A; A×7 | clean (0 external provenance/prevalence claims) | clean (“Two constant-resistance cases” names tests) | Original C and RMS wording fixed. RMS now modifies the residual explicitly; causal explanation removed; comparison conditions and baseline are retained. |
| 05-discussion.tex:21 relocated scaling paragraph | Discussion | A; A×6 | clean (0 external provenance/prevalence claims) | clean (“Same-direction scaling” names the operation defined in the pairing models) | Original 04a:53 C fixed by placement: perturbation mechanism and manufacturing limits now perform Discussion's job. |
| 05-discussion.tex:23 relocated approximation explanation | Discussion | A; A×2 | clean (0 external provenance/prevalence claims) | clean (“The reduced sinusoidal residual” points to the reported residual comparison) | Original 03a:115 interpretive sentence now belongs to its section and develops into a bounded design implication. |
| main.tex:27, “Three- and four-stage transient cases checked the history dependence.” | Abstract | A | clean (not applicable: abstract, ER-T19) | clean (sentence names the transient cases) | Bounded description of the checked quantity; no broad validity claim. |
| main.tex:27, “The complete second-moment quotient reduced relative prediction residuals ...” | Abstract | B | clean (not applicable: abstract, ER-T19) | clean (“The ... quotient” has the preceding moment-expansion antecedent within the abstract) | Surface term inconsistency with the body's second-order ratio expression (L5 vocabulary). Use “The second-order ratio approximation reduced relative prediction residuals ...”. The current words “second-moment quotient” could be read as a quotient of moments, which Eq. (second-order-ratio) is not. Values, 100 Hz condition and baseline need no language change. |

Repair re-review share: A 6 · B 2 · C 0 · D 0 across 8 reviewed units; A|B = 100%. No original refusal-level L defect remains. Two surface edits above would bring the re-reviewed units to A. This targeted round does not imply a fresh full-manuscript review, and the initial full-review share remains a historical record rather than the current repair outcome.

Ceiling note: no independent lint count is claimed. Unresolved: no additional rule needed for the targeted repair review. Primary-source truth beyond the supplied Lee abstract verification remains outside this L-only pass.

## Final surface-edit confirmation

Only the two outstanding B items were rechecked; no scope expansion and no source edits.

| Unit | Section | Final class | Citation scan | Opening scan | Closure |
|---|---|---|---|---|---|
| 00-related-work.tex:15, replacement sentence | Introduction | A | clean (present-study action, no external provenance claim) | clean (“We use a chain-matrix representation” explicitly names the representation) | Confirmed exact text “We use a chain-matrix representation to formulate ...”; former ambiguous “that representation” removed. |
| main.tex:28, replacement sentence | Abstract | A | clean (not applicable: abstract, ER-T19) | clean (“The second-order ratio approximation” names the previously introduced approximation) | Confirmed exact text “The second-order ratio approximation reduced ...”; terminology now matches the body's approximation. |

Final targeted repair outcome: A 8 · B 0 · C 0 · D 0 for the eight re-reviewed units. Both outstanding B items are closed. No refusal-level L defects remain within this targeted review. The initial full-review table is retained as historical evidence; it is superseded by these repair dispositions where applicable.
