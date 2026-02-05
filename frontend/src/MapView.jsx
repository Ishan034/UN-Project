import React, { useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

/*
  🔴 Migration SOURCE zones
  These represent areas cattle are migrating FROM
*/
const migrationSources = [
  { lng: 29.9, lat: 7.9, weight: 1.0 },
  { lng: 30.2, lat: 7.6, weight: 0.8 },
];

/*
  🟢 Migration DESTINATION zones
  These represent areas cattle are migrating TOWARDS
*/
const migrationDestinations = [
  { lng: 31.3, lat: 6.8, weight: 0.9 },
  { lng: 31.6, lat: 6.5, weight: 1.0 },
];

export default function MapView() {
  useEffect(() => {
    // 🔗 Backend call (already verified working)
    fetch("https://un-project-4ajo.onrender.com/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("Prediction response from backend:", data);
      });

    // 🗺️ Initialize map
    const map = new mapboxgl.Map({
      container: "map",
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.8, 7.2],
      zoom: 6,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {
      /* ================================
         🔴 SOURCE HEATMAP (RED)
         ================================ */
      map.addSource("migration-source", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: migrationSources.map((p) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [p.lng, p.lat],
            },
            properties: {
              weight: p.weight,
            },
          })),
        },
      });

      map.addLayer({
        id: "migration-source-heat",
        type: "heatmap",
        source: "migration-source",
        paint: {
          "heatmap-weight": ["get", "weight"],
          "heatmap-radius": 45,
          "heatmap-opacity": 0.6,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(255,0,0,0)",
            0.4,
            "rgba(255,120,120,0.5)",
            0.8,
            "rgba(180,0,0,0.9)",
          ],
        },
      });

      /* ================================
         🟢 DESTINATION HEATMAP (GREEN)
         ================================ */
      map.addSource("migration-destination", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: migrationDestinations.map((p) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [p.lng, p.lat],
            },
            properties: {
              weight: p.weight,
            },
          })),
        },
      });

      map.addLayer({
        id: "migration-destination-heat",
        type: "heatmap",
        source: "migration-destination",
        paint: {
          "heatmap-weight": ["get", "weight"],
          "heatmap-radius": 45,
          "heatmap-opacity": 0.6,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(0,255,0,0)",
            0.4,
            "rgba(120,220,120,0.5)",
            0.8,
            "rgba(0,140,0,0.9)",
          ],
        },
      });
    });

    return () => map.remove();
  }, []);

  return (
    <div
      id="map"
      style={{
        width: "100%",
        height: "100vh",
      }}
    />
  );
}
