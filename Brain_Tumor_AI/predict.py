# import json
# import time
# import torch

# from utils.model import build_model
# from utils.preprocessing import preprocess_image
# from utils.gradcam import GradCAMGenerator
# from utils.shap_explainer import SHAPGenerator
# from utils.integrated_gradients import IntegratedGradientsGenerator
# from utils.explanation import generate_summary
from utils.xai_consistency import compute_xai_consistency


# class BrainTumorPredictor:

#     def __init__(self):

#         self.device = torch.device(
#             "cuda" if torch.cuda.is_available() else "cpu"
#         )

#         with open("config.json", "r") as f:
#             self.config = json.load(f)

#         self.class_names = self.config["class_names"]

#         self.model = build_model()

#         self.model.load_state_dict(
#             torch.load(
#                 "models/best_densenet121.pth",
#                 map_location=self.device
#             )
#         )

#         self.model.to(self.device)
#         self.model.eval()

#         self.gradcam = GradCAMGenerator(self.model)
#         self.shap = SHAPGenerator(self.model)
#         self.integrated_gradients = IntegratedGradientsGenerator(self.model)

#     def predict(self, image_path):

#         start = time.time()

#         input_tensor, image_np = preprocess_image(
#             image_path,
#             self.config["mean"],
#             self.config["std"],
#             return_original=True
#         )

#         input_tensor = input_tensor.to(self.device)

#         # ---------- Prediction ----------
#         with torch.no_grad():

#             outputs = self.model(input_tensor)

#             probs = torch.softmax(outputs, dim=1)

#             confidence, pred = torch.max(probs, 1)

#         prediction = self.class_names[pred.item()]

#         summary = generate_summary(
#             prediction,
#             confidence.item() * 100
#         )

#         # ---------- GradCAM ----------
#         gradcam = self.gradcam.generate(
#             input_tensor=input_tensor,
#             image_np=image_np,
#             prediction=pred.item(),
#             class_names=self.class_names,
#             confidence=confidence.item()
#         )

#         # ---------- SHAP ----------
#         shap, shap_map = self.shap.generate(
#             input_tensor=input_tensor,
#             image_np=image_np,
#             prediction=pred.item(),
#             class_names=self.class_names,
#             confidence=confidence.item()
#         )

#         # ---------- Integrated Gradients ----------
#         integrated_gradients, integrated_gradients_map = self.integrated_gradients.generate(
#             input_tensor=input_tensor,
#             image_np=image_np,
#             prediction=pred.item(),
#             class_names=self.class_names,
#             confidence=confidence.item()
#         )

#         return {

#             "prediction": {
#                 "class": prediction,
#                 "confidence": round(confidence.item() * 100, 2)
#             },

#             "processing_time": round(
#                 total_seconds,
#                 3
#             ),

#             "gradcam": gradcam,

#             "shap": shap,

#             "integrated_gradients": integrated_gradients,

#             "summary": summary,

#           "xai_consistency": xai_consistency

#         }


# if __name__ == "__main__":

#     predictor = BrainTumorPredictor()

#     result = predictor.predict("sample.jpg")

#     print(result)




import json
import time
import torch

from utils.model import build_model
from utils.preprocessing import preprocess_image
from utils.gradcam import GradCAMGenerator
from utils.shap_explainer import SHAPGenerator
from utils.integrated_gradients import IntegratedGradientsGenerator
from utils.explanation import generate_summary
from utils.xai_consistency import compute_xai_consistency


class BrainTumorPredictor:

    def __init__(self):

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        with open("config.json", "r") as f:
            self.config = json.load(f)

        self.class_names = self.config["class_names"]

        self.model = build_model()

        self.model.load_state_dict(
            torch.load(
                "models/best_densenet121.pth",
                map_location=self.device
            )
        )

        self.model.to(self.device)
        self.model.eval()

        self.gradcam = GradCAMGenerator(self.model)
        self.shap = SHAPGenerator(
        self.model,
        background_folder="background"
        )
        self.integrated_gradients = IntegratedGradientsGenerator(self.model)

    def predict(self, image_path):

        start = time.time()

        stage_start = time.time()
        input_tensor, image_np = preprocess_image(
            image_path,
            self.config["mean"],
            self.config["std"],
            return_original=True
        )

        input_tensor = input_tensor.to(self.device)
        preprocess_seconds = time.time() - stage_start

        # ---------------- Prediction ----------------

        stage_start = time.time()

        with torch.no_grad():

            outputs = self.model(input_tensor)

            probabilities = torch.softmax(outputs, dim=1)

            confidence, pred = torch.max(
                probabilities,
                dim=1
            )

        prediction = self.class_names[pred.item()]
        prediction_seconds = time.time() - stage_start

        summary = generate_summary(
            prediction,
            confidence.item() * 100
        )

        # ---------------- GradCAM ----------------

        stage_start = time.time()
        gradcam, gradcam_map = self.gradcam.generate(
            input_tensor
        )
        gradcam_seconds = time.time() - stage_start

        # ---------------- SHAP ----------------

        stage_start = time.time()
        shap, shap_map = self.shap.generate(
            input_tensor=input_tensor,
            image_np=image_np,
            prediction=pred.item(),
            class_names=self.class_names,
            confidence=confidence.item()
        )
        shap_seconds = time.time() - stage_start

        # -------- Integrated Gradients --------

        stage_start = time.time()
        integrated_gradients, integrated_gradients_map = self.integrated_gradients.generate(
            input_tensor=input_tensor,
            image_np=image_np,
            prediction=pred.item(),
            class_names=self.class_names,
            confidence=confidence.item()
        )
        integrated_gradients_seconds = time.time() - stage_start

        xai_consistency = compute_xai_consistency(
            gradcam_map,
            integrated_gradients_map,
            shap_map,
        )

        total_seconds = time.time() - start
        print(
            "[NeuroScan timing] "
            f"preprocess={preprocess_seconds:.3f}s | "
            f"prediction={prediction_seconds:.3f}s | "
            f"gradcam={gradcam_seconds:.3f}s | "
            f"shap={shap_seconds:.3f}s | "
            f"integrated_gradients={integrated_gradients_seconds:.3f}s | "
            f"total={total_seconds:.3f}s"
        )

        return {

            "prediction": {

                "class": prediction,

                "confidence": round(
                    confidence.item() * 100,
                    2
                )

            },

            "processing_time": round(
                time.time() - start,
                3
            ),

            "gradcam": gradcam,

            "shap": shap,

            "integrated_gradients": integrated_gradients,

            "summary": summary,

            "xai_consistency": xai_consistency

        }


if __name__ == "__main__":

    predictor = BrainTumorPredictor()

    result = predictor.predict("notumor.jpg")

    print(result)