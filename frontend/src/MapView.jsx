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

  // -------------------------
  // Fetch metadata
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
  // Initialize Mapbox once
  // -------------------------
  useEffect(() => {
    if (mapRef.current) return;
    if (!mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {
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
            1, "rgba(180,0,0,0.95)",
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
            1, "rgba(0,140,0,0.95)",
          ],
        },
      });
    });

    mapRef.current = map;
  }, []);

  // -------------------------
  // Toggle visibility
  // -------------------------
  useEffect(() => {
    if (!mapRef.current) return;

    const map = mapRef.current;

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
  }, [showSource, showDestination]);

  return (
    <>
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
            />{" "}
            🔴 Show Source
          </label>
        </div>

        <div style={{ marginTop: "6px" }}>
          <label>
            <input
              type="checkbox"
              checked={showDestination}
              onChange={() => setShowDestination(!showDestination)}
            />{" "}
            🟢 Show Destination
          </label>
        </div>
      </div>
    </>
  );
}
