import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import tsData from "../../data/timeseries_neighborhood.json";

export default function ProductionVsConsumption() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [groupBy, setGroupBy] = useState("hour"); // "hour" | "day"

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    let aggregated;
    if (groupBy === "hour") {
      aggregated = Array.from({ length: 24 }, (_, h) => {
        const rows = tsData.filter((d) => d.hour === h);
        return {
          key: h,
          label: `${String(h).padStart(2, "0")}:00`,
          production: d3.mean(rows, (d) => d.solar_kw_used),
          consumption: d3.mean(rows, (d) => d.load_kw),
        };
      });
    } else {
      const days = [...new Set(tsData.map((d) => d.day))].sort((a, b) => a - b);
      aggregated = days.map((day) => {
        const rows = tsData.filter((d) => d.day === day);
        return {
          key: day,
          label: `D${day}`,
          production: d3.sum(rows, (d) => d.solar_kw_used),
          consumption: d3.sum(rows, (d) => d.load_kw),
        };
      });
    }

    const width = containerRef.current.clientWidth || 500;
    const height = 300;
    const margin = { top: 16, right: 20, bottom: 50, left: 55 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const keys = ["production", "consumption"];
    const x0 = d3
      .scaleBand()
      .domain(aggregated.map((d) => d.label))
      .range([0, innerW])
      .paddingInner(0.25)
      .paddingOuter(0.1);

    const x1 = d3.scaleBand().domain(keys).range([0, x0.bandwidth()]).padding(0.08);

    const maxVal = d3.max(aggregated, (d) => Math.max(d.production, d.consumption));
    const y = d3.scaleLinear().domain([0, maxVal * 1.1]).nice().range([innerH, 0]);

    const color = d3.scaleOrdinal().domain(keys).range(["#f59e0b", "#3b82f6"]);

    // Grid
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Bars
    const groups = g
      .selectAll(".bar-group")
      .data(aggregated)
      .join("g")
      .attr("class", "bar-group")
      .attr("transform", (d) => `translate(${x0(d.label)},0)`);

    groups
      .selectAll("rect")
      .data((d) => keys.map((k) => ({ key: k, value: d[k], label: d.label })))
      .join("rect")
      .attr("x", (d) => x1(d.key))
      .attr("y", (d) => y(d.value))
      .attr("width", x1.bandwidth())
      .attr("height", (d) => innerH - y(d.value))
      .attr("fill", (d) => color(d.key))
      .attr("rx", 3)
      .attr("opacity", 0.88);

    // Axes
    const showEvery = groupBy === "day" ? 5 : 1;
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x0)
          .tickValues(aggregated.filter((_, i) => i % showEvery === 0).map((d) => d.label))
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g
          .selectAll(".tick text")
          .attr("fill", "#64748b")
          .attr("font-size", "10px")
          .attr("dy", "1em")
      );

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d.toFixed(0)} kW`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Legend
    const leg = svg
      .append("g")
      .attr("transform", `translate(${margin.left + 10},${height - 10})`);
    [
      { label: "Producción solar", color: "#f59e0b" },
      { label: "Consumo", color: "#3b82f6" },
    ].forEach((item, i) => {
      const gItem = leg.append("g").attr("transform", `translate(${i * 150},0)`);
      gItem
        .append("rect")
        .attr("width", 12)
        .attr("height", 12)
        .attr("rx", 2)
        .attr("fill", item.color)
        .attr("opacity", 0.88);
      gItem
        .append("text")
        .attr("x", 16)
        .attr("y", 10)
        .attr("fill", "#475569")
        .attr("font-size", "11px")
        .text(item.label);
    });

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".pvsc-tooltip")
      .data([null])
      .join("div")
      .attr("class", "pvsc-tooltip")
      .style("position", "fixed")
      .style("background", "rgba(15,23,42,0.92)")
      .style("color", "#f8fafc")
      .style("padding", "10px 14px")
      .style("border-radius", "8px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("display", "none")
      .style("z-index", "9999")
      .style("line-height", "1.7");

    groups
      .selectAll("rect")
      .on("mousemove", function (event, d) {
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>${d.label}</b><br/>${
              d.key === "production" ? "Producción" : "Consumo"
            }: <b>${d.value.toFixed(2)} kW</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, [groupBy]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          Producción vs Consumo
        </h3>
        <div style={{ display: "flex", gap: 6 }}>
          {["hour", "day"].map((v) => (
            <button
              key={v}
              onClick={() => setGroupBy(v)}
              style={{
                padding: "3px 12px",
                borderRadius: 20,
                border: "1.5px solid",
                borderColor: groupBy === v ? "#10b981" : "#e2e8f0",
                background: groupBy === v ? "#ecfdf5" : "#fff",
                color: groupBy === v ? "#10b981" : "#64748b",
                fontSize: 12,
                cursor: "pointer",
                fontWeight: groupBy === v ? 600 : 400,
              }}
            >
              {v === "hour" ? "Por hora" : "Por día"}
            </button>
          ))}
        </div>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
