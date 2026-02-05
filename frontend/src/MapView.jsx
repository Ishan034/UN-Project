import React, { useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css"; // ✅ FIX 1: Mapbox CSS

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

export default function MapView() {
  useEffect(() => {
    // 1️⃣ Correct POST request to backend
    fetch("https://un-project-4ajo.onrender.com/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}), // placeholder payload
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("Prediction response from backend:", data);
      })
      .catch((err) => {
        console.error("Backend connection error:", err);
      });

    // 2️⃣ Initialize Mapbox map
    const map = new mapboxgl.Map({
      container: "map",
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.5, 7.3], // South Sudan
      zoom: 5,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

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
