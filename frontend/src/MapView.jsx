import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

export default function MapView() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);

  const [confidence, setConfidence] = useState(null);
  const [leadTime, setLeadTime] = useState(null);

  // -------------------------
  // Fetch metadata (confidence, lead time)
  // -------------------------
  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => res.json())
      .then((data) => {
        setConfidence(data.confidence);
        setLeadTime(data.lead_time_days);
      })
      .catch((err) => console.error(err));
  }, []);

  // -------------------------
  // Initialize map
  // -------------------------
  useEffect(() => {
    if (mapRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      // -------------------------
      // Heatmap source
      // -------------------------
      map.addSource("migration-heatmap", {
        type: "geojson",
        data: "https://un-project-4ajo.onrender.com/heatmap",
      });

      // -------------------------
      // Heatmap layer
      // -------------------------
      map.addLayer({
        id: "migration-heat",
        type: "heatmap",
        source: "migration-heatmap",
        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["get", "pressure"],
            -0.2, 0,
             0.0, 0.3,
             0.2, 1
          ],
          "heatmap-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            5, 20,
            7, 40,
            9, 60
          ],
          "heatmap-opacity": 0.75,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0.0, "rgba(0,0,0,0)",
            0.2, "#2c7bb6",
            0.4, "#abd9e9",
            0.6, "#ffffbf",
            0.8, "#fdae61",
            1.0, "#d7191c"
          ],
        },
      });
    });

    return () => map.remove();
  }, []);

  return (
    <>
      {/* Map */}
      <div
        ref={mapContainer}
        style={{ width: "100%", height: "100vh" }}
      />

      {/* Info Panel */}
      {confidence !== null && (
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
          }}
        >
          <div><b>Confidence:</b> {confidence}</div>
          <div><b>Lead time:</b> {leadTime} days</div>
          <div><b>Status:</b> Elevated migration pressure</div>
        </div>
      )}
    </>
  );
}
