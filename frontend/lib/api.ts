import axios, { AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";


export const api = axios.create({

  baseURL:
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000",

  headers:{
    "Content-Type":
      "application/json",
  },

});



api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Add auth token here later
  return config;
});


export default api;