import torch
import torch.nn as nn

class MigrationPredictor(nn.Module):
    """
    Generates a continuous migration probability heatmap.
    Output is later rendered as red → green gradient on the map.
    """
    def __init__(self, in_channels: int):
        super().__init__()
        self.head = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.head(x)
