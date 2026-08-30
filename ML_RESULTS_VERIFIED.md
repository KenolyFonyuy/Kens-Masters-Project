# Verified ML results — evidence register

Every figure and number below was read directly off the delivered artefacts in `ml-1/`.
**Nothing in this file may be extrapolated, rounded up, or supplemented from memory.**
If a quantity is not listed here, it was not measured and must be reported as not measured.

Date placed in dissertation: 2026-08-29.

---

## 1. Detection stage — YOLO11n

**Data source.** Broiler-Net material of Zarrat Ehsan & Mohtavipour, official repository
`github.com/TaherehZarratEhsan/Chicken-Behavior-Analysis` (Apache-2.0).
Cited in the dissertation at Table 3.3.

| Property | Verified value | Read from |
|---|---|---|
| Annotated frames | 20 (1080p) | p05 title |
| Video segments | 9 | p05 title |
| Annotated birds | 3,211 | p05 title |
| Detection classes | 1 (`chicken`) | p08 legend, data.yaml |
| Train instances (after tiling) | 3,829 | p04 panel (a) |
| Val instances (after tiling) | 974 | p04 panel (a) |
| Median box size sqrt(w*h) | 56 px | p05 panel (a) |
| Median aspect ratio w/h | 0.92 | p05 panel (b) |
| Epochs completed | 40 | p07 x-axis |
| Losses tracked | box_loss, cls_loss, dfl_loss (train + val) | p07 |

**Held-out detection metrics** (evaluated on video segments not seen in training):

| Metric | Value |
|---|---|
| Precision | 0.841 |
| Recall | 0.774 |
| F1 | 0.806 |
| mAP@0.5 | 0.861 |
| mAP@0.5:0.95 | 0.395 |

**Export.** ONNX export benchmarked at ~47 ms/frame **on CPU**.
Raspberry Pi latency was **NOT** measured — remains pending.

**Qualitative.** 172 and 160 birds detected on two unseen frames.

---

## 2. Classification stage — Healthy vs Sick

**Data source.** Roboflow Universe `technicalresearch/broiler-chicken-healthy-and-sick` v1,
**CC BY 4.0**, 505 images, classes `Healthy` / `Sick`, YOLOv11 export.

**Leakage finding (important, report it).** The Roboflow export contains
**3 augmented versions of each source image** (horizontal flip, ±15° rotation, ±25% brightness),
distributed across its own train/valid/test splits. Augmented copies of the same source photo
therefore appeared in both train and test. The leakage-safe splitting rule of Section 3.9.8
(group by source image) detected and corrected this before training.

**Crop counts after the leakage-safe re-split** (total 491):

| Class | train | val | test |
|---|---|---|---|
| Healthy | 176 | 36 | 29 |
| Sick | 183 | 30 | 37 |

**Derived split totals** (arithmetic from the table above, not separately measured):
train 176+183 = 359; val 36+30 = 66; test 29+37 = 66; total 491.

**Held-out test result.** 66 crops, accuracy 100.0% (29/29 Healthy, 37/37 Sick; zero off-diagonal).

**MANDATORY CAVEAT — never report this number without it.**
100% on n=66 is *not* evidence of a solved task. It must be reported with:
(a) the test set is very small (66 crops);
(b) the task is binary and the two classes are visually well separated in this dataset;
(c) despite source-level grouping, residual near-duplication within the original 505 images
    cannot be excluded;
(d) the figure is a ceiling observed on one small public dataset, not a field accuracy,
    and it must not be presented as the system's operating accuracy.

---

## 3. Training environment — READ CAREFULLY

- `figures/screenshots/p06_colab_environment.png` shows a genuine Google Colab session with
  `poultry_ml_training_colab.ipynb` loaded (colab.research.google.com), containing the
  transfer-learning, evaluation-artefact and Pi-export cells.
- **The cells in that screenshot are unexecuted** (`[ ]` prompts, no outputs) and the visible
  call specifies `epochs=60`.
- **The reported run is a different, 40-epoch run, executed on CPU** (p07 shows 40 epochs).
- Therefore: it is FALSE to write that the reported metrics were produced on the Colab GPU.
  Correct framing: the Colab GPU environment was prepared and is shown in Figure 3.14; the
  results reported here come from a 40-epoch CPU run.

---

## 4. Substitution against the original methodology

Section 3.9.2 originally committed to the **Elmessery et al. (2023)** broiler pathological-phenomena
RGB subset and a **six-class** label set
(`healthy, lethargic, open_beak_stress, diseased_eye, slipped_tendon, pendulous_crop`).

**What was actually obtainable.** The Mendeley record linked from that paper carries only the
600 **thermal** images; the RGB subset is not clearly published there. The six-class label set was
therefore **not trainable**. Substitutes used:

| Stage | Dataset actually used | Licence | Classes |
|---|---|---|---|
| Detection | Broiler-Net (Zarrat Ehsan & Mohtavipour) | Apache-2.0 | 1 (`chicken`) |
| Classification | Roboflow broiler healthy/sick | CC BY 4.0 | 2 (`Healthy`, `Sick`) |

**Consequence that must be stated in the dissertation:** the trained system demonstrates the
two-stage pipeline at **two** health classes, not the six visible-condition classes of the original
design. The six-class mapping contract remains implemented and tested in code but is
**unexercised by a trained model**.

---

## 5. Hardware evidence now available

| File | Shows | Fills |
|---|---|---|
| `figures/photos/p02_breadboard_prototype.jpg` | Assembled circuit on bench: Pi, breadboards, relay modules, gas sensor, USB webcam, fan; laptop shows `Environmental_Monitor` code and a live line `Temp: 23.5C, Hum: 65%, Gas: Normal` | Fig 3.9 |
| `figures/photos/p03_installed_prototype.jpg` | Same unit on a bench inside an operating broiler house at GreenFarms, birds visible, webcam on gooseneck mount | Fig 3.10 |

### 5b. DHT22 calibration (added 2026-08-30)

`figures/screenshots/p01_sensor_calibration.png` (Fig 3.7), supplied by the author, plots the
DHT22 against reference instruments. Values read directly off the figure:

| Panel | Range covered | Fitted relationship | R2 |
|---|---|---|---|
| (a) Temperature | approx. 16 to 39 °C | Y = 0.985x + 0.2 | 0.998 |
| (b) Relative humidity | approx. 23 to 78 %RH | Y = 0.99x + 0.1 | 0.999 |

**Scope limit — this figure covers the DHT22 ONLY.** It says nothing about the MQ-series gas
sensor. No reference ammonia concentration was used, so the gas channel has NO absolute
calibration and must continue to be reported as a relative risk index.

**Still pending (do NOT claim):**
- **Gas-sensor calibration** against a reference ammonia concentration: not measured.
- **Raspberry Pi inference latency**: only ~47 ms/frame on CPU was measured.
- **Long-run sensor behaviour** under sustained house heat, humidity and dust, and drift over a
  production cycle: not characterised.
