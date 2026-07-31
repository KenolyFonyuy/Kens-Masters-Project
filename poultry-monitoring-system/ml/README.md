# ML Subsystem — Broiler Detection (YOLO)

Object-detection pipeline that localises visible broiler states/abnormalities
from images and video frames. Default model: **YOLO11n** (lightweight, edge-friendly).

> Predictions are **early-warning indicators**, not veterinary diagnosis.

## Install (separate environment from the backend)

```bash
python -m venv .venv-ml
# activate, then:
pip install -r requirements.txt        # ultralytics, torch, opencv, etc.
```

The data tools, class mapping and inference *contract* are import-safe and unit
tested **without** torch/ultralytics:

```bash
pytest          # 9 tests: class mapping, inference payload, label/stat tools
```

## Classes & risk mapping

Trained classes come from the RGB portion of the **Broiler Pathological
Phenomena Dataset (Elmessery et al.)** — verify the licence before downloading.
The class → risk-category/severity map lives in
[`configs/class_mapping.yaml`](configs/class_mapping.yaml) and is shared with the
web app and edge client. Default classes: `healthy, lethargic,
open_beak_stress, diseased_eye, slipped_tendon, pendulous_crop`. Supplementary
classes (`huddling, inactivity, abnormal_gathering`) are documented but **must
not** be trained until labelled data exists. `uncertain` is a review/inference
outcome, not a trained class.

## Workflow

```bash
# 1. Import a verified dataset (records provenance + checksums; preserves originals)
python -m src.data.import_dataset --source /path/to/broiler_rgb --name broiler_rgb --licence <id>

# 2. Verify integrity
python -m src.data.verify_images --dir data/raw/broiler_rgb
python -m src.data.find_duplicates --dir data/raw/broiler_rgb

# 3. Split WITHOUT leakage (group frames by video/session)
python -m src.data.split_dataset --images data/interim/images --labels data/interim/labels \
    --group-by parent_dir --train 0.7 --val 0.15 --test 0.15 --seed 42

# 4. Validate labels + generate the Ultralytics dataset.yaml
python -m src.data.verify_labels --images data/processed/images/train \
    --labels data/processed/labels/train --num-classes 6
python -m src.data.create_dataset_yaml --out data/processed/dataset.yaml

# 5. EDA (CLI + notebooks/01_dataset_eda.ipynb) -> plots in outputs/eda/
python -m src.data.generate_statistics --images data/processed/images/train \
    --labels data/processed/labels/train --out outputs/eda/stats_train.json

# 6. Train (configs/train.yaml; Colab via DATASET_YAML/PROJECT_DIR env vars)
python -m src.training.train_yolo --config configs/train.yaml

# 7. Evaluate on the held-out test split -> outputs/evaluation/
python -m src.evaluation.evaluate_detection --weights outputs/runs/.../best.pt \
    --data data/processed/dataset.yaml --split test

# 8. Export + benchmark (run benchmark ON the Pi for real numbers)
python -m src.deployment.export_model --weights best.pt --format ncnn
python -m src.deployment.benchmark --weights best_ncnn_model --runs 50

# 9. Inference (emits the vision-results API payload; --weights optional -> mock)
python -m src.deployment.inference --weights best.pt --source frame.jpg \
    --device-id PI-001 --pen-code P1 --batch-code B1
```

## Notebooks (`notebooks/`)

`01_dataset_eda`, `02_train_yolo`, `03_efficientnet_baseline` (optional),
`04_evaluate_model`, `05_export_and_benchmark`. They are fully runnable but ship
with **empty outputs and clearly-marked PENDING cells** — no results are
fabricated. Execute them only after preparing real data / training a model.

## What is NOT done here (honest status)

No model has been trained and no metrics, curves, confusion matrices or Pi
benchmarks have been generated, because the dataset and a GPU are not available
in this environment. The code paths that would produce them are implemented and
tested; run them on real data to obtain real numbers.
"""
