import { useState, useEffect } from "react";

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const Barrios = [
  { id: 1,  nombre: "Galan",               meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 2,  nombre: "Morichal",             meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 3,  nombre: "Juan Frio",            meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 4,  nombre: "El Palmar",            meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 5,  nombre: "Palogordo",            meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 6,  nombre: "Gran Colombia",        meta: 600,  actual: 210,  lider: "Sin asignar",    estado: "danger",  simpatizantes: 210,  indecisos: 280, opositores: 95  },
  { id: 7,  nombre: "Santa Barbara",        meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 8,  nombre: "San Jose",             meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 9,  nombre: "San Judas",            meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 10, nombre: "Primero de Mayo",      meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 11, nombre: "La Palmita",           meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 12, nombre: "Paramo",               meta: 600,  actual: 210,  lider: "Sin asignar",    estado: "danger",  simpatizantes: 210,  indecisos: 280, opositores: 95  },
  { id: 13, nombre: "Gramalote",            meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 14, nombre: "San Martin",           meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 15, nombre: "Bellavista",           meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 16, nombre: "San Gregorio",         meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 17, nombre: "Santander",            meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 18, nombre: "Centro",               meta: 600,  actual: 210,  lider: "Sin asignar",    estado: "danger",  simpatizantes: 210,  indecisos: 280, opositores: 95  },
  { id: 19, nombre: "Fatima",               meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 20, nombre: "Piedecuesta",          meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 21, nombre: "La Parada",            meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 22, nombre: "Turbay Ayala",         meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 23, nombre: "Villa Antigua",        meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 24, nombre: "La Primavera",         meta: 600,  actual: 210,  lider: "Sin asignar",    estado: "danger",  simpatizantes: 210,  indecisos: 280, opositores: 95  },
  { id: 25, nombre: "Antonio Nariño",       meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 26, nombre: "Brisas del Nariño",    meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 27, nombre: "Limites",              meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 28, nombre: "20 de Julio",          meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 30, nombre: "La Esperanza Alta",    meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 31, nombre: "Montevideo 1",         meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 32, nombre: "Montevideo 2",         meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 33, nombre: "Navarro Wolf",         meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 34, nombre: "Trapiches",            meta: 1100, actual: 1050, lider: "Diego Ríos",     estado: "green",   simpatizantes: 1050, indecisos: 140, opositores: 60  },
  { id: 35, nombre: "Villa Graciela",       meta: 600,  actual: 210,  lider: "Sin asignar",    estado: "danger",  simpatizantes: 210,  indecisos: 280, opositores: 95  },
  { id: 36, nombre: "Campo Verde",          meta: 1200, actual: 980,  lider: "Carlos Mesa",    estado: "warning", simpatizantes: 1140, indecisos: 320, opositores: 88  },
  { id: 37, nombre: "Lomitas",              meta: 900,  actual: 870,  lider: "Ana Puentes",    estado: "green",   simpatizantes: 870,  indecisos: 95,  opositores: 41  },
  { id: 38, nombre: "Bocono",               meta: 1500, actual: 620,  lider: "Pedro López",    estado: "danger",  simpatizantes: 620,  indecisos: 540, opositores: 210 },
  { id: 39, nombre: "La Esperanza Baja",    meta: 800,  actual: 790,  lider: "Luisa Valencia", estado: "green",   simpatizantes: 790,  indecisos: 110, opositores: 55  },
  { id: 40, nombre: "Pueblito Español",     meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
  { id: 41, nombre: "Senderos de Paz",      meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
  { id: 42, nombre: "Altos de Buenavista",  meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
  { id: 43, nombre: "Buenavista I",  meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
  { id: 44, nombre: "Buenavista II",  meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
  { id: 45, nombre: "Monaco",  meta: 600,  actual: 380,  lider: "Sin asignar",    estado: "warning", simpatizantes: 380,  indecisos: 190, opositores: 70  },
];

const ALERTAS = [
  { id: 1, tipo: "danger",  msg: "Juan Frio: 41% de meta — refuerzo urgente",          time: "12 min", leida: false },
  { id: 2, tipo: "warning", msg: "Gran Colombia sin líder asignado",                    time: "31 min", leida: false },
  { id: 3, tipo: "info",    msg: "IA detectó oportunidad en Barrio La Esperanza",       time: "1h",     leida: false },
  { id: 4, tipo: "success", msg: "Morichal alcanzó 97% de su meta",                     time: "2h",     leida: true  },
  { id: 5, tipo: "warning", msg: "Muchos indecisos en San Judas (540 registrados)",     time: "3h",     leida: true  },
];

const IA_RECOMENDACIONES = [
  { icon: "📍", text: "Haz campaña en La Esperanza — 280 indecisos sin contactar", urgencia: "alta"  },
  { icon: "👥", text: "Asigna un líder a Gran Colombia esta semana",                urgencia: "alta"  },
  { icon: "📢", text: "Envía WhatsApp a los 540 indecisos de San Judas",           urgencia: "media" },
  { icon: "🕐", text: "Mejor horario para contactar: martes y jueves 5–7 PM",      urgencia: "baja"  },
];

const CRECIMIENTO = [
  { dia: "Lun", votos: 320 }, { dia: "Mar", votos: 480 }, { dia: "Mié", votos: 390 },
  { dia: "Jue", votos: 620 }, { dia: "Vie", votos: 710 }, { dia: "Sáb", votos: 890 },
  { dia: "Hoy", votos: 1040 },
];

const CONTACTOS_RECIENTES = [
  { nombre: "María Rodríguez", tipo: "simpatizante", zona: "Galan",        lider: "Carlos M.", estado: "contactado", fecha: "Hoy 09:14" },
  { nombre: "Jorge Peña",      tipo: "simpatizante", zona: "Morichal",      lider: "Ana P.",    estado: "contactado", fecha: "Hoy 08:50" },
  { nombre: "Valentina Cruz",  tipo: "indeciso",     zona: "Juan Frio",     lider: "Pedro L.",  estado: "pendiente",  fecha: "Ayer"      },
  { nombre: "Hernán Vargas",   tipo: "indeciso",     zona: "El Palmar",     lider: "Luisa V.",  estado: "contactado", fecha: "Ayer"      },
  { nombre: "Sandra López",    tipo: "simpatizante", zona: "Palogordo",     lider: "Diego R.",  estado: "contactado", fecha: "Hace 2d"   },
];

const NAV_ITEMS = [
  { id: "dashboard",     icon: "⚡", label: "Dashboard"       },
  { id: "base",          icon: "👥", label: "Base Electoral"  },
  { id: "equipos",       icon: "🏗️", label: "Equipos"         },
  { id: "mapa",          icon: "🗺️", label: "Mapa Electoral"  },
  { id: "analitica",     icon: "📊", label: "Analítica IA"    },
  { id: "campanas",      icon: "📣", label: "Campañas"        },
  { id: "redes",         icon: "📡", label: "Redes Sociales"  },
  { id: "reportes",      icon: "📄", label: "Reportes"        },
  { id: "configuracion", icon: "⚙️", label: "Configuración"   },
];

const ESTADO_COLORS = {
  green:   { bg: "#052e16", border: "#166534", bar: "#22c55e", text: "#4ade80", badge: "#14532d", badgeText: "#86efac" },
  warning: { bg: "#422006", border: "#92400e", bar: "#f59e0b", text: "#fbbf24", badge: "#713f12", badgeText: "#fde68a" },
  danger:  { bg: "#450a0a", border: "#991b1b", bar: "#ef4444", text: "#f87171", badge: "#7f1d1d", badgeText: "#fca5a5" },
};

const TIPO_COLORS = {
  simpatizante: { bg: "#0c2340", text: "#60a5fa" },
  indeciso:     { bg: "#2d1a00", text: "#fbbf24" },
  opositor:     { bg: "#1f0505", text: "#f87171" },
};

const MAX_BAR     = Math.max(...CRECIMIENTO.map(d => d.votos));
const total_meta  = Barrios.reduce((a, z) => a + z.meta,          0);
const total_votos = Barrios.reduce((a, z) => a + z.actual,        0);
const total_simp  = Barrios.reduce((a, z) => a + z.simpatizantes, 0);
const total_ind   = Barrios.reduce((a, z) => a + z.indecisos,     0);
const total_op    = Barrios.reduce((a, z) => a + z.opositores,    0);
const pct_global  = Math.round((total_votos / total_meta) * 100);

// ─── COMPONENTES ─────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, color, trend }) {
  return (
    <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: "20px 22px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
        <div style={{ width: 38, height: 38, borderRadius: 10, background: `${color}18`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>{icon}</div>
      </div>
      <div style={{ fontSize: 30, fontWeight: 900, color: "#f1f5f9", lineHeight: 1 }}>{value.toLocaleString("es-CO")}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {trend && <span style={{ fontSize: 11, color: trend > 0 ? "#4ade80" : "#f87171", fontWeight: 700 }}>{trend > 0 ? "↑" : "↓"} {Math.abs(trend)}%</span>}
        {sub && <span style={{ fontSize: 11, color: "#475569" }}>{sub}</span>}
      </div>
    </div>
  );
}

function ZonaRow({ z, onClick }) {
  const pct = Math.round((z.actual / z.meta) * 100);
  const c = ESTADO_COLORS[z.estado];
  return (
    <div
      onClick={() => onClick(z)}
      style={{ padding: "14px 16px", borderRadius: 12, border: `1px solid ${c.border}60`, background: `${c.bg}60`, cursor: "pointer", transition: "all 0.2s" }}
      onMouseEnter={e => { e.currentTarget.style.background = c.bg; e.currentTarget.style.borderColor = c.border; }}
      onMouseLeave={e => { e.currentTarget.style.background = `${c.bg}60`; e.currentTarget.style.borderColor = `${c.border}60`; }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#f1f5f9" }}>{z.nombre}</span>
          <span style={{ fontSize: 11, color: "#475569", marginLeft: 8 }}>● {z.lider}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 800, color: c.text }}>{z.actual.toLocaleString()}</span>
          <span style={{ fontSize: 11, color: "#475569" }}>/ {z.meta.toLocaleString()}</span>
          <span style={{ background: c.badge, color: c.badgeText, fontSize: 10, fontWeight: 800, padding: "2px 8px", borderRadius: 999 }}>{pct}%</span>
        </div>
      </div>
      <div style={{ height: 5, background: "rgba(255,255,255,0.05)", borderRadius: 3 }}>
        <div style={{ height: 5, borderRadius: 3, background: c.bar, width: `${Math.min(pct, 100)}%`, transition: "width 1s ease" }} />
      </div>
    </div>
  );
}

function AlertaItem({ a }) {
  const cfg = {
    danger:  { icon: "⛔" },
    warning: { icon: "⚠️" },
    info:    { icon: "💡" },
    success: { icon: "✅" },
  }[a.tipo];
  return (
    <div style={{ display: "flex", gap: 10, padding: "10px 0", borderBottom: "1px solid #1a2e4a", opacity: a.leida ? 0.5 : 1 }}>
      <span style={{ fontSize: 15 }}>{cfg.icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.5 }}>{a.msg}</div>
        <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>Hace {a.time}</div>
      </div>
    </div>
  );
}

// ─── MODAL DETALLE BARRIO ─────────────────────────────────────────────────────
function ZonaModal({ zona, onClose }) {
  if (!zona) return null;
  const pct = Math.round((zona.actual / zona.meta) * 100);
  const c = ESTADO_COLORS[zona.estado];
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 300, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={onClose}>
      <div style={{ background: "#0f1e35", border: `1px solid ${c.border}`, borderRadius: 20, padding: 32, maxWidth: 440, width: "90%" }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>Barrio</div>
            <div style={{ fontSize: 24, fontWeight: 900, color: "#f1f5f9" }}>{zona.nombre}</div>
          </div>
          <button onClick={onClose} style={{ background: "#1a2e4a", border: "none", color: "#64748b", width: 32, height: 32, borderRadius: 8, cursor: "pointer", fontSize: 16 }}>✕</button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
          {[
            { l: "Líder",         v: zona.lider,                        col: "#f1f5f9" },
            { l: "Progreso",      v: `${pct}%`,                         col: c.text   },
            { l: "Simpatizantes", v: zona.simpatizantes.toLocaleString(), col: "#4ade80" },
            { l: "Indecisos",     v: zona.indecisos.toLocaleString(),    col: "#fbbf24" },
            { l: "Opositores",    v: zona.opositores.toLocaleString(),   col: "#f87171" },
            { l: "Meta",          v: zona.meta.toLocaleString(),         col: "#60a5fa" },
          ].map((item, i) => (
            <div key={i} style={{ background: "#1a2e4a50", borderRadius: 10, padding: "12px 14px" }}>
              <div style={{ fontSize: 10, color: "#475569", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.8 }}>{item.l}</div>
              <div style={{ fontSize: 18, fontWeight: 900, color: item.col }}>{item.v}</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: "#475569", fontWeight: 700, marginBottom: 6 }}>AVANCE</div>
        <div style={{ height: 8, background: "rgba(255,255,255,0.05)", borderRadius: 4 }}>
          <div style={{ height: 8, borderRadius: 4, background: c.bar, width: `${Math.min(pct, 100)}%` }} />
        </div>
      </div>
    </div>
  );
}

// ─── MODAL TODOS LOS BARRIOS ──────────────────────────────────────────────────
function ModalTodosBarrios({ onClose, onSelectBarrio }) {
  const [filtro, setFiltro] = useState("todos");
  const lista = filtro === "todos" ? Barrios : Barrios.filter(z => z.estado === filtro);

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={onClose}>
      <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 20, padding: 28, width: 620, maxWidth: "95vw", maxHeight: "80vh", display: "flex", flexDirection: "column", gap: 16 }} onClick={e => e.stopPropagation()}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: "#f1f5f9" }}>Todos los Barrios ({Barrios.length})</div>
          <button onClick={onClose} style={{ background: "#1a2e4a", border: "none", color: "#64748b", width: 32, height: 32, borderRadius: 8, cursor: "pointer", fontSize: 18, fontFamily: "inherit" }}>✕</button>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {[
            { key: "todos",   label: "Todos",    color: "#60a5fa" },
            { key: "green",   label: "Fuertes",  color: "#4ade80" },
            { key: "warning", label: "Alerta",   color: "#fbbf24" },
            { key: "danger",  label: "Críticos", color: "#f87171" },
          ].map(f => (
            <button key={f.key} onClick={() => setFiltro(f.key)}
              style={{
                fontSize: 12, padding: "5px 14px", borderRadius: 8, cursor: "pointer",
                fontFamily: "inherit", fontWeight: 700, border: "1px solid",
                background:   filtro === f.key ? `${f.color}20` : "transparent",
                color:        filtro === f.key ? f.color : "#475569",
                borderColor:  filtro === f.key ? `${f.color}60` : "#1a2e4a",
              }}>
              {f.label} ({f.key === "todos" ? Barrios.length : Barrios.filter(z => z.estado === f.key).length})
            </button>
          ))}
        </div>

        <div style={{ overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, paddingRight: 4 }}>
          {lista.map(z => (
            <ZonaRow key={z.id} z={z} onClick={(zona) => { onClose(); onSelectBarrio(zona); }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── PANTALLAS ────────────────────────────────────────────────────────────────
function ScreenComingSoon({ label }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16, paddingTop: 80 }}>
      <div style={{ fontSize: 56 }}>🚧</div>
      <div style={{ fontSize: 20, fontWeight: 800, color: "#475569" }}>{label}</div>
      <div style={{ fontSize: 13, color: "#334155" }}>Próximamente — En desarrollo</div>
    </div>
  );
}

function DashboardScreen({ onZonaClick }) {
  const [animVotos, setAnimVotos] = useState(0);
  const [modalTodos, setModalTodos] = useState(false);

  useEffect(() => {
    let v = 0;
    const step = total_votos / 80;
    const t = setInterval(() => {
      v += step;
      if (v >= total_votos) { setAnimVotos(total_votos); clearInterval(t); }
      else setAnimVotos(Math.floor(v));
    }, 14);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* STAT CARDS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
        <StatCard icon="🗳️" label="Votos Estimados"  value={animVotos}  sub={`de ${total_meta.toLocaleString()} meta`} color="#3b82f6" trend={3.2}  />
        <StatCard icon="🤝" label="Simpatizantes"    value={total_simp} sub="registrados"   color="#10b981" trend={5.7}  />
        <StatCard icon="🤔" label="Indecisos"        value={total_ind}  sub="por convencer" color="#f59e0b" trend={-2.1} />
        <StatCard icon="❌" label="Opositores"       value={total_op}   sub="identificados" color="#ef4444" />
      </div>

      {/* ROW 2 */}
      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14 }}>

        {/* Gráfica de crecimiento */}
        <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9" }}>Crecimiento de Votos</div>
              <div style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>Últimos 7 días</div>
            </div>
            <span style={{ background: "#052e1680", color: "#4ade80", fontSize: 11, fontWeight: 800, padding: "3px 10px", borderRadius: 999, border: "1px solid #166534" }}>↑ Esta semana</span>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 130 }}>
            {CRECIMIENTO.map((d, i) => {
              const h = Math.round((d.votos / MAX_BAR) * 110);
              const isHoy = d.dia === "Hoy";
              return (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 5 }}>
                  {isHoy && <span style={{ fontSize: 10, color: "#60a5fa", fontWeight: 800 }}>{d.votos}</span>}
                  <div style={{ width: "100%", height: h, borderRadius: "6px 6px 0 0", background: isHoy ? "linear-gradient(180deg,#3b82f6,#1d4ed8)" : "#1e3a5f", transition: "height 0.8s ease" }} />
                  <span style={{ fontSize: 10, color: isHoy ? "#60a5fa" : "#334155", fontWeight: isHoy ? 800 : 400 }}>{d.dia}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Progreso global */}
        <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: 22, display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9" }}>Meta Electoral Global</div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ position: "relative", width: 120, height: 120 }}>
              <svg viewBox="0 0 120 120" style={{ width: 120, height: 120, transform: "rotate(-90deg)" }}>
                <circle cx="60" cy="60" r="50" fill="none" stroke="#1a2e4a" strokeWidth="12" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="#3b82f6" strokeWidth="12"
                  strokeDasharray={`${2 * Math.PI * 50}`}
                  strokeDashoffset={`${2 * Math.PI * 50 * (1 - pct_global / 100)}`}
                  strokeLinecap="round" style={{ transition: "stroke-dashoffset 1.5s ease" }} />
              </svg>
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 24, fontWeight: 900, color: "#60a5fa" }}>{pct_global}%</span>
                <span style={{ fontSize: 9, color: "#475569", fontWeight: 700 }}>COMPLETADO</span>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 0", borderTop: "1px solid #1a2e4a" }}>
            {[
              { label: "Alcanzados", val: total_votos.toLocaleString("es-CO"),              color: "#60a5fa" },
              { label: "Faltantes",  val: (total_meta - total_votos).toLocaleString("es-CO"), color: "#475569" },
            ].map((item, i) => (
              <div key={i} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 18, fontWeight: 900, color: item.color }}>{item.val}</div>
                <div style={{ fontSize: 10, color: "#334155", marginTop: 2 }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ROW 3 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>

        {/* Barrios — 5 primeros + Ver todos */}
        <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9" }}>Estado por Barrios</div>
            <button onClick={() => setModalTodos(true)}
              style={{ fontSize: 12, color: "#60a5fa", background: "none", border: "none", cursor: "pointer", fontWeight: 700, fontFamily: "inherit" }}>
              Ver todos ({Barrios.length}) →
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {Barrios.slice(0, 5).map(z => <ZonaRow key={z.id} z={z} onClick={onZonaClick} />)}
          </div>
        </div>

        {/* Alertas + IA */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: 22 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9", marginBottom: 4 }}>🔔 Alertas Inteligentes</div>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 14 }}>{ALERTAS.filter(a => !a.leida).length} sin leer</div>
            {ALERTAS.map(a => <AlertaItem key={a.id} a={a} />)}
          </div>

          <div style={{ background: "linear-gradient(135deg,#0c1e38,#0f2545)", border: "1px solid #1e3a6a", borderRadius: 16, padding: 22 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9", marginBottom: 14 }}>🧠 Recomendaciones IA</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {IA_RECOMENDACIONES.map((r, i) => (
                <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "10px 12px", borderRadius: 10, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={{ fontSize: 16 }}>{r.icon}</span>
                  <div style={{ flex: 1, fontSize: 12, color: "#cbd5e1", lineHeight: 1.5 }}>{r.text}</div>
                  <span style={{
                    fontSize: 9, fontWeight: 800, padding: "2px 7px", borderRadius: 999, flexShrink: 0,
                    background: r.urgencia === "alta" ? "#450a0a" : r.urgencia === "media" ? "#422006" : "#0c2340",
                    color:      r.urgencia === "alta" ? "#f87171" : r.urgencia === "media" ? "#fbbf24" : "#60a5fa",
                  }}>{r.urgencia.toUpperCase()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Contactos recientes */}
      <div style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 16, padding: 22 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9" }}>Contactos Recientes</div>
          <button style={{ background: "#1d4ed8", color: "#fff", border: "none", padding: "7px 14px", borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>+ Agregar</button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Nombre", "Tipo", "Barrio", "Líder asignado", "Estado", "Fecha"].map(h => (
                <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 10, color: "#334155", fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.8, borderBottom: "1px solid #1a2e4a" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CONTACTOS_RECIENTES.map((c, i) => {
              const tc = TIPO_COLORS[c.tipo] || { bg: "#1a2e4a", text: "#94a3b8" };
              return (
                <tr key={i} style={{ borderBottom: "1px solid #0f1e35" }}
                  onMouseEnter={e => e.currentTarget.style.background = "#1a2e4a40"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  <td style={{ padding: "12px", fontWeight: 700, fontSize: 13, color: "#f1f5f9" }}>{c.nombre}</td>
                  <td style={{ padding: "12px" }}>
                    <span style={{ background: tc.bg, color: tc.text, fontSize: 10, fontWeight: 700, padding: "3px 9px", borderRadius: 999, textTransform: "capitalize" }}>{c.tipo}</span>
                  </td>
                  <td style={{ padding: "12px", fontSize: 12, color: "#64748b" }}>{c.zona}</td>
                  <td style={{ padding: "12px", fontSize: 12, color: "#64748b" }}>{c.lider}</td>
                  <td style={{ padding: "12px" }}>
                    <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
                      background: c.estado === "contactado" ? "#052e16" : "#1c1917",
                      color:      c.estado === "contactado" ? "#4ade80"  : "#a8a29e" }}>
                      {c.estado === "contactado" ? "✓ Contactado" : "⏳ Pendiente"}
                    </span>
                  </td>
                  <td style={{ padding: "12px", fontSize: 11, color: "#334155" }}>{c.fecha}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal todos los barrios */}
      {modalTodos && (
        <ModalTodosBarrios
          onClose={() => setModalTodos(false)}
          onSelectBarrio={(zona) => onZonaClick(zona)}
        />
      )}
    </div>
  );
}

// ─── APP PRINCIPAL ────────────────────────────────────────────────────────────
export default function Dashboard({ onGoLanding }) {
  const [activeNav,       setActiveNav]       = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [zonaModal,       setZonaModal]       = useState(null);
  const [notifsOpen,      setNotifsOpen]      = useState(false);
  const [hora,            setHora]            = useState(
    new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
  );

  useEffect(() => {
    const t = setInterval(() =>
      setHora(new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" }))
    , 1000);
    return () => clearInterval(t);
  }, []);

  const activeLabel  = NAV_ITEMS.find(n => n.id === activeNav)?.label || "Dashboard";
  const unreadAlerts = ALERTAS.filter(a => !a.leida).length;

  return (
    <div style={{ display: "flex", height: "100vh", background: "#060d1f", fontFamily: "'Plus Jakarta Sans','Segoe UI',sans-serif", color: "#e2e8f0", overflow: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: #0a1525; }
        ::-webkit-scrollbar-thumb { background: #1a2e4a; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #253d5e; }
      `}</style>

      {/* SIDEBAR */}
      <div style={{ width: sidebarCollapsed ? 68 : 230, flexShrink: 0, background: "#080f1f", borderRight: "1px solid #111e35", display: "flex", flexDirection: "column", transition: "width 0.25s ease", overflow: "hidden" }}>
        <div style={{ padding: "18px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid #111e35", minHeight: 64 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg,#2563eb,#1d4ed8)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, fontWeight: 900, flexShrink: 0 }}>P</div>
          {!sidebarCollapsed && <span style={{ fontWeight: 900, fontSize: 17, letterSpacing: "-0.3px", whiteSpace: "nowrap" }}>Politi<span style={{ color: "#3b82f6" }}>CRM</span></span>}
        </div>

        <nav style={{ flex: 1, padding: "12px 8px", display: "flex", flexDirection: "column", gap: 3, overflowY: "auto" }}>
          {NAV_ITEMS.map(item => {
            const active = activeNav === item.id;
            return (
              <button key={item.id} onClick={() => setActiveNav(item.id)} title={sidebarCollapsed ? item.label : undefined}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, border: "none", background: active ? "#1d4ed820" : "transparent", color: active ? "#60a5fa" : "#475569", cursor: "pointer", fontFamily: "inherit", fontWeight: active ? 700 : 500, fontSize: 13, borderLeft: active ? "3px solid #3b82f6" : "3px solid transparent", transition: "all 0.15s", textAlign: "left", width: "100%" }}>
                <span style={{ fontSize: 17, flexShrink: 0 }}>{item.icon}</span>
                {!sidebarCollapsed && <span style={{ whiteSpace: "nowrap" }}>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div style={{ borderTop: "1px solid #111e35", padding: "12px 8px", display: "flex", flexDirection: "column", gap: 8 }}>
          <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 10, border: "none", background: "transparent", color: "#334155", cursor: "pointer", fontFamily: "inherit", fontSize: 12, width: "100%" }}>
            <span style={{ fontSize: 16, flexShrink: 0 }}>{sidebarCollapsed ? "→" : "←"}</span>
            {!sidebarCollapsed && <span>Colapsar</span>}
          </button>
          {!sidebarCollapsed && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, background: "#0f1e35" }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#7c3aed,#db2777)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 12, flexShrink: 0 }}>AG</div>
              <div style={{ overflow: "hidden" }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#e2e8f0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>Adriana González</div>
                <div style={{ fontSize: 10, color: "#334155" }}>Admin</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MAIN */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* TOPBAR */}
        <div style={{ height: 60, background: "#080f1f", borderBottom: "1px solid #111e35", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", flexShrink: 0 }}>
          <div>
            <span style={{ fontWeight: 800, fontSize: 18, color: "#f1f5f9" }}>{activeLabel}</span>
            <span style={{ fontSize: 12, color: "#334155", marginLeft: 10 }}>Campaña Adriana González 2027</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 12, color: "#334155" }}>🕐 {hora}</span>
            <div style={{ position: "relative" }}>
              <button onClick={() => setNotifsOpen(!notifsOpen)}
                style={{ background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 10, width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "#64748b", fontSize: 16, position: "relative" }}>
                🔔
                {unreadAlerts > 0 && (
                  <span style={{ position: "absolute", top: 4, right: 4, width: 16, height: 16, background: "#ef4444", borderRadius: "50%", fontSize: 9, fontWeight: 900, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>{unreadAlerts}</span>
                )}
              </button>
              {notifsOpen && (
                <div style={{ position: "absolute", right: 0, top: 44, width: 320, background: "#0f1e35", border: "1px solid #1a2e4a", borderRadius: 14, padding: 16, zIndex: 50, boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>
                  <div style={{ fontSize: 13, fontWeight: 800, color: "#f1f5f9", marginBottom: 12 }}>Alertas</div>
                  {ALERTAS.map(a => <AlertaItem key={a.id} a={a} />)}
                </div>
              )}
            </div>
            {onGoLanding && (
              <button onClick={onGoLanding}
                style={{ background: "#1a2e4a", border: "1px solid #253d5e", borderRadius: 10, padding: "7px 14px", cursor: "pointer", color: "#64748b", fontSize: 12, fontWeight: 600, fontFamily: "inherit" }}>
                ← Landing
              </button>
            )}
          </div>
        </div>

        {/* CONTENIDO */}
        <div style={{ flex: 1, overflowY: "auto", padding: 20 }} onClick={() => notifsOpen && setNotifsOpen(false)}>
          {activeNav === "dashboard" && <DashboardScreen onZonaClick={setZonaModal} />}
          {activeNav !== "dashboard" && <ScreenComingSoon label={activeLabel} />}
        </div>
      </div>

      {/* Modal detalle barrio */}
      <ZonaModal zona={zonaModal} onClose={() => setZonaModal(null)} />
    </div>
  );
}