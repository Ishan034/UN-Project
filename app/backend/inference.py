import torch
from models.cnn_backbone import CNNBackbone
from models.fusion import LayerFusion
from models.predictor import MigrationPredictor

class InferencePipeline:
    def __init__(self, device="cpu"):
        self.device = device
        self.backbone = CNNBackbone(pretrained=False).to(device)
        self.fusion = LayerFusion(in_channels=128, aux_channels=5).to(device)
        self.predictor = MigrationPredictor(in_channels=128).to(device)

        self.backbone.eval()
        self.fusion.eval()
        self.predictor.eval()

    def run(self, image_tensor, aux_tensor):
        with torch.no_grad():
            img_feat = self.backbone(image_tensor)
            fused = self.fusion(img_feat, aux_tensor)
            heatmap = self.predictor(fused)
        return heatmap
