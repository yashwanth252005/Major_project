"""
DEMO training script.

Why this exists:
  The real BraTS 2021 dataset (~a few GB of .nii.gz volumes) has to be
  downloaded from Kaggle, which this sandbox cannot reach. To let you
  see and test the FULL working pipeline (CNN -> Grad-CAM -> LRP -> SHAP
  -> web app) right now, this script generates synthetic MRI-like brain
  slices: a skull-shaped brain silhouette, with a bright circular "tumour"
  blob randomly placed in half of the images, and no blob in the other
  half. It then trains BrainTumorCNN on this synthetic set.

  Swap this for train_real.py once you've pulled the actual BraTS 2021
  FLAIR data (see README.md, Section 2). The model architecture, saving
  format, and everything downstream (xai.py, main.py, the React app) is
  IDENTICAL either way — only the data source changes.
"""

import os
import random
import numpy as np
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from app.model import BrainTumorCNN

IMG_SIZE = 128
N_SAMPLES = 900
DATA_DIR = "demo_data"
MODEL_OUT = "model_weights.pt"


def make_brain_silhouette(size):
    img = np.zeros((size, size), dtype=np.float32)
    center = (size // 2, size // 2)
    axes = (int(size * 0.38), int(size * 0.46))
    cv2.ellipse(img, center, axes, 0, 0, 360, 0.55, -1)
    # add some texture (gyri-like noise) so it's not a flat blob
    noise = np.random.normal(0, 0.05, (size, size)).astype(np.float32)
    img = np.clip(img + noise * (img > 0), 0, 1)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    return img


def add_tumor_blob(img, size):
    img = img.copy()
    r = random.randint(int(size * 0.06), int(size * 0.13))
    cx = random.randint(int(size * 0.35), int(size * 0.65))
    cy = random.randint(int(size * 0.35), int(size * 0.65))
    overlay = np.zeros_like(img)
    cv2.circle(overlay, (cx, cy), r, 1.0, -1)
    overlay = cv2.GaussianBlur(overlay, (9, 9), 0)
    img = np.clip(img + overlay * 0.5, 0, 1)
    return img


def generate_dataset(n=N_SAMPLES, out_dir=DATA_DIR):
    os.makedirs(os.path.join(out_dir, "tumor"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "notumor"), exist_ok=True)
    for i in range(n):
        base = make_brain_silhouette(IMG_SIZE)
        if i % 2 == 0:
            img = add_tumor_blob(base, IMG_SIZE)
            path = os.path.join(out_dir, "tumor", f"{i}.png")
        else:
            img = base
            path = os.path.join(out_dir, "notumor", f"{i}.png")
        cv2.imwrite(path, np.uint8(img * 255))
    print(f"Generated {n} synthetic demo slices in '{out_dir}/'")


class DemoDataset(Dataset):
    def __init__(self, root):
        self.samples = []
        for label, cls in enumerate(["notumor", "tumor"]):
            cls_dir = os.path.join(root, cls)
            for f in os.listdir(cls_dir):
                self.samples.append((os.path.join(cls_dir, f), label))
        random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
        img = (img - 0.5) / 0.5  # normalize to [-1, 1]
        tensor = torch.from_numpy(img).unsqueeze(0)  # (1, H, W)
        return tensor, torch.tensor([label], dtype=torch.float32)


def train():
    if not (os.path.isdir(os.path.join(DATA_DIR, "tumor"))
            and os.path.isdir(os.path.join(DATA_DIR, "notumor"))):
        generate_dataset()

    dataset = DemoDataset(DATA_DIR)
    n_val = int(0.15 * len(dataset))
    train_ds, val_ds = random_split(dataset, [len(dataset) - n_val, n_val])
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BrainTumorCNN(in_channels=1, input_size=IMG_SIZE).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()

    epochs = 5
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                pred = (torch.sigmoid(model(x)) > 0.5).float()
                correct += (pred == y).sum().item()
                total += y.size(0)

        print(f"Epoch {epoch+1}/{epochs}  train_loss={total_loss/len(train_ds):.4f}  val_acc={correct/total:.4f}")

    torch.save(model.state_dict(), MODEL_OUT)
    print(f"Saved trained weights to {MODEL_OUT}")


if __name__ == "__main__":
    train()
