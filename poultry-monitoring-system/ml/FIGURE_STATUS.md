# ML Figure Status — Section 3.9 (Figures 3.12–3.18)

Honest provenance map for the machine-learning figures. **No figure below is
fabricated.** Figures marked *pending* stay as `\pendingfig` placeholders in the
dissertation until the corresponding cell has actually run on real data and
produced the artefact. Fill them only from real outputs.

**Updated 2026-08-29:** Figures 3.12–3.17 are now filled from a real training run.
Every reported number traces to `ML_RESULTS_VERIFIED.md` in the project root, which
is the single source of truth. Do not quote a figure that is not in that file.

| Fig | Dissertation label | Depicts | Produced by | Status |
|---|---|---|---|---|
| 3.11 | `fig:mlpipe` | ML development pipeline | `figures/generated/ml_pipeline.pdf` (diagram) | **Done** (diagram) |
| 3.12 | `fig:classdist` | Dataset class distribution | Real EDA over the assembled data | **Done** — 3,829/974 detection instances; 491 health crops |
| 3.13 | `fig:bboxdist` | Bounding-box size / aspect-ratio | Real EDA over 3,211 boxes | **Done** — median 56 px, median aspect 0.92 |
| 3.14 | `fig:colab` | Colab training environment | Screenshot of a genuine Colab session | **Done** — see caveat below |
| 3.15 | `fig:losscurve` | Training/validation curves | Ultralytics `results.png`, 40-epoch run | **Done** |
| 3.16 | `fig:prcurve` | Precision–recall curve | Ultralytics `PR_curve.png` | **Done** — mAP@0.5 = 0.861 |
| 3.17 | `fig:confmat` | Confusion matrix | Classification stage, held-out crops | **Done** — 66 crops, see caveat below |
| 3.18 | `fig:mlinf` | On-device inference flow | `figures/generated/ml_inference_flow.pdf` (diagram) | **Done** (diagram, verified vs §3.9.15) |

## What was actually trained

| Stage | Dataset | Licence | Classes | Result |
|---|---|---|---|---|
| Detection | Broiler-Net (Zarrat Ehsan & Mohtavipour) | Apache-2.0 | 1 (`chicken`) | P 0.841, R 0.774, F1 0.806, mAP@0.5 0.861, mAP@0.5:0.95 0.395 |
| Classification | Roboflow broiler healthy/sick | CC BY 4.0 | 2 (`Healthy`, `Sick`) | 66/66 held-out crops (see caveat) |

## Two caveats that must travel with these figures

**Figure 3.14 does not show the reported run.** The screenshot is a genuine Colab
session with the project notebook loaded, but its cells are unexecuted and the
visible call specifies `epochs=60`. The reported metrics come from a separate
**40-epoch CPU run**. It is false to write that the reported metrics were produced
on the Colab GPU.

**Figure 3.17's 100% accuracy is not a solved task.** It is 66 crops, a binary and
visually well-separated problem, with residual near-duplication in the source
dataset not fully excludable. Report it only as a ceiling observed on one small
public dataset, never as the system's operating accuracy.

## Substitution against the original methodology

The Elmessery RGB subset proved **not retrievable**: the Mendeley record linked from
the paper carries only the 600 thermal images. The six-class label set
(`healthy, lethargic, open_beak_stress, diseased_eye, slipped_tendon, pendulous_crop`)
was therefore not trainable. The substitutes above demonstrate the pipeline at two
health classes. The six-class mapping contract remains implemented and unit-tested
in `src/` but is **unexercised by a trained model**.

## Genuinely still pending (must NOT be fabricated)

- **Sensor calibration curve** (Fig 3.7, `p01_sensor_calibration.png`): requires bench
  measurement against a reference instrument. No calibration relationship measured.
- **Raspberry Pi inference latency**: ONNX was benchmarked at ~47 ms/frame **on CPU only**.
  Nothing has been measured on Pi hardware.
- **Sample correct/incorrect prediction figures**: not delivered with the run.
- **Locally collected GreenFarms training data**: models use public datasets only.

## On-device pipeline code (Section 3.9.15)

The inference flow in Fig 3.18 is implemented and unit-tested:
`src/deployment/ondevice_pipeline.py` (frame-skip → threshold → N-frame
aggregation → flag / queue-for-review → POST). Runs offline with the mock
detector; swap in `--weights best.pt` after training.
