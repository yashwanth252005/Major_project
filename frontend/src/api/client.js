import axios from "axios";

// In dev, vite.config.js proxies /api -> http://127.0.0.1:8000
const client = axios.create({ baseURL: "/api" });

export async function predictScan(file, { onUploadProgress } = {}) {
  const formData = new FormData();
  formData.append("image", file);

  const { data } = await client.post("/predict/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });

  return data;
  // Expected shape (from Brain_Tumor_AI/predict.py, plus persistence fields
  // added by the Django view):
  // {
  //   id: "uuid", created_at: "iso timestamp",
  //   prediction: { class: "glioma", confidence: 97.42 },
  //   processing_time: 1.203,
  //   original_image: "<base64 png>",
  //   gradcam: "<base64 png>",
  //   shap: "<base64 png>",
  //   integrated_gradients: "<base64 png>",
  //   summary: "..."
  // }
}

export async function fetchHistory() {
  const { data } = await client.get("/history/");
  return data;
}

export async function fetchScan(id) {
  const { data } = await client.get(`/history/${id}/`);
  return data;
}

export async function deleteScan(id) {
  await client.delete(`/history/${id}/`);
}

export default client;
