"""Optional EfficientNet classification baseline on bird crops.

This is an EXPERIMENTAL comparison, not the production pipeline. It expects
crops derived from verified bounding boxes laid out as
crops/{train,val,test}/{class}/*.jpg. Lazy torch import.

Usage: python -m src.training.train_efficientnet --data crops --epochs 15
"""
from __future__ import annotations

import argparse
from pathlib import Path


def train(data_dir: str, epochs: int, imgsz: int, batch: int, lr: float):
    import torch  # lazy
    from torch import nn
    from torch.utils.data import DataLoader
    from torchvision import datasets, models, transforms

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tf = transforms.Compose([
        transforms.Resize((imgsz, imgsz)),
        transforms.ToTensor(),
    ])
    train_ds = datasets.ImageFolder(Path(data_dir) / "train", transform=tf)
    val_ds = datasets.ImageFolder(Path(data_dir) / "val", transform=tf)
    train_dl = DataLoader(train_ds, batch_size=batch, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=batch)

    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(train_ds.classes))
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()
        # validation accuracy
        model.eval(); correct = total = 0
        with torch.no_grad():
            for x, y in val_dl:
                x, y = x.to(device), y.to(device)
                correct += (model(x).argmax(1) == y).sum().item(); total += y.numel()
        print(f"epoch {epoch + 1}/{epochs} val_acc={correct / max(total, 1):.3f}")
    return model


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="Folder with train/val/test ImageFolders")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--imgsz", type=int, default=224)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()
    if not Path(args.data).exists():
        raise SystemExit(f"Crops directory not found: {args.data}")
    train(args.data, args.epochs, args.imgsz, args.batch, args.lr)


if __name__ == "__main__":
    main()
