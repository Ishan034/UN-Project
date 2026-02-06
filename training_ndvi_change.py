"""
CNN Training with NDVI-change Labels (STABLE VERSION)
---------------------------------------------------
Fixes NaN loss by:
- Cleaning NaNs/Infs
- Robust NDVI-change labeling
- Safe value clamping
"""

from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent
TENSOR_DIR = PROJECT_ROOT / "data/tensors"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "ndvi_change_cnn.pt"

# =========================
# DATASET
# =========================
class TileDataset(Dataset):
    def __init__(self, tensor_dir: Path):
        self.files = sorted(tensor_dir.glob("tile_*.pt"))
        if len(self.files) == 0:
            raise RuntimeError("No tile tensors found")

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        x = torch.load(self.files[idx]).float()  # [2, 64, 64]

        # 🔧 CLEAN INPUT
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        x = torch.clamp(x, 0.0, 1.0)

        # NDVI channel
        ndvi = x[0]

        # 🔧 ROBUST NDVI-change proxy
        mean_ndvi = ndvi.mean()
        label = ndvi - mean_ndvi

        # Clamp label to avoid exploding gradients
        label = torch.clamp(label, -1.0, 1.0)

        return x, label.unsqueeze(0)

# =========================
# MODEL
# =========================
class MigrationCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(2, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 1, 1)
        )

    def forward(self, x):
        return self.net(x)

# =========================
# TRAINING
# =========================
def train():
    dataset = TileDataset(TENSOR_DIR)
    loader = DataLoader(
        dataset,
        batch_size=8,
        shuffle=True,
        drop_last=True
    )

    model = MigrationCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    print(f"Training on {len(dataset)} tiles")

    for epoch in range(5):
        total_loss = 0.0
        valid_batches = 0

        for x, y in loader:
            pred = model(x)
            loss = loss_fn(pred, y)

            if torch.isnan(loss):
                continue  # safety net

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            valid_batches += 1

        avg_loss = total_loss / max(valid_batches, 1)
        print(f"Epoch {epoch + 1}/5 | Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    train()
