# Final F-axis re-review — completed

Final snapshot: generator **2026-10-28 15:13:26.991467961 +0800**, provenance **15:13:32.327493149 +0800**; both mtimes unchanged before/after review. Independently viewed all eight final PNGs again and reread all eight bilingual caption wrappers. Extracted final PDF `Tf` sizes independently, rather than adopting the root agent's measurement. Source hashes remain **6/6 matching**.

| Figure | Axis | Final grade | Final measured / quoted evidence | Spec clause | Repair |
|---|---|---|---|---|---|
| 11 EN/ZH | F1/F4/F5/F7 | A | Both 2800×1240 px; minimum SVG text 17 px. `R_est(t)` renders correctly in both languages. Analysis plane, upstream sensor-amplitude statement and output-plane loading remain consistent. No tofu, wire-through-text or clipping observed. | F4/F5/F7; repository schematic requirements | None |
| 12 EN/ZH | F1/F4/F5/F7 | A | Both 2800×1240 px; minimum SVG text 17 px. `R_est` formula renders correctly. Both captions now use LaTeX `$\ast$` and `$R_{\mathrm{est}}$`; separate observable models and nonzero denominator remain explicit. No visible collision. | F4/F5/F7 | None |
| 13 a/b + EN/ZH captions | F1–F7 | A | Equal panels **1575×1126 px**; borders (0,0,35,80)/(0,0,0,0). PDF glyph floors **6.5/5.11 pt**. Caption statistics and synthetic population constraints remain correct. Legend sits above curves. | figure-style §3, §11.2; F5/F7 | None |
| 14 a/b + EN/ZH captions | F1–F7 | **A** | Equal panels **1611×1137 px**; borders (32,7,0,0)/(0,0,0,0). PDF glyph floors now **5.11/5.11 pt**, replacing the initial 4.55/4.2 pt. Both legends visibly show plain `1e6` and remain clear of curves. Both captions explicitly specify **Cd=0** and omit g=0 with a reason. | figure-style §3, §11.2; F5/F7 | Initial B surface issue repaired and verified |

Final grade share: **A4 · B0 · C0 · D0**. Initial B is retained below as historical evidence, not the current verdict. Shared-crop whitespace follows panel equality priority; neither panel is required to have separate zero borders. No visually observed tofu, wire/text crossing, legend/curve overlap or clipped label in the final eight PNGs. Caption/model consistency remains satisfactory. No repository files modified by this reviewer.

---

# Initial review (superseded only by the final re-review above)

# Independent F-axis review — Fig. 11–14

Reviewed 2026-10-28 (Asia/Shanghai), read-only repository review. Read expert-figure.md first; did not read other experts, reviews/, or handoff reports. Actually viewed all eight required PNGs, read all eight bilingual caption wrappers, latest generator, provenance, and relevant manuscript equations. Report is the only file written.

Generator actually located at `paper/manuscript/tools/generate_review_figures.py` (not root tools/). Its mtime at initial and final reads: **2026-10-28 15:03:17.529570877 +0800**; provenance mtime 15:03:22.988487166. These findings apply to that rendered snapshot; later regeneration needs another check.

| Figure | Axis | Grade | Defect, named | Measured / quoted evidence | Spec clause | Repair |
|---|---|---|---|---|---|---|
| 11 EN/ZH | F1/F4/F5/F7 | A | No observed collision or caption/model contradiction | Both 2800×1240 px. SVG minimum text 17 px (34 px in @2x PNG). Border EN (68,54,68,122), ZH (68,52,68,126). Six blocks; analysis frame encloses only RC ladders; captions place loading/probes at the output and resistance upstream, matching the illustrated plane. No tofu or wire-through-text observed. | F4 annotation furniture; F5 schematic caption; F7 honesty; repository AGENTS schematic layout/font requirements | None |
| 12 EN/ZH | F1/F4/F5/F7 | A | No observed collision or caption/model contradiction | Both 2800×1240 px. SVG minimum text 17 px. Border EN (78,54,98,90), ZH (78,52,98,92). Two distinct output blocks. `GDC = HP − HN` and normalized-kernel quotient agree with manuscript section 03a; captions define convolution and estimate. Equal-DC-gain condition is printed next to decaying pulse. No tofu or line/text collision observed. | F4; F5; F7; repository AGENTS schematic layout/font requirements | None |
| 13 (a,b), EN/ZH captions | F1–F7 | A | No delivery defect observed | Panels both **1575×1126 px**; borders a=(0,0,35,80), b=(0,0,0,0), acceptable group union crop. Actual PDF font sizes a≥6.5 pt, b≥5.11 pt. Three populations each contain 5000 raw values; three representative curves each have 145 raw frequency points. Legend clear of all three curves; no crop or tofu observed. Caption medians and 5–95% bars match generator percentile operations; synthetic/exact-trimming distinction explicit. | figure-style §3, §6, §11.2; F5 statistics; F7 honesty | None |
| 14 (a,b), EN/ZH captions | F6/F5 | **B** | **Legend exponent below 5 pt glyph floor** | Panels both **1611×1137 px**; borders a=(32,7,0,0), b=(0,0,0,0). Decompressed delivered PDF text commands contain `4.55 Tf` in a and `4.2 Tf` in b, from `10^6` legend exponent (legend base sizes 6.5 and 6.0). Minimum logarithmic tick exponent elsewhere is 5.11 pt. Eight finite g values match caption: .01,.05,.1,.2,.5,2,10,1e6. Both legends occupy visually empty bands. Caption omits g=0 with explicit reason and correctly distinguishes rejection from attenuation. | **figure-style §3: “no glyph below 5 pt”**; expert F6 export/lettering | Single shared surface edit: print last legend label as plain `1e6` instead of math `10^6`, or raise that label's superscript to ≥5 pt. Re-render and verify both panels. |

## Measurements and provenance

Borders above are independently computed with PIL white-background ink bounding boxes, ordered **left, top, right, bottom**. Equal-panel size takes priority over each member's zero border under figure-style §11.2, so the residual margins in 13a/14a are **not defects**. Diagram whitespace and Noto Sans CJK SC follow the explicit repository schematic requirements, which override the generic chart Times/4:3 rules for these explanatory diagrams.

PDF font sizes were independently extracted from decompressed content streams (`Tf` operators) for all four numerical panels; no reliance on eyeballing the typeface. Times New Roman family also appears in Poppler output. The artwork has editable-text SVG counterparts and matching PDF assets.

All **6/6 source SHA256 values independently match** review-provenance.json. Histogram population counts and representative-curve row counts independently match the captions. Terminal CSV contains g=0 and eight finite values, matching the omission policy and plotted series. Neither captions nor figures claim laboratory measurements. No fabricated uncertainty/statistics detected.

Collision findings: **0 visually observed** tofu glyphs; **0 visually observed** wire-through-text defects; **0 visually observed** legend/curve overlaps; **0 visibly clipped** labels in the eight PNGs. This is an artwork review, not a claim of exhaustive glyph-intersection automation. Tick sides/directions and one minor interval were visibly consistent in numerical panels. Superscript floor is the one measured exception.

## Grade share and rerender obligation

Per figure: Fig11 A1·B0·C0·D0; Fig12 A1·B0·C0·D0; Fig13 A1·B0·C0·D0; Fig14 A0·B1·C0·D0.

Set: **A3 · B1 · C0 · D0** (four figure groups; bilingual versions reviewed together). All meet the A|B delivery line; Fig14 has one remaining surface correction.

After the Fig14 label correction, regenerate both 14 panels, re-extract font minima, verify equal sizes, and visually confirm both legends. If a shared helper rather than the label changes, rerun the whole shared template set under lesson 10. No manuscript/model change is requested.
