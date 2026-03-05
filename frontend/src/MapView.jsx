import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

export default function MapView() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  const [confidence, setConfidence] = useState(null);
  const [leadTime, setLeadTime] = useState(null);

  const [showSource, setShowSource] = useState(true);
  const [showDestination, setShowDestination] = useState(true);
  const [showNDVI, setShowNDVI] = useState(false);
  const [showRain, setShowRain] = useState(false);
  const [showConflict, setShowConflict] = useState(false);

  // ============================
  // Fetch prediction metadata
  // ============================
  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => res.json())
      .then((data) => {
        setConfidence(data.confidence);
        setLeadTime(data.lead_time_days);
      })
      .catch((err) => console.error("Prediction error:", err));
  }, []);

  // ============================
  // Initialize Map
  // ============================
  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {

      // ========================
      // Migration Pressure
      // ========================
      map.addSource("migration-pressure", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/heatmap",
      });

      map.addLayer({
        id: "migration-source",
        type: "heatmap",
        source: "migration-pressure",
        filter: ["<", ["get", "pressure"], 0],
        paint: {
          "heatmap-weight": ["abs", ["get", "pressure"]],
          "heatmap-radius": 40,
          "heatmap-opacity": 0.8,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.5, "rgba(255,120,120,0.6)",
            1, "rgba(180,0,0,0.95)"
          ],
        },
      });

      map.addLayer({
        id: "migration-destination",
        type: "heatmap",
        source: "migration-pressure",
        filter: [">", ["get", "pressure"], 0],
        paint: {
          "heatmap-weight": ["get", "pressure"],
          "heatmap-radius": 40,
          "heatmap-opacity": 0.75,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.5, "rgba(120,255,120,0.6)",
            1, "rgba(0,140,0,0.95)"
          ],
        },
      });

      // ========================
      // NDVI Layer
      // ========================
      map.addSource("ndvi-layer", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/ndvi",
      });

      map.addLayer({
        id: "ndvi-heat",
        type: "circle",
        source: "ndvi-layer",
        paint: {
          "circle-radius": 3,
          "circle-opacity": 0.7,
          "circle-color": [
            "interpolate",
            ["linear"],
            ["get", "ndvi"],
            -0.2, "#d7191c",
            0, "#ffffbf",
            0.3, "#1a9850"
          ]
        }
      });

      // ========================
      // Rainfall Layer
      // ========================
      map.addSource("rain-layer", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/rainfall",
      });

      map.addLayer({
        id: "rain-heat",
        type: "circle",
        source: "rain-layer",
        paint: {
          "circle-radius": 3,
          "circle-opacity": 0.6,
          "circle-color": [
            "interpolate",
            ["linear"],
            ["get", "rain"],
            0, "#ffffcc",
            50, "#41b6c4",
            150, "#253494"
          ]
        }
      });

      // ========================
      // Conflict Layer (ACLED/UCDP)
      // ========================
      map.addSource("conflict-layer", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/conflict",
      });

      map.addLayer({
        id: "conflict-heat",
        type: "heatmap",
        source: "conflict-layer",
        paint: {
          "heatmap-weight": ["get", "weight"],
          "heatmap-radius": 35,
          "heatmap-opacity": 0.8,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.4, "orange",
            0.7, "red",
            1, "darkred"
          ],
        },
        layout: { visibility: "none" }
      });

      mapRef.current = map;
    });
  }, []);

  // ============================
  // Toggle Logic
  // ============================
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const toggleLayer = (layerId, visible) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(
          layerId,
          "visibility",
          visible ? "visible" : "none"
        );
      }
    };

    toggleLayer("migration-source", showSource);
    toggleLayer("migration-destination", showDestination);
    toggleLayer("ndvi-heat", showNDVI);
    toggleLayer("rain-heat", showRain);
    toggleLayer("conflict-heat", showConflict);

  }, [showSource, showDestination, showNDVI, showRain, showConflict]);

  return (
    <>
      <div ref={mapContainerRef} style={{ position: "absolute", inset: 0 }} />

      {/* INFO PANEL */}
      {confidence !== null && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: 20,
            zIndex: 10,
            background: "white",
            padding: "12px 16px",
            borderRadius: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
            fontSize: "14px",
          }}
        >
          <div><b>Confidence:</b> {confidence}</div>
          <div><b>Lead time:</b> {leadTime} days</div>
          <div><b>Status:</b> Elevated migration pressure</div>
        </div>
      )}

      {/* LAYER CONTROLS */}
      <div
        style={{
          position: "absolute",
          top: 20,
          right: 20,
          zIndex: 10,
          background: "white",
          padding: "12px",
          borderRadius: "6px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
          fontSize: "14px",
        }}
      >

        <div>
          <label>
            <input
              type="checkbox"
              checked={showSource}
              onChange={() => setShowSource(!showSource)}
            /> 🔴 Source
          </label>
        </div>

        <div>
          <label>
            <input
              type="checkbox"
              checked={showDestination}
              onChange={() => setShowDestination(!showDestination)}
            /> 🟢 Destination
          </label>
        </div>

        <div>
          <label>
            <input
              type="checkbox"
              checked={showNDVI}
              onChange={() => setShowNDVI(!showNDVI)}
            /> 🌱 NDVI
          </label>
        </div>

        <div>
          <label>
            <input
              type="checkbox"
              checked={showRain}
              onChange={() => setShowRain(!showRain)}
            /> 🌧 Rainfall
          </label>
        </div>

        <div>
          <label>
            <input
              type="checkbox"
              checked={showConflict}
              onChange={() => setShowConflict(!showConflict)}
            /> ⚔ Conflict
          </label>
        </div>

      </div>

      {/* LEGEND */}
      <div
        style={{
          position: "absolute",
          bottom: 20,
          right: 20,
          zIndex: 10,
          background: "white",
          padding: "12px",
          borderRadius: "6px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
          fontSize: "13px",
          width: "200px",
        }}
      >
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>
          Legend
        </div>

        <div>🔴 Migration Source</div>
        <div>🟢 Migration Destination</div>
        <div>🌱 NDVI Vegetation</div>
        <div>🌧 Rainfall</div>
        <div>⚔ Conflict Events</div>

        <div style={{ marginTop: "8px", fontSize: "11px", color: "#555" }}>
          Environmental & conflict drivers influencing migration
        </div>
      </div>
    </>
  );
}