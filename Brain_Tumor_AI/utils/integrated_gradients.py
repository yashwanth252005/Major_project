import io
import base64
import numpy as np
import matplotlib.pyplot as plt

from captum.attr import IntegratedGradients


class IntegratedGradientsGenerator:

    def __init__(self, model):
        self.model = model
        self.ig = IntegratedGradients(model)

    def generate(
        self,
        input_tensor,
        image_np,
        prediction,
        class_names,
        confidence
    ):

        input_tensor.requires_grad_(True)

        attributions = self.ig.attribute(
            input_tensor,
            target=prediction,
            n_steps=50
        )

        attr = attributions.squeeze(0).detach().cpu().numpy()

        attr = np.mean(attr, axis=0)
        attr = np.maximum(attr, 0)
        attr = attr / (attr.max() + 1e-8)

        plt.figure(figsize=(7,7))

        plt.imshow(image_np)
        plt.imshow(attr, cmap="jet", alpha=0.5)

        plt.title(
            f"Integrated Gradients\nPrediction: {class_names[prediction]} ({confidence*100:.2f}%)"
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