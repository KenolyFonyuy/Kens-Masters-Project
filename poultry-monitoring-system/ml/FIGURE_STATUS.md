# ML Figure Status — Section 3.9 (Figures 3.12–3.18)

Honest provenance map for the machine-learning figures. **No figure below is
fabricated.** Figures marked *pending* stay as `\pendingfig` placeholders in the
dissertation until the corresponding notebook cell has actually run on the real
data and produced the artefact. Fill them only from real outputs.

| Fig | Dissertation label | Depicts | Produced by | Status |
|---|---|---|---|---|
| 3.11 | `fig:mlpipe` | ML development pipeline | `figures/generated/ml_pipeline.pdf` (diagram) | **Done** (diagram) |
| 3.12 | `fig:classdist` | Dataset class distribution | `notebooks/train_yolo11n.ipynb` §6 → `outputs/eda/fig_3_12_class_distribution.png` | **Pending** real EDA run |
| 3.13 | `fig:bboxdist` | Bounding-box size / aspect-ratio (EDA) | `notebooks/train_yolo11n.ipynb` §6 + `01_dataset_eda.ipynb` | **Pending** real EDA run |
| 3.14 | `fig:colab` | Colab GPU training environment | Screenshot of `train_yolo11n.ipynb` §1 output while running | **Pending** — you screenshot it during your run |
| 3.15 | `fig:losscurve` | Training/validation curves | Ultralytics `results.png` → `results/fig_3_15_training_curves.png` (§8b) | **Pending** training |
| 3.16 | `fig:prcurve` | Precision–recall curve | Ultralytics `PR_curve.png` → `results/fig_3_16_pr_curve.png` (§8b) | **Pending** training |
| 3.17 | `fig:confmat` | Confusion matrix | Ultralytics `confusion_matrix.png` → `results/fig_3_17_confusion_matrix.png` (§8b) | **Pending** training |
| 3.18 | `fig:mlinf` | On-device inference flow | `figures/generated/ml_inference_flow.pdf` (diagram) | **Done** (diagram, verified vs §3.9.15) |

## How to fill a pending figure (after your Colab run)

1. Run `notebooks/train_yolo11n.ipynb` in Colab (GPU runtime) end-to-end.
2. The EDA cell writes `outputs/eda/*.png`; the training cell + §8b copy the
   Ultralytics plots into `results/`.
3. Copy the produced PNG to the dissertation's `figures/screenshots/` under the
   filename the placeholder already expects (e.g. `p04_class_distribution.png`,
   `p07_training_curves.png`, `p08_pr_curve.png`, `p09_confusion_matrix.png`,
   `p06_colab_environment.png`), or tell me and I will switch the `\pendingfig`
   to `\dedicatedfig`/`\inlinefig` and recompile.
4. Record the run in `ml/models/MODEL_CARD.md` (dataset version, test metrics,
   export sizes, benchmark host).

## Documented limitation (per project decision)

The Elmessery RGB dataset is retained as the primary dataset. If its Google Drive
folder becomes gated or the full ~10k-image RGB subset proves impractical to
retrieve, that is recorded as an **access limitation**; training-dependent
figures (3.12–3.17) remain pending rather than being filled with any substitute
or synthetic result. See `data/metadata/dataset_info.md`.

## On-device pipeline code (Section 3.9.15)

The inference flow in Fig 3.18 is implemented and unit-tested:
`src/deployment/ondevice_pipeline.py` (frame-skip → threshold → N-frame
aggregation → flag / queue-for-review → POST). Runs offline with the mock
detector; swap in `--weights best.pt` after training.
