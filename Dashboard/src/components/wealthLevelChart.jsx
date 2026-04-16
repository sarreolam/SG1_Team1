import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import wealthData from "../../data/by_wealth_level.json";

const WEALTH_LABELS = {
  low: "Low",
  middle: "Middle",
  high: "High",
  luxury: "Luxury",
};

const WEALTH_ORDER = ["low", "middle", "high", "luxury"];

export default function WealthLevelChart() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [metric, setMetric] = useState("generation_kwh");

    const metrics = [
    { key: "generation_kwh", label: "Generation (kWh)", color: "#f59e0b" },
    { key: "load_kwh", label: "Consumption (kWh)", color: "#3b82f6" },
    { key: "import_kwh", label: "Import (kWh)", color: "#ef4444" },
    { key: "export_kwh", label: "Export (kWh)", color: "#10b981" },
    { key: "avg_soc_pct", label: "Average battery (%)", color: "#8b5cf6" },
    { key: "net_cost", label: "Net cost ($)", color: "#f97316" },
    ];

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const sorted = WEALTH_ORDER.map((w) => wealthData.find((d) => d.wealth_level === w)).filter(Boolean);
    const currentMetric = metrics.find((m) => m.key === metric);

    const width = containerRef.current.clientWidth || 500;
    const height = 300;
    const margin = { top: 16, right: 20, bottom: 50, left: 70 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(sorted.map((d) => WEALTH_LABELS[d.wealth_level]))
      .range([0, innerW])
      .padding(0.3);

    const maxVal = d3.max(sorted, (d) => d[metric]);
    const minVal = d3.min(sorted, (d) => d[metric]);
    const domainMin = minVal < 0 ? minVal * 1.15 : 0;

    const y = d3
      .scaleLinear()
      .domain([domainMin, maxVal * 1.12])
      .nice()
      .range([innerH, 0]);

    // Grid
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Zero line if needed
    if (minVal < 0) {
      g.append("line")
        .attr("x1", 0)
        .attr("x2", innerW)
        .attr("y1", y(0))
        .attr("y2", y(0))
        .attr("stroke", "#94a3b8")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "4,2");
    }

    // Bars
    const colorScale = d3
      .scaleSequential()
      .domain([0, sorted.length - 1])
      .interpolator(d3.interpolate("#d1fae5", currentMetric.color));

    g.selectAll(".bar")
      .data(sorted)
      .join("rect")
      .attr("class", "bar")
      .attr("x", (d) => x(WEALTH_LABELS[d.wealth_level]))
      .attr("y", (d) => (d[metric] >= 0 ? y(d[metric]) : y(0)))
      .attr("width", x.bandwidth())
      .attr("height", (d) =>
        d[metric] >= 0 ? innerH - y(d[metric]) : y(d[metric]) - y(0)
      )
      .attr("fill", (_, i) => colorScale(i))
      .attr("rx", 5);

    // Value labels on bars
    g.selectAll(".bar-label")
      .data(sorted)
      .join("text")
      .attr("class", "bar-label")
      .attr("x", (d) => x(WEALTH_LABELS[d.wealth_level]) + x.bandwidth() / 2)
      .attr("y", (d) =>
        d[metric] >= 0 ? y(d[metric]) - 6 : y(d[metric]) + 14
      )
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#374151")
      .attr("font-weight", 600)
      .text((d) =>
        metric === "avg_soc_pct"
          ? `${d[metric].toFixed(1)}%`
          : metric === "net_cost"
          ? `$${d[metric].toFixed(2)}`
          : `${d[metric].toFixed(0)}`
      );

    // Axes
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x))
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "12px").attr("font-weight", 500)
      );

    const unit =
      metric === "avg_soc_pct" ? "%" : metric === "net_cost" ? "$" : " kWh";
    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d.toFixed(0)}${unit}`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );
  }, [metric]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 6 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          By wealth level
        </h3>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
          style={{
            padding: "4px 10px",
            borderRadius: 8,
            border: "1.5px solid #e2e8f0",
            fontSize: 12,
            color: "#475569",
            background: "#fff",
            cursor: "pointer",
          }}
        >
          {metrics.map((m) => (
            <option key={m.key} value={m.key}>
              {m.label}
            </option>
          ))}
        </select>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
