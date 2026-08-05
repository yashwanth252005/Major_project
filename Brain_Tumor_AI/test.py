import base64

from predict import BrainTumorPredictor


predictor = BrainTumorPredictor()

# Change this path to your test image
print("predicting started...")
result = predictor.predict("google_glioma.jpg")
print("predicting completed...")

print("results received...")
print("=" * 60)
print("Prediction :", result["prediction"]["class"])
print("Confidence :", result["prediction"]["confidence"], "%")
print("Summary    :", result["summary"])
print("=" * 60)

print("Saving GradCAM, SHAP, and Integrated Gradients images...")
# Save GradCAM
with open("gradcam.png", "wb") as f:
    f.write(base64.b64decode(result["gradcam"]))

# Save SHAP
with open("shap.png", "wb") as f:
    f.write(base64.b64decode(result["shap"]))

# Save Integrated Gradients
with open("integrated_gradients.png", "wb") as f:
    f.write(base64.b64decode(result["integrated_gradients"]))

print("✅ gradcam.png saved")
print("✅ shap.png saved")
print("✅ integrated_gradients.png saved")