def generate_summary(

    prediction,

    confidence

):

    if confidence > 95:

        certainty = "very high"

    elif confidence > 85:

        certainty = "high"

    else:

        certainty = "moderate"

    return (

        f"The model predicts "

        f"{prediction} "

        f"with {certainty} confidence "

        f"({confidence:.2f}%). "

        f"Grad-CAM highlights the lesion "

        f"region responsible for the prediction, "

        f"while SHAP identifies the pixel-level "

        f"contributions supporting this decision."

    )