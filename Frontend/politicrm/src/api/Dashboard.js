// src/api/dashboard.js
import { apiFetch } from "./config";

// Resumen general del dashboard
export const getDashboardResumen = () => apiFetch("/dashboard/resumen");

// Barrios con conteo real de líderes
export const getBarrios = () => apiFetch("/barrios/");

// Líderes con filtros opcionales
export const getLideres = (params = {}) => {
  const query = new URLSearchParams();
  if (params.barrio_id) query.append("barrio_id", params.barrio_id);
  if (params.activo !== undefined) query.append("activo", params.activo);
  if (params.skip) query.append("skip", params.skip);
  if (params.limit) query.append("limit", params.limit);
  return apiFetch(`/lideres/?${query.toString()}`);
};

// Un líder por ID
export const getLiderById = (id) => apiFetch(`/lideres/${id}`);

// Crear nuevo líder
export const crearLider = (data) =>
  apiFetch("/lideres/", {
    method: "POST",
    body: JSON.stringify(data),
  });

// Actualizar líder
export const actualizarLider = (id, data) =>
  apiFetch(`/lideres/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

// Stats de nurturing
export const getNurturingStats = () => apiFetch("/nurturing/stats");