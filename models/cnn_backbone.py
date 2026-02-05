import torch
import torch.nn as nn
from torchvision import models

class CNNBackbone(nn.Module):
    """
    Lightweight but robust CNN backbone using EfficientNet-B0.
    Suitable for cloud deployment and near–real-time inference.
    """
    def __init__(self, pretrained: bool = True, out_channels: int = 128):
        super().__init__()
        base_model = models.efficientnet_b0(pretrained=pretrained)
        self.features = base_model.features

        self.projection = nn.Sequential(
            nn.Conv2d(1280, out_channels, kernel_size=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.projection(x)
        return x
