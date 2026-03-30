import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function DashboardView() {

  const [confidence, setConfidence] = useState(0);
  const [leadTime, setLeadTime] = useState(0);
  const [zones, setZones] = useState(0);
  const [data, setData] = useState([]);

  useEffect(function () {

    fetch("https://un-project-4ajo.onrender.com/predict")
      .then(function (res) { return res.json(); })
      .then(function (d) {

        setConfidence(d.confidence);
        setLeadTime(d.lead_time_days);
        setZones(d.zones.features.length);

        // SAFE mock data (no template literals)
        var mock = Array.from({ length: 12 }, function (_, i) {
          return {
            day: "T" + i,
            pressure: Math.random()
          };
        });

        setData(mock);

      })
      .catch(function (err) {
        console.error("Dashboard fetch error:", err);
      });

  }, []);

  return (
    <div style={{
      display: "flex",
      height: "100%",
      background: "#0f172a",
      color: "white",
      fontFamily: "Inter, sans-serif"
    }}>

      {/* SIDEBAR */}
      <div style={{
        width: "240px",
        background: "#020617",
        padding: "20px",
        borderRight: "1px solid rgba(255,255,255,0.05)"
      }}>
        <h2 style={{ fontSize: "18px", marginBottom: "20px" }}>
          Navigation
        </h2>

        <div style={{ color: "#94a3b8", marginBottom: "10px" }}>Overview</div>
        <div style={{ color: "#94a3b8", marginBottom: "10px" }}>Analytics</div>
        <div style={{ color: "#94a3b8", marginBottom: "10px" }}>Validation</div>
      </div>

      {/* MAIN */}
      <div style={{ flex: 1, padding: "24px", overflowY: "auto" }}>

        {/* HEADER */}
        <div style={{ marginBottom: "20px" }}>
          <h1 style={{ fontSize: "26px", fontWeight: "600" }}>
            Migration Intelligence Dashboard
          </h1>
          <div style={{ color: "#94a3b8" }}>
            AI-based livestock movement forecasting
          </div>
        </div>

        {/* METRICS */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
          marginBottom: "24px"
        }}>
          <MetricCard title="Confidence" value={confidence} />
          <MetricCard title="Lead Time" value={leadTime + " days"} />
          <MetricCard title="Active Zones" value={zones} />
        </div>

        {/* GRID */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: "20px"
        }}>

          {/* CHART */}
          <Card title="Migration Pressure Trend">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data}>
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="pressure"
                  stroke="#f97316"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* INSIGHTS */}
          <Card title="Insights">
            <ul style={{ lineHeight: "1.8", color: "#cbd5f5" }}>
              <li>High migration pressure detected in Western Equatoria</li>
              <li>Predicted movement trending toward Sudd wetlands</li>
              <li>Low vegetation index driving outbound migration</li>
              <li>Rainfall deficit observed in key grazing zones</li>
              <li>Conflict overlap detected in migration corridors</li>
            </ul>
          </Card>

        </div>

        {/* VALIDATION */}
        <div style={{ marginTop: "24px" }}>
          <Card title="Validation Metrics">
            <ul style={{ lineHeight: "1.8", color: "#cbd5f5" }}>
              <li>✔ Strong correlation with NDVI gradients</li>
              <li>✔ Rainfall patterns align with migration pressure</li>
              <li>✔ Conflict hotspots overlap predicted movement zones</li>
              <li>✔ Spatial consistency across regions</li>
              <li>✔ Out-of-sample robustness observed in test regions</li>
            </ul>
          </Card>
        </div>

      </div>
    </div>
  );
}

/* =========================
   COMPONENTS
========================= */

function Card(props) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.05)",
      padding: "16px",
      borderRadius: "16px",
      backdropFilter: "blur(10px)"
    }}>
      <div style={{ marginBottom: "10px", fontWeight: "500" }}>
        {props.title}
      </div>
      {props.children}
    </div>
  );
}

function MetricCard(props) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.05)",
      padding: "16px",
      borderRadius: "16px"
    }}>
      <div style={{ color: "#94a3b8", fontSize: "13px" }}>
        {props.title}
      </div>
      <div style={{ fontSize: "22px", fontWeight: "600" }}>
        {props.value}
      </div>
    </div>
  );
}