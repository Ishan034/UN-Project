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

  // -------------------------
  // Fetch prediction metadata
  // -------------------------
  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => res.json())
      .then((data) => {
        setConfidence(data.confidence);
        setLeadTime(data.lead_time_days);
      })
      .catch(() => {});
  }, []);

  // -------------------------
  // Initialize Mapbox
  // -------------------------
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
      // =============================
      // Migration Pressure
      // =============================
      map.addSource("migration-pressure", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/heatmap",
      });

      // 🔴 SOURCE
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

      // 🟢 DESTINATION
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

      // =============================
      // NDVI Layer
      // =============================
      map.addSource("ndvi-layer", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/ndvi",
      });

      map.addLayer({
        id: "ndvi-heat",
        type: "heatmap",
        source: "ndvi-layer",
        paint: {
          "heatmap-weight": ["get", "ndvi"],
          "heatmap-radius": 35,
          "heatmap-opacity": 0.6,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.4, "#ffffbf",
            0.7, "#a6d96a",
            1, "#1a9850"
          ],
        },
      });

      mapRef.current = map;
    });
  }, []);

  // -------------------------
  // Toggle Layer Visibility
  // -------------------------
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (map.getLayer("migration-source")) {
      map.setLayoutProperty(
        "migration-source",
        "visibility",
        showSource ? "visible" : "none"
      );
    }

    if (map.getLayer("migration-destination")) {
      map.setLayoutProperty(
        "migration-destination",
        "visibility",
        showDestination ? "visible" : "none"
      );
    }

    if (map.getLayer("ndvi-heat")) {
      map.setLayoutProperty(
        "ndvi-heat",
        "visibility",
        showNDVI ? "visible" : "none"
      );
    }

  }, [showSource, showDestination, showNDVI]);

  return (
    <>
      {/* MAP */}
      <div
        ref={mapContainerRef}
        style={{ position: "absolute", inset: 0 }}
      />

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

      {/* LAYER CONTROL PANEL */}
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

        <div style={{ marginTop: "6px" }}>
          <label>
            <input
              type="checkbox"
              checked={showNDVI}
              onChange={() => setShowNDVI(!showNDVI)}
            /> 🌱 NDVI
          </label>
        </div>
      </div>

      {/* LEGEND PANEL */}
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

        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{
            width: "16px",
            height: "16px",
            background: "rgba(180,0,0,0.95)",
            marginRight: "8px"
          }} />
          Migration Source (From)
        </div>

        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{
            width: "16px",
            height: "16px",
            background: "rgba(0,140,0,0.95)",
            marginRight: "8px"
          }} />
          Migration Destination (To)
        </div>

        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{
            width: "16px",
            height: "16px",
            background: "#1a9850",
            marginRight: "8px"
          }} />
          High Vegetation (NDVI)
        </div>

        <div style={{ marginTop: "8px", fontSize: "11px", color: "#555" }}>
          Based on environmental change signals
        </div>
      </div>
    </>
  );
}
