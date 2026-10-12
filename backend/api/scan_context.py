"""Build trusted scan context without sending MRI/XAI image bytes to the LLM."""


def build_scan_context(scan):
    return {
        "scan_id": str(scan.id),
        "model": {
            "name": "DenseNet121",
            "num_classes": 4,
            "class_names": ["glioma", "meningioma", "notumor", "pituitary"],
            "confidence_method": "softmax probability of the predicted class",
        },
        "predicted_class": scan.predicted_class,
        "confidence_percent": float(scan.confidence),
        "processing_time_seconds": scan.processing_time,
        "existing_summary": scan.summary or "",
        "xai": {
            "gradcam": {
                "available": bool(scan.gradcam_b64),
                "method": "Grad-CAM",
                "target_layer": "model.features.norm5",
                "meaning": "spatial regions influencing the model output; not segmentation",
            },
            "integrated_gradients": {
                "available": bool(scan.integrated_gradients_b64),
                "method": "Captum IntegratedGradients",
                "n_steps": 50,
                "baseline_configuration": "No baseline argument is explicitly supplied in the project code.",
                "meaning": "input attribution for the predicted output",
            },
            "shap": {
                "available": bool(scan.shap_b64),
                "method": "shap.GradientExplainer",
                "background_images_runtime": 20,
                "explained_output": "top/predicted model output",
                "nsamples": 50,
                "meaning": "feature/input contribution toward the model output",
            },
        },
        "xai_consistency": scan.xai_consistency or {},
        "created_at": scan.created_at.isoformat(),
    }
