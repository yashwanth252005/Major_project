export const XAI_METHODS = [
  {
    key: "gradcam",
    label: "Grad-CAM",
    sub: "Region-level",
    desc: "Highlights which spatial regions of the scan most influenced the prediction, via gradients flowing into the final convolutional layer.",
  },
  {
    key: "lrp",
    label: "LRP",
    sub: "Pixel-level",
    desc: "Layer-wise Relevance Propagation redistributes the prediction score back through every layer to each individual pixel.",
  },
  {
    key: "shap",
    label: "SHAP",
    sub: "Feature-level",
    desc: "Shapley Additive Explanations estimate each region's marginal contribution to the model's output, grounded in game theory.",
  },
];
