import io
import base64

import numpy as np
from PIL import Image

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image


class GradCAMGenerator:

    def __init__(self, model):

        self.model = model

        self.target_layers = [
            model.features.norm5
        ]

        self.cam = GradCAM(
            model=model,
            target_layers=self.target_layers
        )

    def generate(self, input_tensor):

        self.model.eval()

        grayscale_cam = self.cam(
            input_tensor=input_tensor
        )[0]

        image = input_tensor.squeeze(0).detach().cpu()

        image = image.permute(1, 2, 0).numpy()

        # Reverse ImageNet normalization
        image = image * np.array([0.229, 0.224, 0.225])

        image = image + np.array([0.485, 0.456, 0.406])

        image = np.clip(image, 0, 1)

        overlay = show_cam_on_image(
            image,
            grayscale_cam,
            use_rgb=True
        )

        # Convert NumPy image to PIL
        pil_image = Image.fromarray(overlay)

        buffer = io.BytesIO()

        pil_image.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        gradcam_base64 = base64.b64encode(
            buffer.read()
        ).decode("utf-8")

        return gradcam_base64