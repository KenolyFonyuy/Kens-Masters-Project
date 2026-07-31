# Changelog — Chapter 2 & Chapter 3 Update

Date: 2026-06-26
Main file: `Dissertation_IoT_AI_Poultry.tex` (single source document — chapters NOT split)
Backup: `backup_before_chapter2_chapter3_update_2026-06-25/`

## Important context (read first)

The folder did **not** contain an existing `.tex` dissertation. It held:
- `WORK.docx` / `chap 1 & 2.docx` — these are a **different student's** dissertation (a cybersecurity / solar-microgrid paper by another author), not this poultry project. They were **left untouched**.
- The genuine poultry LaTeX source existed only as a **read-only** file in imported project knowledge (`IoT_AI_Poultry_Proposal_updated.md`, which is LaTeX despite the `.md` name) — a **project proposal**, not a full dissertation.

With the author's confirmation of the title, the poultry proposal LaTeX was adopted as the base, copied into the folder as `Dissertation_IoT_AI_Poultry.tex`, and expanded in place. Chapter 1, the title page, and all preliminary pages were preserved.

## Preamble (minimal, necessary additions only)

- Added: `amsmath`, `amssymb` (evaluation-metric formulae), `float`, `pdflscape` (landscape hardware table), `adjustbox`, `makecell`.
- Added compile-safe figure macros: `\dedicatedfig` (dedicated-page diagrams), `\inlinefig` (in-text diagrams), `\pendingfig` (evidence placeholders). All use `\IfFileExists` so missing assets never break compilation.
- Made the title-page logo compile-safe (`\IfFileExists{ubalogo.jpg}{...}{box}`).
- Citation system unchanged: in-text author–year + manual `hangparas` APA list. No BibTeX/BibLaTeX introduced.

## Title page (minor consistency corrections only)

- "PROJECT PROPOSAL" → "M.ENG DISSERTATION"; "A Research Proposal Submitted..." → "A Dissertation Submitted...". All other title-page content preserved.

## Chapter 1

- Preserved. No content changes (it already described the confirmed Raspberry Pi / Django / YOLO architecture and was consistent with the new Chapters 2–3).

## Chapter 2 (Literature Review) — expanded

- Rebuilt around the recommended thematic structure (broiler health; environmental factors; traditional monitoring; PLF; IoT in agriculture; IoT poultry monitoring; AI/computer vision; datasets; web FMIS; integration; related systems; comparative analysis; gaps; conceptual framework; synthesis; summary).
- Written as **critical synthesis** across studies rather than study-by-study summary.
- **10 comparison tables** added (environmental parameters; environmental-monitoring approaches; IoT poultry systems; Raspberry Pi vs microcontroller; CV studies; YOLO vs EfficientNet; datasets; FMIS approaches; research gaps; literature→design synthesis).
- Dataset discussion added: Elmessery et al. (2023) broiler pathological phenomena (RGB subset) with its six visible classes; Broiler-Net (Zarrat Ehsan & Mohtavipour, 2024) for inactivity/huddling/gathering/movement; local-data supplementation factors; project-facing labels (`normal`, `inactive_or_lethargic`, `open_beak_distress`, `huddling`, `mobility_abnormality`, `visible_physical_abnormality`, `uncertain`); framed as early-warning aid, not diagnosis.
- Conceptual-framework figure placed on a dedicated page.
- New verified citations integrated: Astill (2020), Redmon (2016), Tan & Le (2019), Elmessery (2023), Zarrat Ehsan & Mohtavipour (2024), Howard (2017), plus canonical He (2016), Lin (2014), Liu (2016), Jocher (2023).
- **Result: ~26 pages** (target ≥25).

## Chapter 3 (Materials and Methods) — corrected, expanded, completed

- **Architecture corrected.** The original draft described the *excluded* ESP32 / Node.js / React / MySQL / MQTT / four-layer-cloud / MQ-137 / sound-sensor design. This was **replaced** with the confirmed direction: Raspberry Pi 4/5; DHT22; MQ135 (ammonia-risk indicator) via MCP3008/ADS1115 ADC; USB/Pi camera; relay-controlled fan and heater; local buffering; Python/OpenCV/Colab; pretrained YOLO (+ optional EfficientNet); TFLite/ONNX/NCNN; Django + DRF; PostgreSQL; Bootstrap; REST over HTTPS.
- Full methods structure implemented: research design; study area; requirements elicitation; functional/non-functional/hardware/ML/software/integration requirements; materials (3 tables incl. landscape hardware table with spec/qty/function/interface/justification/limitation/alternative); iterative model (with per-iteration table); hardware methodology (incl. **proposed, validation-subject** GPIO table — no invented final pins); ML methodology (two-stage detection+classification, EDA, leakage-safe splitting, transfer learning, export/quantisation); web methodology (roles, modules, UML, ERD, REST, testing); three-subsystem integration (18-step data flow); evaluation **formulae** (accuracy, precision, recall, specificity, F1, IoU, mAP@0.5, mAP@0.5:0.95, FPR/FNR, FPS) with classification-vs-detection applicability stated; reliability; security; safety; ethics; assumptions; limitations.
- Flock-balance rule and non-negative-balance business rules included.
- Explicit statements: Raspberry Pi has **no native analogue input → ADC required**; MQ-series treated as gas/ammonia-**risk** indicator, not a selective meter.
- **No fabricated results** — all accuracy/measurement/screenshot/photo evidence replaced by placeholders; results reserved for Chapter 4.
- **Result: ~40 pages** (target 30–40).

## Chapter 4 (Expected Outcomes) — removed

- The proposal's forward-looking "Expected Outcomes" chapter (built on the excluded architecture, and containing anticipatory performance claims) was removed. Chapter 4 is reserved for actual results after implementation, consistent with the brief.

## Appendices & references

- Gantt and Budget relabelled as **Appendix A** and **Appendix B**.
- Budget updated to the **confirmed bill of materials** (Raspberry Pi, MQ135, ADC, webcam, relay, fan, heat lamp, PSU, protection, reference instruments) — old ESP32/MQ-137/sound/cloud-VPS/SMS items removed.
- References expanded and de-duplicated; all entries cited; APA 7th maintained.

## Diagrams

- **20 original monochrome vector (PDF) diagrams** generated (Graphviz + matplotlib; PlantUML host is blocked in this environment, so equivalent StarUML-like monochrome styling was used). Sources saved in `figures/diagram_sources/`.
- Major diagrams (conceptual framework, overall architecture, ERD, deployment) placed on dedicated pages; the hardware materials table uses a landscape page.

## New report files

`SOURCE_VERIFICATION.md`, `PENDING_EVIDENCE_REGISTER.md`, `CHANGELOG_CHAPTER2_CHAPTER3.md`, `COMPILATION_REPORT.md`.

---

## Revision 2 (2026-06-26) — review feedback

- **Em-dashes removed:** all 63 em-dashes (`---`) in Chapters 2–3 replaced with commas/parentheses (prose) or en-dashes (table N/A cells). En-dashes in number/page ranges and terms like "precision–recall" were preserved.
- **UBa logo added:** `ubalogo.jpg` installed in the project root and now renders on the title page (was a placeholder box).
- **Diagrams made vertical:** the four diagrams the review flagged (then numbered 3.2 iterative lifecycle, 3.8 ML pipeline, 3.12 alert state, 3.17 component) were regenerated in top-to-bottom (vertical) layout.
- **Figure 3.3 / 3.4:** the complete-workflow diagram (was hard to spot) and the overall-architecture diagram are now each placed on their own dedicated single page.
- **Placeholders repositioned:** the 11 pending-evidence placeholders were moved out of the end-of-chapter cluster to **inline** positions at the exact subsection where each is discussed; figure numbering is therefore now chronological with the text. Expected filenames renamed to a chronological scheme (`p01_…` … `p11_…`); register table (Table 3.x) and `PENDING_EVIDENCE_REGISTER.md` updated to match.
- **Table 3.2 (ML materials):** material/tool column narrowed (fixed 3.3 cm) and the role column widened (flexible) for better balance.
- **Hardware design/build detailed:** added a signal-level wiring & connection schedule (new table), expanded electrical-interface detail (DHT22 pull-up, MCP3008/ADS1115 buses, active-low opto-isolated relay drive, snubber for the inductive fan, common ground), a power-budget subsection, and a three-stage build-and-assembly procedure (breadboard → soldered board → enclosure) with bring-up tests.
- **Recompiled:** 93 pages, 0 errors, 0 undefined references, 0 missing files, 0 duplicate labels.
- **Note:** the original `Dissertation_IoT_AI_Poultry.pdf` was locked (open in a viewer) at write time, so the updated PDF was saved as `Dissertation_IoT_AI_Poultry_UPDATED.pdf`. The `.tex` was updated in place. Close the old PDF and recompile (or rename) to consolidate to one file.
