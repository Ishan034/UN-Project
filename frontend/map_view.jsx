import React, { useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

export default function MapView() {
  const [map, setMap] = useState(null);

  useEffect(() => {
    const m = new mapboxgl.Map({
      container: "map",
      style: "mapbox://styles/mapbox/light-v11",
      center: [30.5, 7.3], // South Sudan
      zoom: 5,
    });
    setMap(m);
  }, []);

  return <div id="map" style={{ width: "100%", height: "100vh" }} />;
}
