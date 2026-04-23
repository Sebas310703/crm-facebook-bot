import { useState, useEffect, useRef } from "react";

const NAV_LINKS = ["Características", "Precios", "Testimonios", "Contacto"];

const FEATURES = [
  {
    icon: "🗳️",
    title: "Control Electoral en Tiempo Real",
    desc: "Visualiza cuántos votos lleva tu campaña minuto a minuto. Semáforo por zonas: verde, amarillo o rojo.",
  },
  {
    icon: "🧠",
    title: "Inteligencia Artificial Integrada",
    desc: "Análisis de sentimiento en redes sociales, predicción de votos y recomendaciones estratégicas automáticas.",
  },
  {
    icon: "👥",
    title: "Gestión de Simpatizantes",
    desc: "Base de datos centralizada con filtros por zona, tipo de votante, líder asignado y estado de contacto.",
  },
  {
    icon: "🗺️",
    title: "Mapa Electoral Interactivo",
    desc: "Identifica zonas débiles y fuertes visualmente. Toma decisiones basadas en geografía real.",
  },
  {
    icon: "📣",
    title: "Campañas de Mensajería",
    desc: "Envía mensajes masivos por WhatsApp, SMS y Email. Segmenta por barrio, tipo de votante o edad.",
  },
  {
    icon: "📊",
    title: "Reportes Exportables",
    desc: "Genera reportes en PDF y Excel de votos, zonas y rendimiento de líderes con un solo clic.",
  },
];

const PLANS = [
  {
    name: "Starter",
    target: "Concejal / JAC",
    price: "$890.000",
    period: "COP / mes",
    usd: "≈ USD 220",
    color: "from-slate-700 to-slate-800",
    accent: "#64748b",
    features: ["Hasta 500 contactos", "Dashboard principal", "Mapa básico", "1 usuario admin", "Soporte por email"],
    cta: "Comenzar",
    highlight: false,
  },
  {
    name: "Professional",
    target: "Alcalde municipal",
    price: "$2.200.000",
    period: "COP / mes",
    usd: "≈ USD 540",
    color: "from-blue-700 to-blue-900",
    accent: "#3b82f6",
    features: ["Hasta 5.000 contactos", "Todo Starter +", "Análisis de redes sociales IA", "5 usuarios", "Mapa avanzado", "Campañas WhatsApp", "Soporte prioritario"],
    cta: "Más popular",
    highlight: true,
  },
  {
    name: "Campaign",
    target: "Diputado / Senado",
    price: "$4.800.000",
    period: "COP / mes",
    usd: "≈ USD 1.180",
    color: "from-emerald-700 to-emerald-900",
    accent: "#10b981",
    features: ["Contactos ilimitados", "Todo Professional +", "Predicción IA de votos", "Usuarios ilimitados", "API personalizada", "Reportes avanzados", "Soporte 24/7"],
    cta: "Contáctanos",
    highlight: false,
  },
];

const STATS = [
  { value: "3.200+", label: "Simpatizantes gestionados" },
  { value: "98%", label: "Precisión en proyecciones" },
  { value: "47", label: "Campañas activas" },
  { value: "6x", label: "Más eficiencia que Excel" },
];

const TESTIMONIOS = [
  {
    name: "Adriana González",
    role: "Candidata a Alcaldía — Cúcuta",
    text: "PolitiCRM nos permitió organizar más de 3.000 simpatizantes en menos de una semana. El mapa electoral fue clave para entender dónde necesitábamos refuerzo.",
    avatar: "AG",
    color: "from-blue-600 to-blue-800",
  },
  {
    name: "Ricardo Morales",
    role: "Coordinador de Campaña — Norte de Santander",
    text: "Antes usábamos Excel y WhatsApp. Con PolitiCRM tenemos todo centralizado, los líderes pueden registrar personas desde el celular y vemos el conteo en tiempo real.",
    avatar: "RM",
    color: "from-emerald-600 to-emerald-800",
  },
  {
    name: "Camila Herrera",
    role: "Asesora Política — Pamplona",
    text: "El análisis de redes sociales con IA detectó una crisis de reputación antes de que explotara. Nos permitió responder rápido y controlar el daño.",
    avatar: "CH",
    color: "from-violet-600 to-violet-800",
  },
];

function CountUp({ target, suffix = "" }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const num = parseFloat(target.replace(/[^0-9.]/g, ""));
          const isFloat = target.includes(".");
          let current = 0;
          const step = num / 60;
          const t = setInterval(() => {
            current += step;
            if (current >= num) { setCount(num); clearInterval(t); }
            else setCount(isFloat ? parseFloat(current.toFixed(1)) : Math.floor(current));
          }, 16);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [target]);

  const display = target.includes("+")
    ? count.toLocaleString("es-CO") + "+"
    : target.includes("%")
    ? count + "%"
    : target.includes("x")
    ? count + "x"
    : count.toLocaleString("es-CO");

  return <span ref={ref}>{display}</span>;
}

export default function LandingPage({ onEnterApp }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#060d1f] text-white overflow-x-hidden" style={{ fontFamily: "'Plus Jakarta Sans', 'Segoe UI', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');
        .grad-text { background: linear-gradient(135deg, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .gold-text { background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .glow-blue { box-shadow: 0 0 60px rgba(59,130,246,0.25); }
        .glow-green { box-shadow: 0 0 40px rgba(16,185,129,0.2); }
        .card-hover { transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .card-hover:hover { transform: translateY(-6px); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
        .btn-primary { background: linear-gradient(135deg, #2563eb, #1d4ed8); transition: all 0.2s; }
        .btn-primary:hover { background: linear-gradient(135deg, #3b82f6, #2563eb); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(37,99,235,0.4); }
        .btn-ghost { border: 1px solid rgba(255,255,255,0.15); transition: all 0.2s; }
        .btn-ghost:hover { border-color: rgba(255,255,255,0.4); background: rgba(255,255,255,0.05); }
        .grid-bg { background-image: linear-gradient(rgba(59,130,246,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.05) 1px, transparent 1px); background-size: 40px 40px; }
        .plan-highlight { border: 2px solid #3b82f6; position: relative; }
        .plan-highlight::before { content: "MÁS POPULAR"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg,#2563eb,#1d4ed8); color: white; font-size: 10px; font-weight: 800; padding: 3px 14px; border-radius: 999px; letter-spacing: 1px; }
        .feature-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); transition: all 0.3s; }
        .feature-card:hover { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.3); }
        .noise { background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E"); position: fixed; inset: 0; pointer-events: none; z-index: 0; }
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-18px)} }
        @keyframes pulse-ring { 0%{transform:scale(1);opacity:0.6} 100%{transform:scale(1.5);opacity:0} }
        .float { animation: float 6s ease-in-out infinite; }
        .float-delay { animation: float 6s ease-in-out 2s infinite; }
        .fade-in { animation: fadeIn 0.7s ease forwards; opacity: 0; }
        @keyframes fadeIn { to { opacity: 1; } }
      `}</style>

      <div className="noise" />

      {/* NAVBAR */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "bg-[#060d1f]/95 backdrop-blur-md border-b border-white/5 shadow-xl" : ""}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center font-black text-lg shadow-lg shadow-blue-900/50">P</div>
            <span className="font-black text-xl tracking-tight">Politi<span className="text-blue-400">CRM</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map(l => (
              <a key={l} href={`#${l.toLowerCase()}`} className="text-sm text-slate-400 hover:text-white transition-colors font-medium">{l}</a>
            ))}
          </div>
          <div className="hidden md:flex items-center gap-3">
            <button onClick={onEnterApp} className="btn-ghost text-sm font-semibold px-5 py-2 rounded-lg text-slate-300">Ver Demo</button>
            <button onClick={onEnterApp} className="btn-primary text-sm font-bold px-5 py-2 rounded-lg text-white">Acceder al CRM →</button>
          </div>
          <button className="md:hidden text-slate-400" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} /></svg>
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden bg-[#0b1428] border-t border-white/5 px-6 py-4 flex flex-col gap-4">
            {NAV_LINKS.map(l => <a key={l} href={`#${l.toLowerCase()}`} className="text-sm text-slate-300 font-medium">{l}</a>)}
            <button onClick={onEnterApp} className="btn-primary text-sm font-bold px-5 py-3 rounded-lg text-white w-full">Acceder al CRM →</button>
          </div>
        )}
      </nav>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center grid-bg pt-16">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-emerald-600/8 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-6 py-24 grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-blue-950/60 border border-blue-800/40 rounded-full px-4 py-2 text-xs font-bold text-blue-300 mb-8 tracking-wider uppercase">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              Sistema activo en tiempo real
            </div>
            <h1 className="text-5xl lg:text-6xl font-black leading-tight tracking-tight mb-6">
              Gana las elecciones<br />
              con <span className="grad-text">datos reales</span>,<br />
              no con suposiciones.
            </h1>
            <p className="text-slate-400 text-lg leading-relaxed mb-10 max-w-lg">
              PolitiCRM es el sistema inteligente que necesita tu campaña: gestión de simpatizantes, mapa electoral, análisis de redes sociales con IA y conteo de votos en tiempo real.
            </p>
            <div className="flex flex-wrap gap-4">
              <button onClick={onEnterApp} className="btn-primary font-bold px-8 py-4 rounded-xl text-base glow-blue">
                Explorar el Dashboard →
              </button>
              <button className="btn-ghost font-semibold px-8 py-4 rounded-xl text-base text-slate-300">
                Ver video demo ▶
              </button>
            </div>
            <div className="flex items-center gap-6 mt-10">
              <div className="flex -space-x-2">
                {["AG","RM","CH","PL","MV"].map((i,idx)=>(
                  <div key={idx} className={`w-9 h-9 rounded-full border-2 border-[#060d1f] flex items-center justify-center text-xs font-bold ${["bg-blue-700","bg-emerald-700","bg-violet-700","bg-orange-700","bg-rose-700"][idx]}`}>{i}</div>
                ))}
              </div>
              <div className="text-sm text-slate-400"><span className="text-white font-bold">47 campañas</span> activas hoy</div>
            </div>
          </div>

          {/* HERO CARD MOCKUP */}
          <div className="relative hidden lg:block">
            <div className="float">
              <div className="bg-[#0d1a2d] border border-white/10 rounded-2xl p-6 shadow-2xl glow-blue">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Votos proyectados</div>
                    <div className="text-4xl font-black text-white mt-1">14.520 <span className="text-emerald-400 text-lg">↑ 3.2%</span></div>
                  </div>
                  <div className="w-14 h-14 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-2xl">🗳️</div>
                </div>
                <div className="space-y-3">
                  {[
                    { zona: "Centro", pct: 82, color: "#10b981" },
                    { zona: "Sur", pct: 91, color: "#10b981" },
                    { zona: "Norte", pct: 43, color: "#ef4444" },
                    { zona: "Oriente", pct: 68, color: "#f59e0b" },
                  ].map(z => (
                    <div key={z.zona}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">{z.zona}</span>
                        <span className="font-bold" style={{ color: z.color }}>{z.pct}%</span>
                      </div>
                      <div className="h-1.5 bg-white/5 rounded-full">
                        <div className="h-1.5 rounded-full transition-all" style={{ width: `${z.pct}%`, background: z.color }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-2 text-xs text-emerald-400">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    IA detectó oportunidad en Barrio La Merced
                  </div>
                </div>
              </div>
            </div>
            {/* Floating badge */}
            <div className="float-delay absolute -top-6 -right-6 bg-emerald-900/80 border border-emerald-600/40 backdrop-blur-sm rounded-xl px-4 py-3 text-sm font-bold text-emerald-300 shadow-xl">
              📈 +124 nuevos hoy
            </div>
            <div className="float absolute -bottom-4 -left-6 bg-red-950/80 border border-red-700/40 backdrop-blur-sm rounded-xl px-4 py-3 text-sm font-bold text-red-300 shadow-xl">
              ⚠️ Zona Norte necesita atención
            </div>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="py-16 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-8">
          {STATS.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-4xl font-black grad-text mb-2">
                <CountUp target={s.value} />
              </div>
              <div className="text-sm text-slate-500 font-medium">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section id="características" className="py-28 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="text-xs font-bold text-blue-400 tracking-widest uppercase mb-4">Módulos del sistema</div>
          <h2 className="text-4xl font-black tracking-tight mb-4">Todo lo que necesita<br /><span className="grad-text">tu campaña</span></h2>
          <p className="text-slate-400 max-w-xl mx-auto">Desde registrar simpatizantes hasta analizar redes sociales con IA. Todo en una sola plataforma.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => (
            <div key={i} className="feature-card rounded-2xl p-7 card-hover cursor-default" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="text-4xl mb-5">{f.icon}</div>
              <h3 className="font-bold text-lg mb-3 text-white">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FLUJO */}
      <section className="py-24 bg-gradient-to-b from-transparent to-blue-950/10">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="text-xs font-bold text-emerald-400 tracking-widest uppercase mb-4">Flujo real del usuario</div>
            <h2 className="text-4xl font-black tracking-tight">Así funciona en <span className="grad-text">la práctica</span></h2>
          </div>
          <div className="grid lg:grid-cols-2 gap-6">
            {[
              { n: "01", title: "Entra al Dashboard", desc: "Ve el estado de tu campaña en tiempo real: votos, zonas, alertas y recomendaciones de IA." },
              { n: "02", title: "Identifica zonas débiles", desc: "El mapa te muestra en rojo dónde estás perdiendo. Un vistazo basta para tomar decisiones." },
              { n: "03", title: "Detecta el problema", desc: "¿Qué líder está fallando? ¿Cuántos indecisos hay en esa zona? Los datos están ahí." },
              { n: "04", title: "Actúa con precisión", desc: "Envía una campaña segmentada por WhatsApp solo a los indecisos de esa zona. En minutos." },
              { n: "05", title: "Mide los resultados", desc: "¿Cuántos respondieron? ¿Cuántos se convirtieron en simpatizantes? El sistema lo mide todo." },
              { n: "06", title: "Gana la elección", desc: "Con datos reales, estrategia inteligente y ejecución organizada. Eso es PolitiCRM." },
            ].map((step, i) => (
              <div key={i} className="flex gap-5 p-6 rounded-2xl bg-white/[0.03] border border-white/5 card-hover">
                <div className="text-4xl font-black text-white/10 leading-none min-w-[3rem]">{step.n}</div>
                <div>
                  <h3 className="font-bold text-white mb-2">{step.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIOS */}
      <section id="testimonios" className="py-28 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="text-xs font-bold text-blue-400 tracking-widest uppercase mb-4">Testimonios</div>
          <h2 className="text-4xl font-black tracking-tight">Campañas que <span className="grad-text">confían en nosotros</span></h2>
        </div>
        <div className="grid lg:grid-cols-3 gap-6">
          {TESTIMONIOS.map((t, i) => (
            <div key={i} className="p-8 rounded-2xl bg-white/[0.03] border border-white/7 card-hover flex flex-col gap-5">
              <div className="text-slate-300 text-sm leading-relaxed italic">"{t.text}"</div>
              <div className="flex items-center gap-4 mt-auto pt-4 border-t border-white/5">
                <div className={`w-11 h-11 rounded-full bg-gradient-to-br ${t.color} flex items-center justify-center text-sm font-bold`}>{t.avatar}</div>
                <div>
                  <div className="font-bold text-sm text-white">{t.name}</div>
                  <div className="text-xs text-slate-500">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* PRECIOS */}
      <section id="precios" className="py-28 bg-gradient-to-b from-blue-950/10 to-transparent">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="text-xs font-bold text-blue-400 tracking-widest uppercase mb-4">Planes</div>
            <h2 className="text-4xl font-black tracking-tight mb-3">Precios <span className="grad-text">transparentes</span></h2>
            <p className="text-slate-400">Sin sorpresas. Sin comisiones ocultas. Cancela cuando quieras.</p>
          </div>
          <div className="grid lg:grid-cols-3 gap-6 items-center">
            {PLANS.map((p, i) => (
              <div key={i} className={`rounded-2xl p-8 ${p.highlight ? "plan-highlight bg-blue-950/40 scale-105" : "bg-white/[0.03] border border-white/7"} card-hover`}>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{p.target}</div>
                <div className="font-black text-2xl text-white mb-1">{p.name}</div>
                <div className="mb-2">
                  <span className="text-3xl font-black" style={{ color: p.highlight ? "#60a5fa" : "white" }}>{p.price}</span>
                  <span className="text-slate-500 text-sm ml-2">{p.period}</span>
                </div>
                <div className="text-xs text-slate-500 mb-7">{p.usd}</div>
                <div className="space-y-3 mb-8">
                  {p.features.map((f, j) => (
                    <div key={j} className="flex items-start gap-3 text-sm">
                      <span className="text-emerald-400 mt-0.5 text-base">✓</span>
                      <span className="text-slate-300">{f}</span>
                    </div>
                  ))}
                </div>
                <button
                  onClick={onEnterApp}
                  className={`w-full py-3 rounded-xl font-bold text-sm transition-all ${p.highlight ? "btn-primary text-white" : "btn-ghost text-slate-300"}`}
                >
                  {p.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section id="contacto" className="py-28 max-w-4xl mx-auto px-6 text-center">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-600/10 rounded-3xl blur-2xl" />
          <div className="relative bg-gradient-to-br from-blue-950/60 to-[#060d1f] border border-blue-800/30 rounded-3xl p-16">
            <div className="text-5xl mb-6">🏆</div>
            <h2 className="text-4xl font-black tracking-tight mb-5">
              ¿Listo para ganar<br /><span className="grad-text">con datos reales?</span>
            </h2>
            <p className="text-slate-400 mb-10 text-lg max-w-xl mx-auto leading-relaxed">
              Únete a las campañas que ya están usando PolitiCRM. El sistema que convierte datos en votos.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button onClick={onEnterApp} className="btn-primary font-bold px-10 py-4 rounded-xl text-base glow-blue">
                Ver el Dashboard ahora →
              </button>
              <a href="tel:+573001234567" className="btn-ghost font-semibold px-10 py-4 rounded-xl text-base text-slate-300">
                📞 Hablar con ventas
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center font-black text-sm">P</div>
            <span className="font-black text-lg">Politi<span className="text-blue-400">CRM</span></span>
          </div>
          <div className="text-sm text-slate-600">© 2025 PolitiCRM — Universidad de Pamplona. Todos los derechos reservados.</div>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-white transition-colors">Privacidad</a>
            <a href="#" className="hover:text-white transition-colors">Términos</a>
            <a href="#" className="hover:text-white transition-colors">Soporte</a>
          </div>
        </div>
      </footer>
    </div>
  );
}