import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

export default function MapView() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);

  const [zones, setZones] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [leadTime, setLeadTime] = useState(null);
  const [error, setError] = useState(null);

  /* ===============================
     1️⃣ Fetch prediction (GET)
     =============================== */
  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Backend error: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("Prediction response:", data);
        setZones(data.zones);
        setConfidence(data.confidence);
        setLeadTime(data.lead_time_days);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load prediction");
      });
  }, []);

  /* ===============================
     2️⃣ Initialize map ONCE
     =============================== */
  useEffect(() => {
    if (mapRef.current) return;

    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    mapRef.current.addControl(
      new mapboxgl.NavigationControl(),
      "top-right"
    );
  }, []);

  /* ===============================
     3️⃣ Add GeoJSON layers SAFELY
     =============================== */
  useEffect(() => {
    if (!zones || !mapRef.current) return;

    const map = mapRef.current;

    const addLayers = () => {
      // Avoid duplicates
      if (map.getSource("migration-zones")) {
        map.getSource("migration-zones").setData(zones);
        return;
      }

      map.addSource("migration-zones", {
        type: "geojson",
        data: zones,
      });

      // 🔴 SOURCE (FROM)
      map.addLayer({
        id: "migration-source",
        type: "fill",
        source: "migration-zones",
        filter: ["==", ["get", "type"], "source"],
        paint: {
          "fill-color": "#d73027",
          "fill-opacity": 0.55,
        },
      });

      // 🟢 DESTINATION (TO)
      map.addLayer({
        id: "migration-destination",
        type: "fill",
        source: "migration-zones",
        filter: ["==", ["get", "type"], "destination"],
        paint: {
          "fill-color": "#1a9850",
          "fill-opacity": 0.55,
        },
      });

      // Outline
      map.addLayer({
        id: "migration-outline",
        type: "line",
        source: "migration-zones",
        paint: {
          "line-color": "#333",
          "line-width": 1,
        },
      });
    };

    if (map.isStyleLoaded()) {
      addLayers();
    } else {
      map.once("load", addLayers);
    }
  }, [zones]);

  return (
    <>
      {/* 🗺️ Map */}
      <div
        ref={mapContainer}
        style={{ width: "100%", height: "100vh" }}
      />

      {/* 📊 Info Panel */}
      {confidence !== null && !error && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: 20,
            background: "white",
            padding: "12px 16px",
            borderRadius: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
            fontSize: "14px",
            maxWidth: "260px",
          }}
        >
          <div><b>Confidence:</b> {confidence}</div>
          <div><b>Lead time:</b> {leadTime} days</div>
          <div>
            <b>Status:</b>{" "}
            {confidence < 0.6
              ? "Low migration pressure detected"
              : "Elevated migration risk"}
          </div>
        </div>
      )}

      {/* ❌ Error state */}
      {error && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: 20,
            background: "#fee",
            padding: "12px 16px",
            borderRadius: "6px",
            color: "#900",
          }}
        >
          {error}
        </div>
      )}
    </>
  );
}
