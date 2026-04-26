// src/api/config.js
// URL base del backend — cambia el puerto si usas otro
export const API_URL = "http://127.0.0.1:8000";

// Función helper para fetch con manejo de errores
export async function apiFetch(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`[API] Error en ${endpoint}:`, error.message);
    throw error;
  }
}