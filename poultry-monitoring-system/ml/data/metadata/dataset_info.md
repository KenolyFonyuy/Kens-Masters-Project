# Dataset Information — Primary Training Data

> Citable record for Section 3.9.2 of the dissertation. All counts below are as
> reported by the dataset authors; any figures the project derives from the data
> will be **measured on disk** by `src/data/generate_statistics.py` and never
> transcribed by hand. Nothing here is a project result — it is provenance only.

## Primary dataset — Elmessery et al. (2023)

| Field | Value |
|---|---|
| Title | Broiler pathological-phenomena dataset (visual + thermal) |
| Publication | Elmessery, W. M., *et al.* (2023). "YOLO-Based Model for Automatic Detection of Broiler Pathological Phenomena through Visual and Thermal Images in Intensive Poultry Houses." *Agriculture*, 13(8), 1527. |
| DOI | https://doi.org/10.3390/agriculture13081527 |
| Article licence | CC BY 4.0 (MDPI open access) — figures/text reusable with attribution |
| Data source | Public Google Drive folder linked from the paper: `https://drive.google.com/drive/folders/1jj9LKL0d1YDyDez8xrmKWRWd3psFoeZ2` (folder title: "Automatic Detection of pathological phenomena Broiler Based on RGB, Infrared Thermal Imaging and Deep Learning Techniques") |
| Reported size | 10,000 images (RGB + thermal), 50,000 bounding-box annotations |
| Birds | 48 Cobb Avian broilers (male + female, varying ages), research farm, Dept. of Poultry Production, Faculty of Agriculture, Kafrelsheikh University, Egypt |
| Capture | Smartphone cameras (RGB) + thermal camera |
| Download date | _to be filled by the run that actually downloads (recorded automatically in `*_provenance.json`)_ |

### Classes (exact match to `ml/configs/class_mapping.yaml`)

1. `healthy` — healthy broiler
2. `lethargic` — lethargic chicken
3. `open_beak_stress` — stressed, open-beak breathing
4. `diseased_eye` — diseased eye
5. `slipped_tendon` — slipped tendon
6. `pendulous_crop` — pendulous crop

### Modality used by this project

The methodology (Section 3.9) commits to **RGB images only** for edge deployment
on a Raspberry Pi with a standard camera (no thermal sensor). Only the visual/RGB
subset is imported into `data/raw`; the thermal images are **excluded**. This is a
deliberate scope decision, not a data limitation.

### Dataset licence — status

The MDPI **article** is CC BY 4.0. The **image files** are author-shared via the
public Drive folder above; a distinct dataset-level licence file has **not yet been
confirmed**. Action before publication: confirm the dataset's own licence (Drive
folder README / correspondence with the authors) and record it here. Until then,
treat reuse as "author-shared, licence to confirm" and always attribute the paper.

### Access note (documented limitation)

Per the supervisor-facing decision on this project, the Elmessery dataset is retained
as the methodology's primary dataset. If the Drive folder later becomes gated or the
bulk RGB subset proves impractical to retrieve in full, this is recorded as a
**documented access limitation** rather than silently swapped for another dataset;
training-dependent results remain pending until the data is obtained. Candidate
permissively-licensed substitutes were surveyed and are listed below **for
contingency only** — none is in use.

## Contingency substitutes (NOT in use — surveyed only)

| Dataset | Approx. images | Labels | Notes |
|---|---|---|---|
| Roboflow Universe — "Broiler Chicken Healthy and Sick" (TechnicalResearch) | ~209 | bbox | small; healthy/sick only |
| Roboflow Universe — "Healthy and Sick Chicken Detection" | ~1,250 | bbox | RGB, permissive |
| Roboflow Universe — "Chicken Disease Dataset (Fecal)" | ~500 | bbox | faecal-image disease classes (different task) |

Adopting any substitute would require updating **Section 2.7** (literature comparison
table) and **Section 3.9.2** (dataset description) to disclose the change. This has
**not** been done because no substitute is in use.

## Folder layout (already present)

```
ml/
  data/
    raw/        # untouched originals (RGB subset imported here)
    interim/    # after dedup + YOLO-format conversion
    processed/  # images/{train,val,test} + labels/{...} + dataset.yaml
    metadata/   # this file + *_provenance.json (auto-written on import)
  notebooks/    # train_yolo11n.ipynb (end-to-end Colab) + 01..05 modular
  models/       # trained weights + MODEL_CARD.md (after training)
  outputs/      # runs/, eda/, evaluation/  (generated, never committed as truth)
```
