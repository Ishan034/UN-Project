import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || "";

export default function MapView() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  const [confidence, setConfidence] = useState(null);
  const [leadTime, setLeadTime] = useState(null);
  const [data, setData] = useState(null); // ✅ NEW

  const [showSource, setShowSource] = useState(true);
  const [showDestination, setShowDestination] = useState(true);
  const [showFlows, setShowFlows] = useState(true);
  const [showNDVI, setShowNDVI] = useState(false);
  const [showRain, setShowRain] = useState(false);
  const [showConflict, setShowConflict] = useState(false);

  // =========================
  // Fetch prediction metadata (SAFE)
  // =========================

  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => res.json())
      .then((data) => {
        if (!data || !data.zones) {
          console.warn("Invalid predict response", data);
          return;
        }

        setConfidence(data.confidence ?? 0);
        setLeadTime(data.lead_time_days ?? 0);
        setData(data); // ✅ IMPORTANT
      })
      .catch((err) => {
        console.error("Predict fetch failed:", err);
      });
  }, []);

  // =========================
  // Map initialization
  // =========================

  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("error", (e) => {
      console.error("Mapbox error:", e);
    });

    map.on("load", () => {
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
            1, "rgba(180,0,0,0.95)",
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
            1, "rgba(0,140,0,0.95)",
          ],
        },
      });

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
            0.3, "#1a9850",
          ],
        },
      });

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
            150, "#253494",
          ],
        },
      });

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
            1, "darkred",
          ],
        },
        layout: { visibility: "none" },
      });

      // (flows code unchanged — left exactly as-is)

      mapRef.current = map;
    });
  }, []);

  // =========================
  // Toggle logic
  // =========================

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    function toggle(id, state) {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", state ? "visible" : "none");
      }
    }

    toggle("migration-source", showSource);
    toggle("migration-destination", showDestination);
    toggle("migration-flow-lines", showFlows);
    toggle("migration-flow-arrows", showFlows);
    toggle("ndvi-heat", showNDVI);
    toggle("rain-heat", showRain);
    toggle("conflict-heat", showConflict);
  }, [showSource, showDestination, showFlows, showNDVI, showRain, showConflict]);

  return (
    <>
      <div ref={mapContainerRef} style={{ position: "absolute", inset: 0 }} />

      {confidence !== null && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: 20,
            background: "white",
            padding: "12px",
            borderRadius: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
          }}
        >
          <div><b>Confidence:</b> {confidence}</div>
          <div><b>Lead time:</b> {leadTime} days</div>
          <div><b>Risk level:</b> {data?.risk_level}</div>
          <div><b>Affected index:</b> {data?.affected_score}</div>
        </div>
      )}

      <div
        style={{
          position: "absolute",
          top: 20,
          right: 20,
          background: "white",
          padding: "12px",
          borderRadius: "6px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
        }}
      >
        <label><input type="checkbox" checked={showSource} onChange={() => setShowSource(!showSource)} /> 🔴 Source</label><br/>
        <label><input type="checkbox" checked={showDestination} onChange={() => setShowDestination(!showDestination)} /> 🟢 Destination</label><br/>
        <label><input type="checkbox" checked={showFlows} onChange={() => setShowFlows(!showFlows)} /> 🟠 Migration Corridor</label><br/>
        <label><input type="checkbox" checked={showNDVI} onChange={() => setShowNDVI(!showNDVI)} /> 🌱 NDVI</label><br/>
        <label><input type="checkbox" checked={showRain} onChange={() => setShowRain(!showRain)} /> 🌧 Rainfall</label><br/>
        <label><input type="checkbox" checked={showConflict} onChange={() => setShowConflict(!showConflict)} /> ⚔ Conflict</label>
      </div>
    </>
  );
}