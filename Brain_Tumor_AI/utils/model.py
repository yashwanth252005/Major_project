import torch.nn as nn
from torchvision import models


NUM_CLASSES = 4


def build_model(num_classes=NUM_CLASSES):
    """
    Build the DenseNet121 architecture used during training.
    """

    model = models.densenet121(weights=None)

    num_features = model.classifier.in_features

    model.classifier = nn.Sequential(

        nn.Dropout(0.4),

        nn.Linear(num_features, 512),

        nn.BatchNorm1d(512),

        nn.ReLU(inplace=True),

        nn.Dropout(0.3),

        nn.Linear(512, num_classes)

    )

    return model