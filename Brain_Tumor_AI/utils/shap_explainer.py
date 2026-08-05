import os
import io
import base64

import cv2
import shap
import torch
import numpy as np
import matplotlib.pyplot as plt


class SHAPGenerator:

    def __init__(
        self,
        model,
        background_folder="background"
    ):

        self.model = model

        self.background = []

        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])

        print("Loading SHAP Background Images...")

        for file in sorted(os.listdir(background_folder)):

            path = os.path.join(
                background_folder,
                file
            )

            img = cv2.imread(path)

            img = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2RGB
            )

            img = cv2.resize(
                img,
                (224,224)
            )

            img = img.astype(np.float32)/255.

            img = (img-mean)/std

            img = torch.tensor(
                img.transpose(2,0,1),
                dtype=torch.float32
            )

            self.background.append(img)

        self.background = torch.stack(
            self.background
        )

        print(
            "Background Shape:",
            self.background.shape
        )

        self.explainer = shap.GradientExplainer(

            self.model,

            self.background

        )

    def generate(

        self,

        input_tensor,

        image_np,

        prediction,

        class_names,

        confidence

    ):

        self.model.eval()

        shap_values = self.explainer.shap_values(

            input_tensor

        )

        if isinstance(shap_values, list):

            shap_map = shap_values[prediction][0]

        else:

            shap_map = shap_values[
                0,
                :,
                :,
                :,
                prediction
            ]

        shap_map = np.mean(
            shap_map,
            axis=0
        )

        plt.figure(figsize=(6,6))

        plt.imshow(
            shap_map,
            cmap="seismic"
        )

        plt.title(
        f"SHAP\nPrediction: {class_names[prediction]} ({confidence*100:.2f}%)"
        )

        plt.axis("off")

        buffer = io.BytesIO()

        plt.savefig(
            buffer,
            format="png",
            bbox_inches="tight"
        )

        plt.close()

        buffer.seek(0)

        return base64.b64encode(
            buffer.read()
        ).decode("utf-8")