"use client";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [light, setLight] = useState(false);
  useEffect(() => {
    setLight(document.documentElement.dataset.theme === "light");
  }, []);
  function toggle() {
    const next = !light;
    setLight(next);
    document.documentElement.dataset.theme = next ? "light" : "dark";
    try {
      localStorage.setItem("convertlab-theme", next ? "light" : "dark");
    } catch {
      /* storage may be disabled */
    }
  }
  return (
    <button
      className="theme-toggle"
      aria-label={light ? "Ativar modo escuro" : "Ativar modo claro"}
      onClick={toggle}
    >
      {light ? <Moon size={17} /> : <Sun size={17} />}
    </button>
  );
}
