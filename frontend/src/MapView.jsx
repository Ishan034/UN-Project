import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || "";

export default function MapView() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  const [confidence, setConfidence] = useState(null);
  const [leadTime, setLeadTime] = useState(null);

  const [showSource, setShowSource] = useState(true);
  const [showDestination, setShowDestination] = useState(true);
  const [showFlows, setShowFlows] = useState(true);
  const [showNDVI, setShowNDVI] = useState(false);
  const [showRain, setShowRain] = useState(false);
  const [showConflict, setShowConflict] = useState(false);

  // =========================
  // Fetch prediction metadata
  // =========================

  useEffect(() => {
    fetch("https://un-project-4ajo.onrender.com/predict")
      .then((res) => res.json())
      .then((data) => {
        setConfidence(data.confidence);
        setLeadTime(data.lead_time_days);
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

    map.on("load", () => {
      // ======================
      // Migration pressure
      // ======================

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

      // ======================
      // NDVI
      // ======================

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

      // ======================
      // Rainfall
      // ======================

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

      // ======================
      // Conflict layer
      // ======================

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

      // ======================
      // Migration corridors
      // ======================

      fetch("https://un-project-4ajo.onrender.com/predict")
        .then((res) => res.json())
        .then((data) => {
          const zones = data.zones.features;

          const sources = zones.filter((f) => f.properties.type === "source");
          const destinations = zones.filter(
            (f) => f.properties.type === "destination"
          );

          function centroid(feature) {
            let coords;

            if (feature.geometry.type === "Polygon")
              coords = feature.geometry.coordinates[0];

            if (feature.geometry.type === "MultiPolygon")
              coords = feature.geometry.coordinates[0][0];

            let x = 0;
            let y = 0;

            coords.forEach((c) => {
              x += c[0];
              y += c[1];
            });

            return [x / coords.length, y / coords.length];
          }

          // ======================
          // Regional clustering
          // ======================

          function cluster(features, cellSize = 1.5) {
            const grid = {};

            features.forEach((f) => {
              const c = centroid(f);

              const gx = Math.floor(c[0] / cellSize);
              const gy = Math.floor(c[1] / cellSize);

              const key = `${gx}_${gy}`;

              if (!grid[key]) grid[key] = [];

              grid[key].push(f);
            });

            return Object.values(grid).map((cluster) => {
              let sx = 0;
              let sy = 0;
              let pressure = 0;

              cluster.forEach((f) => {
                const c = centroid(f);
                sx += c[0];
                sy += c[1];
                pressure += Math.abs(f.properties.pressure || 0);
              });

              return {
                coord: [sx / cluster.length, sy / cluster.length],
                pressure: pressure / cluster.length,
              };
            });
          }

          const sourceClusters = cluster(sources);
          const destClusters = cluster(destinations);

          const flows = [];

          sourceClusters.forEach((src) => {
            let nearest = null;
            let minDist = Infinity;

            destClusters.forEach((dest) => {
              const dx = src.coord[0] - dest.coord[0];
              const dy = src.coord[1] - dest.coord[1];
              const d = Math.sqrt(dx * dx + dy * dy);

              if (d < minDist) {
                minDist = d;
                nearest = dest.coord;
              }
            });

            if (!nearest) return;

            const mid = [
              (src.coord[0] + nearest[0]) / 2,
              (src.coord[1] + nearest[1]) / 2 + 0.4,
            ];

            const points = [];
            const steps = 20;

            for (let t = 0; t <= 1; t += 1 / steps) {
              const x =
                (1 - t) * (1 - t) * src.coord[0] +
                2 * (1 - t) * t * mid[0] +
                t * t * nearest[0];

              const y =
                (1 - t) * (1 - t) * src.coord[1] +
                2 * (1 - t) * t * mid[1] +
                t * t * nearest[1];

              points.push([x, y]);
            }

            flows.push({
              type: "Feature",
              properties: { weight: src.pressure },
              geometry: {
                type: "LineString",
                coordinates: points,
              },
            });
          });

          const flowGeoJSON = {
            type: "FeatureCollection",
            features: flows,
          };

          map.addSource("migration-flows", {
            type: "geojson",
            data: flowGeoJSON,
          });

          map.addLayer({
            id: "migration-flow-lines",
            type: "line",
            source: "migration-flows",
            paint: {
              "line-color": "#ff8800",
              "line-width": [
                "interpolate",
                ["linear"],
                ["get", "weight"],
                0, 2,
                1, 8,
              ],
              "line-opacity": 0.9,
            },
          });

          map.addLayer({
            id: "migration-flow-arrows",
            type: "symbol",
            source: "migration-flows",
            layout: {
              "symbol-placement": "line",
              "symbol-spacing": 80,
              "icon-image": "triangle-15",
              "icon-size": 0.8,
            },
            paint: {
              "icon-color": "#ff8800",
            },
          });
        });

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
          <div><b>Status:</b> Elevated migration pressure</div>
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