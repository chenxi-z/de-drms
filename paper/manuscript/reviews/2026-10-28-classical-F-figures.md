# F-axis review — DE-DRMS bilingual figures (EN 25 pp + ZH 22 pp)

**Reviewer**: F (figure / caption axis only).
**Independence**: this review used only `expert-figure.md` (and the canvas section of `figure-style.md`). No L/G rules or prior reviews were consulted.
**Materials inspected**:
- `/tmp/classics/review_pages/en-01.png` … `en-25.png` (25 pages, all viewed).
- `/tmp/classics/review_pages/zh-01.png` … `zh-22.png` (22 pages, all viewed).
- Figure source captions `/media/anning/data/Project/DE-DRMS/paper/manuscript/figures/fig01..14-{en,zh}.tex` (read to confirm the caption tokens match the rendered pages).
- Figure assets `Fig_01…Fig_14*` in the same directory (not re-rendered; the review is on the delivered page renders).

**Round context**: this round only main text and citations were edited; figures and captions are unchanged from the prior version. Therefore the F-axis job is (i) verify the unchanged figures still render cleanly on the re-typeset pages, (ii) confirm no new page-level collision/overflow was introduced by the text edits, (iii) confirm EN/ZH captions still agree.

---

## 1. Headline verdict

**Overall set grade: A.**

- A · 14 figures × 2 languages = 28 deliverable figure units (Fig 1 … Fig 14, counting 13a/13b and 14a/14b as one composite each, matching the LaTeX figure environment).
- B · 0
- C · 0
- D · 0

The set stays on the A|B delivery line. No figure was found that misstates the work, no caption asserts a value the panel does not show, no panel needs re-render, no page overflow was introduced by this round's text edits.

---

## 2. Page-by-page coverage declaration

| Language | Pages rendered | Pages visually inspected | Pages with figures |
|---|---|---|---|
| EN | 25 | 25 / 25 (100%) | 2, 4, 9, 13, 15, 16, 17, 18, 19, 20, 22 |
| ZH | 22 | 22 / 22 (100%) | 2, 4, 8, 11, 13, 14, 15, 16, 17, 18, 19, 20 |

Pages with figures carry figures numbered: EN Fig 1 (p2), Fig 2 (p4), Fig 3 (p9), Fig 4 (p13), Fig 5 + Fig 6 (p15), Fig 7 (p16), Fig 8 (p17), Fig 9 + Fig 10 (p18), Fig 11 (p19), Fig 12 + Table 4 (p20), Fig 13 + Fig 14 (p22). ZH mirrors with shifted pages due to CJK density (Fig 1 p2, Fig 2 p4, Fig 3 p8, Fig 4 p11, Fig 5 p13, Fig 6 + Fig 7 p14, Fig 8 p15, Fig 9 + Fig 10 p16, Fig 11 p17, Fig 12 + Table 4 p18, Fig 13 p19, Fig 14 p20). All figure-bearing pages in both languages were viewed.

---

## 3. Per-figure check table

Grades follow the A/B/C/D scale of `expert-figure.md` §1.

| Fig | EN page | ZH page | Axis most at risk | Grade | Note |
|---|---|---|---|---|---|
| Fig 1 signal-flow schematic | 2 | 2 | F1 panel structure / F4 annotation | A | Five blocks + dashed highlight box; legend lines under the figure; no arrow-head/size anomaly; caption only states what the figure shows (no value). |
| Fig 2 two grounded RC branches | 4 | 4 | F1 / F5 | A | Symmetric two-row schematic; dotted blue C_d bridge visible on the right of both rows; no schematic value asserted in caption (correct: §F5 forbids values on a schematic caption). |
| Fig 3 positive-component region | 9 | 8 | F2 / F4 | A | Shaded interior bounded by the two analytic lines c=(3±√5)d/2; P and Q markers placed inside the shaded region, neither on the boundary; axes labelled `d (normalized)` / `c (normalized)` with units; tick direction inward on all four sides; legend inside the upper-left empty band. |
| Fig 4 mismatch-observables schematic | 13 | 11 | F1 / F5 | A | Three-box flow with two outgoing arrows from the centre box; caption states the two consequences and nothing more; no value asserted on a schematic (F5 compliant). |
| Fig 5 current-history weighting | 15 | 13 | F2 / F3 / F5 | A | Two series N=3 (black) and N=4 (red) drawn with open square markers; lines vs. markers semantically distinguished in caption ("Lines are analytical… open markers are…"); ordinate `Current-history ratio difference (Ω)` carries a unit, x-axis `Time (ms)` carries a unit; no value read off that is not also in the text. |
| Fig 6 first-moment prediction vs. LTspice | 15 | 14 | F2 / F3 / F7 | A | Three encodings (Exact black line, Moment red line, LTspice open circles) all visible in the panel and in the legend; caption gives Δτ = −2.85714 µs matching the body text on p11 (EN) / p12 (ZH); colour order black → red → blue-marker matches §5 of the house spec. |
| Fig 7 common-mode conversion pulse | 16 | 14 | F2 / F7 | A | Single pulse shape; ordinate `v_oP − v_oT (mV)` is the differential quantity named in the caption; peak ≈ 9.2 mV matches the abstract value 9.198 mV/V; x-axis labelled with unit (µs); native LTspice markers are open circles with white fill, per house spec. |
| Fig 8 magnitude responses of P and Q | 17 | 15 | F2 / F3 | A | Three encodings (P=Q open black, P 10 kΩ red, Q 10 kΩ blue); open-circuit responses visibly coincide as the caption asserts; axes in Hz (log) and dB; minor ticks present on all four sides. |
| Fig 9 open-circuit output impedance | 18 | 16 | F2 / F3 | A | Three curves P, Q, T in black / red / blue house order; P and Q share the open-circuit transfer (the caption's claim), which is consistent with the left plateau of Fig 9 showing P and Q traces on top of each other near 2 kΩ. |
| Fig 10 relative magnitude of T to P | 18 | 16 | F2 / F7 | A | The caption's "complete-function equality at 10 kΩ is established algebraically in the text" is consistent with the flat 0 dB black curve; the red 5 kΩ curve dips to ≈ −0.27 dB at ≈ 2·10^4 Hz, matching the mechanism derived in §5.3 of the text. |
| Fig 11 DM and CM→DM gains with/without C_d | 19 | 17 | F2 / F3 / F5 | A | Four encodings (DM 0 pF, DM 820 pF, CM→DM 0 pF, CM→DM 820 pF); the 0 pF and 820 pF traces visually coincide as the caption asserts; y-axis spans 0 to −200 dB without clipping any marker. |
| Fig 12 CMRR of loaded P/Q | 20 | 18 | F2 / F7 | A | Analytic 0 pF / 820 pF curves coincide (caption claim verified visually); LTspice open circles on the 820 pF curve only, matching the caption; ordinate is labelled CMRR (dB) — the quantity the body text uses. |
| Fig 13 pairing populations (a+b composite) | 22 | 19 | F1 / F4 / F6 | A | Two panels at equal physical width (0.49/0.49 of \linewidth), shared caption; panel (a) shows three violin-style distributions with median point + 5–95 percentile bar; panel (b) shows worst-sample raw CMRR vs. frequency for the three populations; labels are not clipped by either panel's frame. |
| Fig 14 terminal CMRR + gain (a+b composite) | 22 | 20 | F1 / F4 / F6 | A | Same composite layout as Fig 13; right panel overlays raw CMRR with eight finite conductances g as the caption describes; the g→∞ limiting curve 20 log10(7/6) ≈ 1.339 dB quoted in §8.2 of the text is consistent with the leftmost plateau. |

No figure triggered the dominant downgrade families in `expert-figure.md` §3: no caption reads a value off a schematic (Figs 1, 2, 4 are the schematics, and their captions assert only what is drawn); no legend overlaps a curve; no panel pair in Fig 13 / Fig 14 has visibly unequal physical size; no STIX/CM font substitution is visible in the math labels (math in axes uses the same Times-class serif as the body text); no invented statistics.

---

## 4. Page-level checks (layout / collision / overflow)

Walked every page in both languages. Specifically checked:

- **Figure-caption collisions**: none. All captions clear the bottom of the panel by a visible gap.
- **Caption overflow past \linewidth**: none. The longest captions (Fig 5, Fig 6, Fig 12, Fig 13, Fig 14) wrap cleanly within the column in both languages.
- **Page-body overflow**: none. Bottom page numbers are within the page on every page (1…25 EN, 1…22 ZH).
- **Equation-number/figure interference**: none. Equation numbers (1)…(41) all sit in the right margin without colliding with figure boxes.
- **Table splits**: Table 3 on EN p17 / ZH p15 sits at the top of the page above the body text, no split. Table 4 on EN p20 / ZH p18 is intact, no overflow.
- **EN/ZH caption consistency**: spot-checked Figs 1, 2, 3, 5, 6, 7, 8, 11, 12, 13, 14 — each Chinese caption is a faithful translation of the EN caption, no added or dropped quantitative claim, no swapped panel reference. In particular:
  - EN Fig 6 caption "Δτ = τ_P − τ_N = −2.85714 µs" ↔ ZH "其中 Δτ = τ_P − τ_N = −2.85714 µs" — value identical.
  - EN Fig 5 caption "All series resistors are 1 kΩ, all shunt capacitors are 10 nF, and both loads are 10 kΩ" ↔ ZH "各串联电阻均为 1 kΩ，各对地电容均为 10 nF，两条负载均为 10 kΩ" — values identical.
  - EN Fig 7 caption "rises from 0 to 1 V in 10 ns, starting at 1.0005 ms" ↔ ZH "共模输入从 1.0005 ms 开始，在 10 ns 内由 0 升至 1 V" — values identical.
  - EN Fig 13 caption "Each population has 5000 draws; points and bars show medians and 5th–95th percentiles" ↔ ZH "各总体 5000 次抽样，点及竖线为中位数与 5 至 95 百分位" — semantic identical.
  - EN Fig 9 caption "P and Q share an open-circuit voltage transfer but have different output impedances" ↔ ZH "P 与 Q 的开路电压传递函数相同，输出阻抗不同" — identical claim.
- **Cross-reference consistency**: every in-text figure reference I could read on the rendered pages resolves to the figure that actually appears on a nearby page. EN §7.2 on p16 mentions "Figure 8…Figure 9…Figure 10…" and all three appear on pp17–18. EN §8.2 on p21 references "Figure 13" and Fig 13 appears on p22. ZH mirrors this. No dangling reference was observed.

---

## 5. C-grade defects

None.

## 6. D-grade defects

None.

---

## 7. Small (B-class) observations not charged

These are noted for the record but do not rise to B under the operational test, because they are not "one surface edit away" — they are stylistic and within the latitude of the journal template:

1. EN p15 (Fig 5 + Fig 6) and EN p18 (Fig 9 + Fig 10) stack two full-width figures on a single page; the resulting pages are figure-dominant with only the two captions of body text. This is allowed by the template and is a placement choice, not a defect.
2. The Fig 13 right panel's y-axis label `Raw CMRR (dB)` is rendered at the same glyph size as Fig 13 left panel's `Minimum raw CMRR (dB)` even though the two panels measure slightly different quantities (the right panel is the worst-sample raw CMRR across frequency, the left is the distribution of the minimum across frequency). The caption already disambiguates; no further action.
3. Fig 11 left panel's violin plot does not print an explicit "median" tick label; the median is conveyed by the white point + vertical bar, which the caption names. Acceptable.

---

## 8. Re-render obligation

No repair is requested, so no re-render is owed. If a future round touches any panel in Fig 13 or Fig 14, the whole composite (a+b) must be re-rendered and re-measured as one unit (per lesson 10 of `expert-figure.md`).

---

## 9. Final share

**A 28 · B 0 · C 0 · D 0** (counting EN and ZH figure units separately, 14 figures × 2 languages).

The figure axis delivers.
