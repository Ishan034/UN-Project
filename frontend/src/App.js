import React, { useState } from "react";
import MapView from "./MapView";
import DashboardView from "./DashboardView";

function App() {
  const [mode, setMode] = useState("map");

  return (
    <div className="w-full h-screen">

      {/* TOP TOGGLE BAR */}
      <div style={{
        position: "absolute",
        top: 20,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 50,
        background: "white",
        padding: "8px 12px",
        borderRadius: "10px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
        display: "flex",
        gap: "10px"
      }}>

        <button
          onClick={() => setMode("map")}
          style={{
            padding: "6px 12px",
            borderRadius: "6px",
            border: "none",
            background: mode === "map" ? "black" : "#e5e5e5",
            color: mode === "map" ? "white" : "black",
            cursor: "pointer"
          }}
        >
          Model View
        </button>

        <button
          onClick={() => setMode("dashboard")}
          style={{
            padding: "6px 12px",
            borderRadius: "6px",
            border: "none",
            background: mode === "dashboard" ? "black" : "#e5e5e5",
            color: mode === "dashboard" ? "white" : "black",
            cursor: "pointer"
          }}
        >
          Dashboard
        </button>

      </div>

      {/* MAIN CONTENT */}
      {mode === "map" ? <MapView /> : <DashboardView />}
    </div>
  );
}

export default App;