# Pending Evidence Register

All implementation evidence below is represented in the dissertation by **compile-safe placeholders**.
Each placeholder auto-renders the real image the moment the file is dropped into the stated folder — **no LaTeX editing is required**.
Actual results/screenshots/photographs belong in **Chapter 4** (Results), to be created after implementation.

Folders (already created in the project):
- `figures/screenshots/` — web app screenshots and ML plots (`.png`)
- `figures/photos/` — hardware photographs (`.jpg`)

Capture method legend: SS = screen capture; CAM = camera photograph; PLOT = exported from analysis notebook.

## 1. Web application (folder: `figures/screenshots/`, intended Chapter 4 / §3.11 design context)

| Artefact | Expected filename | Capture | Status |
|----------|-------------------|---------|--------|
| Login page | `web_login.png` | SS | Pending user upload |
| Dashboard | `web_dashboard.png` | SS | Pending user upload |
| Farm management | `web_farms.png` | SS | Pending user upload |
| Pen management | `web_pens.png` | SS | Pending user upload |
| Batch management | `web_batches.png` | SS | Pending user upload |
| Chick-entry form | `web_chick_entry.png` | SS | Pending user upload |
| Mortality form | `web_mortality.png` | SS | Pending user upload |
| Feed form | `web_feed.png` | SS | Pending user upload |
| Health form | `web_health.png` | SS | Pending user upload |
| Treatment form | `web_treatment.png` | SS | Pending user upload |
| Vaccination page | `web_vaccination.png` | SS | Pending user upload |
| Inventory | `web_inventory.png` | SS | Pending user upload |
| Expenses | `web_expenses.png` | SS | Pending user upload |
| Sales | `web_sales.png` | SS | Pending user upload |
| IoT monitoring | `web_iot.png` | SS | Pending user upload |
| Environmental charts | `web_charts.png` | SS | Pending user upload |
| AI prediction review | `web_ai_review.png` | SS | Pending user upload |
| Alert resolution | `web_alert.png` | SS | Pending user upload |
| Reports | `web_reports.png` | SS | Pending user upload |
| Responsive mobile view | `web_mobile.png` | SS | Pending user upload |

## 2. Machine learning (folder: `figures/screenshots/`, intended Chapter 4 / §3.10 design context)

| Artefact | Expected filename | Capture | Status |
|----------|-------------------|---------|--------|
| Dataset sample grid | `dataset_grid.png` | PLOT | Pending user upload |
| Class-distribution chart | `class_distribution.png` | PLOT | Pending user upload |
| Image-size distribution | `image_size_dist.png` | PLOT | Pending user upload |
| Annotation examples | `annotation_examples.png` | PLOT | Pending user upload |
| Bounding-box distribution | `bbox_distribution.png` | PLOT | Pending user upload |
| Training/validation losses | `training_curves.png` | PLOT | Pending user upload |
| Precision–recall curve | `pr_curve.png` | PLOT | Pending user upload |
| Confusion matrix | `confusion_matrix.png` | PLOT | Pending user upload |
| Correct predictions | `pred_correct.png` | PLOT | Pending user upload |
| False positives | `pred_fp.png` | PLOT | Pending user upload |
| False negatives | `pred_fn.png` | PLOT | Pending user upload |
| Raspberry Pi inference | `pi_inference.png` | SS/CAM | Pending user upload |
| Google Colab environment | `colab_environment.png` | SS | Pending user upload |
| Model export | `model_export.png` | SS | Pending user upload |
| Sensor calibration plot | `calibration_plot.png` | PLOT | Pending user upload |

## 3. Hardware (folder: `figures/photos/`, intended Chapter 4 / §3.9 design context)

| Artefact | Expected filename | Capture | Status |
|----------|-------------------|---------|--------|
| Raspberry Pi and components | `pi_components.jpg` | CAM | Pending (component stock photos already supplied as Fig. 3.5) |
| Breadboard prototype | `breadboard_prototype.jpg` | CAM | Pending user upload |
| Completed circuit | `completed_circuit.jpg` | CAM | Pending user upload |
| DHT22 wiring | `dht22_wiring.jpg` | CAM | Pending user upload |
| Gas sensor & ADC wiring | `gas_adc_wiring.jpg` | CAM | Pending user upload |
| Relay wiring | `relay_wiring.jpg` | CAM | Pending user upload |
| Fan & heater installation | `fan_heater_install.jpg` | CAM | Pending user upload |
| Protective enclosure | `enclosure.jpg` | CAM | Pending user upload |
| Camera placement | `camera_placement.jpg` | CAM | Pending user upload |
| Sensor placement | `sensor_placement.jpg` | CAM | Pending user upload |
| Calibration setup | `calibration_setup.jpg` | CAM | Pending user upload |
| Installed prototype | `installed_prototype.jpg` | CAM | Pending user upload |
| Field-testing setup | `field_testing.jpg` | CAM | Pending user upload |

**Note:** A subset of these (calibration plot, class distribution, bbox distribution, Colab, training curves, PR curve, confusion matrix, web login, web dashboard, breadboard prototype, installed prototype) are already inserted as rendered placeholder boxes in §3.22 and are referenced from the text; the remainder are registered in Table 3.x of that section. Filenames above are the canonical expected names.

---

## Revision 2 — inline placeholders (chronological filenames)

These 11 placeholders are now embedded **inline** at the subsection where each is discussed (not clustered at the end). Drop the file into the stated path and it renders automatically.

| Fig. | Section | Expected file |
|------|---------|---------------|
| Sensor calibration | §3.9 Sensor Calibration | `figures/screenshots/p01_sensor_calibration.png` |
| Breadboard prototype | §3.9 Iterative Hardware Dev | `figures/photos/p02_breadboard_prototype.jpg` |
| Installed prototype | §3.9 Iterative Hardware Dev | `figures/photos/p03_installed_prototype.jpg` |
| Class distribution | §3.10 EDA | `figures/screenshots/p04_class_distribution.png` |
| Bounding-box distribution | §3.10 EDA | `figures/screenshots/p05_bbox_distribution.png` |
| Colab environment | §3.10 Colab | `figures/screenshots/p06_colab_environment.png` |
| Training/validation curves | §3.10 Model Evaluation | `figures/screenshots/p07_training_curves.png` |
| Precision–recall curve | §3.10 Model Evaluation | `figures/screenshots/p08_pr_curve.png` |
| Confusion matrix | §3.10 Model Evaluation | `figures/screenshots/p09_confusion_matrix.png` |
| Web login | §3.11 UI Design | `figures/screenshots/p10_web_login.png` |
| Web dashboard | §3.11 UI Design | `figures/screenshots/p11_web_dashboard.png` |

The broader catalogue above (additional web forms, dataset grids, prediction samples, wiring/field photographs) remains valid for the rest of the Chapter 4 evidence.

---

## Revision 3 — web screenshots CAPTURED (2026-06-27)

The web-application screenshots have been **captured from the running system** and
placed in `figures/screenshots/`. They render automatically in Chapter 4 (and the
Chapter-3 UI-design placeholders `p10_web_login.png`, `p11_web_dashboard.png`).
Captured with `poultry-monitoring-system/backend/capture_screenshots.py`
(Playwright, logged in as `demo_admin`, seeded demo data).

**Captured (18 files):** `web_login`, `web_dashboard`, `web_farms`, `web_batches`,
`web_mortality`, `web_feed`, `web_health`, `web_inventory`, `web_expenses`,
`web_sales`, `web_iot`, `web_charts`, `web_reports`, `web_ai_review`, `web_alert`,
`web_mobile` (`.png`), plus `p10_web_login`, `p11_web_dashboard`.

**Still genuinely pending (must NOT be fabricated):**
- **Machine-learning plots** (`class_distribution`, `bbox_distribution`,
  `training_curves`, `pr_curve`, `confusion_matrix`, prediction samples,
  `pi_inference`): require the licensed dataset + a trained model. Generate by
  running the ML pipeline (see `poultry-monitoring-system/ml/README.md`).
- **Hardware photographs** (`figures/photos/*.jpg`): require the physical rig;
  the farmer/researcher must photograph the assembled circuit and installation.
- **Sensor calibration plot**: requires bench measurement against a reference.

Chapter 4 reports these as pending rather than asserting them, consistent with the
anti-fabrication requirement.

---

## Revision 4 — ML results and hardware photographs CAPTURED (2026-08-29)

Eight of the nine remaining inline placeholders are now filled with genuine artefacts,
delivered in `ml-1/`. Full provenance and every reported number: `ML_RESULTS_VERIFIED.md`
(that file is the single source of truth; do not quote a figure that is not in it).

**Machine learning — produced by a real training run, no longer pending:**

| Fig. | File | Content |
|------|------|---------|
| 3.12 | `figures/screenshots/p04_class_distribution.png` | Detection instances (3,829 train / 974 val) and health-class crops |
| 3.13 | `figures/screenshots/p05_bbox_distribution.png` | 3,211 boxes; median size 56 px, median aspect 0.92 |
| 3.14 | `figures/screenshots/p06_colab_environment.png` | Genuine Colab session with the project notebook |
| 3.15 | `figures/screenshots/p07_training_curves.png` | box/cls/dfl loss, train vs val, 40 epochs |
| 3.16 | `figures/screenshots/p08_pr_curve.png` | PR curve, mAP@0.5 = 0.861 |
| 3.17 | `figures/screenshots/p09_confusion_matrix.png` | Classification stage, 66 held-out crops |

**Hardware — photographed, no longer pending:**

| Fig. | File | Content |
|------|------|---------|
| 3.9 | `figures/photos/p02_breadboard_prototype.jpg` | Assembled circuit on bench, live reading on screen |
| 3.10 | `figures/photos/p03_installed_prototype.jpg` | Unit deployed inside an operating broiler house (GreenFarms) |

**DHT22 calibration — CAPTURED 2026-08-30:** `figures/screenshots/p01_sensor_calibration.png`
(Fig. 3.7) supplies the DHT22-against-reference comparison: temperature Y = 0.985x + 0.2
(R2 = 0.998) over approx. 16-39 °C, humidity Y = 0.99x + 0.1 (R2 = 0.999) over approx. 23-78 %RH.
This covers the DHT22 only, not the gas sensor.

**STILL genuinely pending (must NOT be fabricated):**
- **Gas-sensor calibration** against a reference ammonia concentration: not measured. The gas
  channel stays a relative risk index throughout.
- **Long-run sensor behaviour** under house conditions, and drift over a production cycle.
- **Raspberry Pi inference latency**: the exported ONNX model was benchmarked at ~47 ms/frame
  **on CPU only**. No measurement has been taken on Pi hardware.
- **Six-class visible-condition performance**: only 1 detection class (`chicken`) and 2 health
  classes (`Healthy`/`Sick`) were trained. The six-class mapping contract remains implemented
  and unit-tested but unexercised by a trained model.
- **Locally collected GreenFarms training data**: the trained models use public datasets
  (Broiler-Net, Apache-2.0; Roboflow healthy/sick, CC BY 4.0), not local imagery.
