import { useState } from "react";
import LandingPage from "./LandingPage";
import Dashboard from "./Dashboard";
 
export default function App() {
  const [view, setView] = useState("landing"); // "landing" | "dashboard"
 
  if (view === "dashboard") return <Dashboard onGoLanding={() => setView("landing")} />;
  return <LandingPage onEnterApp={() => setView("dashboard")} />;
}
