import { useState, useEffect } from "react";
import "./App.css";

export default function App() {
  const [count, setCount] = useState(0);
  const [theme, setTheme] = useState(
    typeof window !== "undefined"
      ? localStorage.getItem("theme") || "dark"
      : "dark"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Aegis Cognitive Mesh</h1>
        <span style={styles.badge}>Day 7</span>
      </header>

      <p style={styles.subtitle}>Minimal UI baseline</p>

      <div style={styles.row}>
        <button
          style={styles.primary}
          onClick={() => setCount((c) => c + 1)}
        >
          Primary Action (clicked {count})
        </button>

        <button
          style={styles.secondary}
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          Toggle {theme === "dark" ? "Light" : "Dark"} Mode
        </button>
      </div>

      <footer style={styles.footer}>
        <code>v0.1.0 • minimal</code>
      </footer>
    </div>
  );
}

const styles = {
page: {
minHeight: "100vh",
width: "100%",
display: "grid",
placeItems: "center",
textAlign: "center",
padding: "24px",
},
header: {
display: "flex",
alignItems: "center",
justifyContent: "center",
gap: "12px",
flexWrap: "wrap",
marginBottom: "8px",
},
// keep the rest unchanged
};
