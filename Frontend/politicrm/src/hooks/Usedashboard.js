// src/hooks/useDashboard.js
import { useState, useEffect } from "react";
import { getDashboardResumen, getBarrios, getLideres } from "../api/dashboard";

// Hook para el resumen general del dashboard
export function useDashboardResumen() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    getDashboardResumen()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

// Hook para barrios con conteo de líderes
export function useBarrios() {
  const [barrios, setBarrios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    getBarrios()
      .then(setBarrios)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { barrios, loading, error };
}

// Hook para líderes con filtros
export function useLideres(params = {}) {
  const [data,    setData]    = useState({ total: 0, lideres: [] });
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    setLoading(true);
    getLideres(params)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [params.barrio_id, params.skip, params.limit]);

  return { data, loading, error };
}