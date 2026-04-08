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
  const [zonesCount, setZonesCount] = useState(0);
  const [data, setData] = useState([]);

  const [fullData, setFullData] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);

  useEffect(function () {

    fetch("https://un-project-4ajo.onrender.com/predict")
      .then(function (res) { return res.json(); })
      .then(function (d) {

        setConfidence(d.confidence || 0);
        setLeadTime(d.lead_time_days || 0);
        setZonesCount(d.zones?.features?.length || 0);

        setFullData(d);

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

  const zones = fullData?.zones?.features || [];

  const sortedZones = [...zones].sort(
    (a, b) =>
      Math.abs(b.properties?.pressure || 0) -
      Math.abs(a.properties?.pressure || 0)
  );

  const topZones = sortedZones.slice(0, 6);

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
          <MetricCard title="Confidence" value={(confidence * 100).toFixed(1) + "%"} />
          <MetricCard title="Lead Time" value={leadTime + " days"} />
          <MetricCard title="Active Zones" value={zonesCount} />
          <MetricCard title="Validation" value={(fullData?.validation_score * 100 || 0).toFixed(1) + "%"} />
          <MetricCard title="Drivers" value={(fullData?.driver_score * 100 || 0).toFixed(1) + "%"} />
          <MetricCard title="Risk" value={fullData?.risk_level || "N/A"} />
        </div>

        {/* SIGNAL BARS (NEW) */}
        <Card title="Model Signal Strength">
          <Bar label="Confidence" value={confidence} />
          <Bar label="Validation" value={fullData?.validation_score || 0} />
          <Bar label="Driver Strength" value={fullData?.driver_score || 0} />
        </Card>

        {/* GRID */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: "20px",
          marginTop: "20px"
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

          {/* REGIONS */}
          <Card title="High Pressure Regions">
            {topZones.map(function (z, i) {
              var p = Math.abs(z.properties?.pressure || 0);

              return (
                <div
                  key={i}
                  onClick={() => setSelectedZone(z)}
                  style={{
                    padding: "8px",
                    marginBottom: "8px",
                    background: "#020617",
                    borderRadius: "6px",
                    cursor: "pointer"
                  }}
                >
                  <div>{z.properties?.type}</div>
                  <div style={{ fontSize: "12px", opacity: 0.7 }}>
                    Pressure: {p.toFixed(3)}
                  </div>
                </div>
              );
            })}
          </Card>

        </div>

        {/* VALIDATION */}
        <div style={{ marginTop: "24px" }}>
          <Card title="Validation Breakdown">
            <Bar label="Alignment" value={(fullData?.validation_score || 0) * 0.4} />
            <Bar label="Direction" value={(fullData?.validation_score || 0) * 0.4} />
            <Bar label="Stability" value={(fullData?.validation_score || 0) * 0.2} />
          </Card>
        </div>

      </div>

      {/* DETAIL PANEL */}
      {selectedZone && (
        <div style={{
          position: "fixed",
          right: 0,
          top: 0,
          width: "320px",
          height: "100%",
          background: "#020617",
          padding: "20px"
        }}>
          <button onClick={() => setSelectedZone(null)}>Close</button>

          <h2>Region Analysis</h2>

          <p><b>Type:</b> {selectedZone.properties?.type}</p>
          <p><b>Pressure:</b> {selectedZone.properties?.pressure}</p>

          <h3>Drivers</h3>
          <p>NDVI: {selectedZone.properties?.ndvi}</p>
          <p>Rainfall: {selectedZone.properties?.rain}</p>
          <p>Conflict: {selectedZone.properties?.conflict}</p>
        </div>
      )}
    </div>
  );
}

/* COMPONENTS */

function Card(props) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.05)",
      padding: "16px",
      borderRadius: "16px"
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

/* BAR COMPONENT (NEW) */
function Bar({ label, value }) {
  return (
    <div style={{ marginBottom: "10px" }}>
      <div style={{ fontSize: "12px", marginBottom: "4px" }}>
        {label} ({(value * 100).toFixed(1)}%)
      </div>
      <div style={{
        width: "100%",
        height: "8px",
        background: "#334155",
        borderRadius: "4px"
      }}>
        <div style={{
          width: `${Math.min(value * 100, 100)}%`,
          height: "100%",
          background: "#22c55e",
          borderRadius: "4px"
        }} />
      </div>
    </div>
  );
}