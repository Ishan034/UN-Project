import torch
import torch.nn as nn

class LayerFusion(nn.Module):
    """
    Fuses satellite features with auxiliary raster layers
    (climate, social, political) via channel concatenation.
    """
    def __init__(self, in_channels: int, aux_channels: int, out_channels: int = 128):
        super().__init__()
        self.fusion = nn.Sequential(
            nn.Conv2d(in_channels + aux_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )

    def forward(self, img_features, aux_layers):
        x = torch.cat([img_features, aux_layers], dim=1)
        return self.fusion(x)
