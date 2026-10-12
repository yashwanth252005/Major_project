def generate_summary(prediction, confidence):
    return (
        f"The DenseNet121 model predicts {prediction} with a softmax confidence "
        f"of {confidence:.2f}%. Grad-CAM, Integrated Gradients, and SHAP were "
        "generated to provide complementary attribution evidence for the model "
        "output. These explanations indicate model influence or contribution; "
        "they do not confirm tumor tissue, lesion boundaries, or a clinical diagnosis."
    )
