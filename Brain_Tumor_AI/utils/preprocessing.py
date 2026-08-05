from PIL import Image
from torchvision import transforms
import numpy as np


def get_transform(mean, std, image_size=224):

    return transforms.Compose([

        transforms.Resize((image_size, image_size)),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=mean,
            std=std
        )

    ])


def preprocess_image(
    image_path,
    mean,
    std,
    return_original=False
):

    image = Image.open(image_path).convert("RGB")

    transform = get_transform(mean, std)

    tensor = transform(image).unsqueeze(0)

    if not return_original:
        return tensor

    # Original image resized to 224x224
    image_np = image.resize((224, 224))
    image_np = np.array(image_np).astype(np.float32) / 255.0

    return tensor, image_np