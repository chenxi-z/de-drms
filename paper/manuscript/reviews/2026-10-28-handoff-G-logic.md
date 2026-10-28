# Independent G-axis review — 2026-10-28

Scope: main.tex abstract; English sections 02a, 03a, 04a; handoff_audit.py and review_extensions.py. Only expert-logic.md was read as expert instructions. No other expert rules, reviews, or handoff reports were read. Source files were not changed. Paragraphs containing displayed equations are judged together with their inferential text. The review records the source state initially read; parent subsequently confirmed that the intended 1.2 V span is at the ladder-output / receiver-input plane.

First break: 04a L15/L29 place the same voltage span at different measurement planes. This is B if corrected to the intended output-plane span (the parent explicitly confirmed that intention); if “input” means ladder source input, the numerical inference is wrong and needs recalculation.

Main substantive remaining break: 04a L49 does not define the synthetic stage-product population uniquely. The sample-generation step must state ladder order, nominal components, and which independently drawn second-branch values are retained while the complementary values are trimmed. This is C, under G2/G3 and DR-548/DR-566, because different admissible generators satisfying the stated product equalities produce different distributions.

## Re-review after author repairs — final G disposition

The original B/C issues below are resolved. Final reviewed disposition: **A 45 · B 0 · C 0 · D 0; A|B=100% — G axis permits delivery within the stated ideal-model scope.** The initial ledger is preserved below as the audit trail; the following grades supersede its rows 36, 39, 43 and 44.

| Original item | Revised evidence | Revised G grade |
|---|---|---|
| 39: noise span plane | 04a L15/L29 now both explicitly put the 1.2 V quantizer span at the ladder output; output noise and quantization variance share a plane. Numeric bits remain correct; ENOB is explicitly excluded. | A |
| 43: population construction | 04a L49 now fixes N=2, unit nominal components, log-uniform reference draws, independent u_j/v_j, and both exponential trimming equations. Product equality follows exactly and the stochastic construction is unique. | A |
| 44: reported population medians | Independently rebuilt second-order transfer denominators and all three population generators in NumPy using SeedSequence(20261028).spawn(8), child streams 0/1/2; did not execute/import the external source. Raw medians 39.1850286892,58.0175244989,33.9570621878 dB and normalized medians 39.5414016897,57.7905279863,34.3269015845 dB reproduce all six manuscript rounded values. | A |
| 36 / calculation certification: crossing | 03a L119 now says crossings, without claiming finalness or persistent settling. review_extensions.py L53 now names the value computed_crossing_10ppm_us. The existing root-finding calculation supports that bounded claim. | A |

The scaling identities and manufacturing-budget boundary previously at 04a L53 were moved to 05-discussion.tex L21. Both identities and their inferential limit remain valid; no manufacturing ranking or equal-cost comparison is inferred from the synthetic results. External pairing_mc.py was read only to identify exact child streams/draw order and confirm the intended generator; no historical outputs were overwritten. The independently calculated values above use direct closed second-order denominators rather than that source's chain recursion.

The new Lee1978 citations at 02a L28/L33 and related-work L15 assign chain-matrix/continued-fraction synthesis to classical work, then limit the present calculation to terminal constraints in the specified topology. That positioning is logically bounded. This review does not certify the unread four-paper general-RC prior-art boundary or a field-wide novelty claim. The publisher DOI could not be reopened through the web tool in this re-review, so no independent full-text verification of Lee1978 is claimed here.

## Initial review (superseded where specified above)

## Paragraph ledger

| # | Link / location | Claim as written | What it rests on | Grade | Missing / mis-directed step | Evidence / repair |
|---|---|---|---|---|---|---|
| 1 | main L27 abstract | Matching dimensions, two-load identification, dynamic history, 84 AC and 8 transient cases | Body theory and case descriptions | A | None in inspected core argument | Exact-vs-numerical scope is explicit; no experimental validation claimed |
| 2 | 02a L6–9 | Positive stages give chain matrix | Series R then shunt C | A | None | Direct multiplication of elementary matrices |
| 3 | 02a L10–16 | Recursive coefficients, degrees, coprimality | Matrix product, determinant one | A | None | det=1 implies a common factor of A,B would divide 1 |
| 4 | 02a L18–24 | A controls open transfer; B exposes output impedance | Terminal equation | A | None | Vin=A Vout+B Iout, Iout=g Vout |
| 5 | 02a L28–33 | Classical Cauer extraction supplies coordinates, not a new synthesis claim | Output looking-back impedance | A | None | z_j=1/[q_j x+1/(r_j+z_{j-1})] |
| 6 | 02a L35–44 | Leading coefficients recover components uniquely | Reverse recurrence | A | None | Highest-power cancellation followed by one-order reduction |
| 7 | 02a L46 | Finite positive realization test | Positive reductions and terminal (1,0) | A | None | Reversing recurrence proves sufficiency; not every arbitrary pair asserted realizable |
| 8 | 02a L48 | Coefficients are local smooth coordinates | Polynomial forward, rational inverse | A | None | Leading coefficients and recovered positivity persist locally |
| 9 | 02a L52 | Open matching leaves N freedoms | Fix N coefficients in 2N-dimensional open domain | A | None | Scaling direction distinguished from full family |
| 10 | 02a L54 | One raw positive resistive load leaves N−1 | N+1 independent affine constraints | A | None | B0 fixed by DC; each A coefficient independently supplies another constraint |
| 11 | 02a L56–60 | One normalized load leaves N; N=1 witness | N normalized coefficients | A | None | q=(r+10)/(11r) gives D/D0=1+10x/11 |
| 12 | 02a L62–66 | N=2 witness has equal normalized response but 16.26 dB raw CMRR | Dcandidate=(7/6)Dref | A | None | Gain quotient gives (1+6/7)/[2(1−6/7)]=13/2 |
| 13 | 02a L70–80 table | Raw/normalized dimensions | Preceding and following proofs | A | None | Open N/N; one load N−1/N; two loads 0/0 |
| 14 | 02a L83–88 | Two raw known loads identify A,B and components | Linear solve in load | A | None | Load separation nonzero; full responses and gain specified |
| 15 | 02a L90 | Two normalized resistive loads also identify | Load-independent leading coefficient fixes proportionality constants | A | None | c1=c2; A(0)=1 then c=1; noisy-estimator limitation present |
| 16 | 02a L94–99 | Rational-load matching kernel | Coprime P,Q | A | None | QΔA=−PΔB implies ΔA=PS, ΔB=−QS |
| 17 | 02a L99–107 | Kernel dimension | Degree and constant-term restrictions | A | None | S has m+1 coefficients, one removed only if P0≠0 |
| 18 | 02a L109–126 | Load-specific counts | Rational kernel | A | None | Capacitor N, resistor N−1, inductor max(N−2,0), RC N−1 checked |
| 19 | 02a L128 | Two rational raw loads identify | Eliminate ΔA | A | None | Nonzero polynomial factor forces ΔB=0 |
| 20 | 02a L132–140 | Load shift leaves zero DC leakage but frequency mismatch | Match at g0 and ΔB0=0 | A | None | Difference of reciprocal denominators has stated sign |
| 21 | 02a L142 | Identifiability does not imply good conditioning | Inversion sensitivity and load separation | A | None | δ(1/H)=−δH/H² |
| 22 | 02a L143 | Unscaled coefficient Jacobian is increasingly ill-conditioned | Explicit dimensionless map | A | None | Recomputed listed values; normalization and estimator caveats stated |
| 23 | 03a L4–8 | Calibrated ratio is quotient of normalized convolutions | Independent ideal buffers, LTI ladders | A | None | Rs and DC gains cancel exactly; prehistory and denominator requirements explicit |
| 24 | 03a L13–22 | Matched response gives history weighting, not instantaneous tracking | Exact subtraction and positive excitation | A | None | Exponential probes give G(α+β)/G(α) |
| 25 | 03a L24–34 | Positive kernel gives moment bound | Metzler nodal state and bounded slope/current | A | None | ∫g=1 and ∫u g=τ; startup denominator handled separately |
| 26 | 03a L39–48 | Mismatch adds current-slew error | Exact decomposition then first moment | A | None | −τP Rdot−R (Idot/I)Δτ |
| 27 | 03a L49–63 | Second moment and second-order ratio | Taylor expansion of numerator and reciprocal denominator | A | None | Independently symbolic-expanded; all terms, including −τNΔτ h², agree |
| 28 | 03a L63–68 | Equal delays do not imply equal kernels; first-order remainder bounded | Explicit unequal μ2 witness, Taylor remainder | A | None | τ/T=31/12, Δμ2/T²=−41/26 checked |
| 29 | 03a L70–74 | Finite-load unit delay and strong-load limit | Unit ladder coefficient sums | A | None | Formula checked N=1…12; N=1 strong-load delay tends to zero |
| 30 | 03a L81–86 | Equality for every constant-R current history iff kernels equal | Arbitrary small perturbation probes | A | None | Necessary/sufficient statement confined to normalized independent model |
| 31 | 03a L91 | Each ladder has simple real negative poles | Irreducible symmetric tridiagonal conductance pencil | A | None | Product may repeat poles; residue limitation explicitly retained |
| 32 | 03a L93–99 | Zero-DC leakage creates decaying step transient with residue energy | Stable rational F, residues of F/s | A | None | a=r/p; step energy differentiated from impulse energy |
| 33 | 03a L101–105 | P/T peak and settling values | Explicit rational F and pole set | A | None | Coefficients and pole set compatible; reported ideal-edge vs ramp distinction clear |
| 34 | 03a L113 | Exponential native cases verify history dependence and lag | Complete-response formula and finite analysis window | A | None | Recomputed −161.0066/−255.7893 Ω; history shifts 5.11377/11.94461 Ω |
| 35 | 03a L115 | Second-order quotient explains leading 100-Hz residual | Exact sinusoidal steady response | A | None | First residuals 5.5928/8.6342%; second 0.22356/0.53176% reproduced |
| 36 | 03a L119 | Fast-step initial +10%; final 10 ppm crossings | Exact step-response quotient | A | None in model argument | +10% follows leading 1/s^N ratio; reported crossings reproduced, but script's “last” label needs stronger verification (below) |
| 37 | 03a L121 | Buffer dynamics can add/cancel delay mismatch | Cascaded normalized transfer moments | A | None | Restriction to independent linear buffers and actual sampling/load plane stated |
| 38 | 04a L6–11 | Output equilibrium thermal spectrum and kT/CN | Johnson–Nyquist, all resistors same temperature | A | None | Independent N1 closed integral 0.606913387 μV agrees; all-band equilibrium follows capacitor energy |
| 39 | 04a L15–29 | Equivalent bits from output noise and 1.2 V “input span” | Ideal quantization variance | B* | One measurement-plane label edit, once intended span is output/receiver-input | Parent confirms output-plane intent; write that consistently. If source-input span retained, bits instead 19.05381,18.97061,18.87960,18.78751 |
| 40 | 04a L31–37 | Ratio covariance and differential common-source noise | First-order additive perturbation | A | None | Correct log-ratio sensitivity; deterministic equality does not eliminate independent thermal noise |
| 41 | 04a L41 | High CMRR can accompany tiny absolute gain | Actual HP,HQ values | A | None | Magnitudes and common-mode residual describe same measurement plane |
| 42 | 04a L43 | Strong-load CMRR tends to 1.339 dB while gains vanish | BP=x+2, BQ=2x+5 | A | None | Independently derived (GDD/GDC)∞=(3x+7)/[2(x+3)]; no universal detection claim |
| 43 | 04a L49 | Synthetic populations defined by correlation constraints | Log-uniform components and product equality | C | Population construction not unique; order absent | State N, nominal values, which random draws survive, and qN=rP qP/rN (if actual method), plus code/data pointer. G3/DR-566 |
| 44 | 04a L51 | Three median comparisons | 5000 draws, 145 points | C | Numerical result cannot be independently reconstructed from L49 alone | Repair generator specification first; then independently reproduce medians. Scope/trimming-cost limitation itself is A. G2/DR-548 |
| 45 | 04a L53 | Same-direction and reciprocal scalings differ; no manufacturing verdict | Scaling identities and explicit caveat | A | None | A(m²x),mB(m²x) verified; conclusion stays within synthetic models |

Share (initial source with confirmed plane intention): A 42 · B 1 · C 2 · D 0; A|B=43/45=95.56%. C paragraphs do not ship until reconstructed. There is no D endpoint to remove.

## Calculation/code audit

Both requested scripts ran successfully under python3; handoff_audit.py reports 41 assertions. review_extensions.py reproduces all reported moment, position, sinusoidal, thermal and coefficient-Jacobian values. In addition, I performed an independent formal quotient expansion: numerator R−ετP(Rdot+hR)+ε²μ2P(Rddot+2hRdot+jR)/2 divided by 1−ετNh+ε²μ2N j/2 exactly yields the manuscript's second-order terms. This tests the general changing-R expansion, whereas review_extensions.py tests only constant-R sinusoidal cases.

- handoff_audit.py L11–24: recurrence and dimensionless moments are correct. They are not an independent proof of all local-dimension or identifiability claims; those claims do have valid manuscript proofs.
- handoff_audit.py L68–70: discriminant check proves the rejected example repeats poles, not the general theorem; manuscript's tridiagonal proof supplies the missing general argument.
- review_extensions.py L48–53: bisection finds one threshold root but by itself does not certify the word “last”. No scan/derivative sign bound excludes subsequent crossings, and only signed error > threshold is tested. Numerical values match; for a rigorous persistent-settling claim add a monotonic-tail or exponential-residue bound / full tail check, or label the computed crossing without claiming global lastness. This is C at the code-certification link, not a demonstrated false manuscript value.
- review_extensions.py L58: bits are calculated from hard-coded noise values rather than the independent integration below. This reproduces the arithmetic but does not independently connect noise integration to bits. Using the newly integrated ladder noises would make the evidence path direct; differences here are just rounding and do not alter values.
- Neither requested derivation script specifies or recomputes the three population medians. The figure generator consumes external verification JSON/CSV, and its wrapper also omits ladder order. Hence population numerical verification remains conditional until the actual generator is referenced.

## Required repairs in order

1. 04a L15/L29: consistently put 1.2 V span at ladder output / receiver input as parent confirmed. Table values then remain correct, and do not imply converter ENOB.
2. 04a L49–51: specify the unique N-stage population generator (including order), point to runnable source/data, reproduce the three raw and normalized medians. Retain current ideal-trimming and selection-budget limitations.
3. For a formally certified “last crossing” at 03a L119, strengthen review_extensions.py L48–53 as above, or weaken that single global-tail claim. No physics/source-model revision is indicated by this review.
