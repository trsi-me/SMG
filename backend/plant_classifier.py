"""EfficientNet plant classifier for inference — no albumentations / training-only deps."""
import torch
import torch.nn as nn
import timm
from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights


class PlantClassifier(nn.Module):
    def __init__(self, num_classes, model_name='efficientnet_b4', pretrained=True):
        super().__init__()
        self.num_classes = num_classes

        if model_name == 'efficientnet_b4':
            try:
                self.backbone = efficientnet_b4(
                    weights=EfficientNet_B4_Weights.IMAGENET1K_V1 if pretrained else None
                )
                self.backbone.classifier = nn.Linear(
                    self.backbone.classifier[1].in_features, num_classes
                )
            except Exception:
                try:
                    self.backbone = timm.create_model(
                        'efficientnet_b4', pretrained=pretrained, num_classes=num_classes
                    )
                except Exception:
                    self.backbone = efficientnet_b4(weights=None)
                    self.backbone.classifier = nn.Linear(
                        self.backbone.classifier[1].in_features, num_classes
                    )
        elif model_name == 'resnet50':
            from torchvision.models import resnet50, ResNet50_Weights

            self.backbone = resnet50(
                weights=ResNet50_Weights.IMAGENET1K_V1 if pretrained else None
            )
            self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)
        elif model_name == 'convnext_base':
            self.backbone = timm.create_model(
                'convnext_base', pretrained=pretrained, num_classes=num_classes
            )
        else:
            raise ValueError(f"نموذج غير مدعوم: {model_name}")

    def forward(self, x):
        return self.backbone(x)
