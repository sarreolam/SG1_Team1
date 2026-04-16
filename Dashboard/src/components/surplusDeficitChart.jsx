import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import tsData from "../../data/timeseries_neighborhood.json";

export default function SurplusDeficitChart() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [view, setView] = useState("daily"); // "daily" | "hourly"

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    let data;

    if (view === "daily") {
      const days = [...new Set(tsData.map((d) => d.day))].sort((a, b) => a - b);
      data = days.map((day) => {
        const rows = tsData.filter((d) => d.day === day);
        const production = d3.sum(rows, (d) => d.solar_kw_used);
        const consumption = d3.sum(rows, (d) => d.load_kw);
        return {
          label: `D${day}`,
          balance: production - consumption,
          import: d3.sum(rows, (d) => d.grid_import_kwh),
          export: d3.sum(rows, (d) => d.grid_export_kwh),
        };
      });
    } else {
      data = Array.from({ length: 24 }, (_, h) => {
        const rows = tsData.filter((d) => d.hour === h);
        const production = d3.mean(rows, (d) => d.solar_kw_used);
        const consumption = d3.mean(rows, (d) => d.load_kw);
        return {
          label: `${String(h).padStart(2, "0")}:00`,
          balance: production - consumption,
          import: d3.mean(rows, (d) => d.grid_import_kwh),
          export: d3.mean(rows, (d) => d.grid_export_kwh),
        };
      });
    }

    const width = containerRef.current.clientWidth || 500;
    const height = 300;
    const margin = { top: 16, right: 20, bottom: 50, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(data.map((d) => d.label))
      .range([0, innerW])
      .padding(0.2);

    const maxAbs = d3.max(data, (d) => Math.abs(d.balance));
    const y = d3.scaleLinear().domain([-maxAbs * 1.15, maxAbs * 1.15]).nice().range([innerH, 0]);

    // Grid
    g.append("g")
      .call(d3.axisLeft(y).ticks(6).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Zero line
    g.append("line")
      .attr("x1", 0)
      .attr("x2", innerW)
      .attr("y1", y(0))
      .attr("y2", y(0))
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", 1.5);

    // Bars
    g.selectAll(".bar")
      .data(data)
      .join("rect")
      .attr("class", "bar")
      .attr("x", (d) => x(d.label))
      .attr("y", (d) => (d.balance >= 0 ? y(d.balance) : y(0)))
      .attr("width", x.bandwidth())
      .attr("height", (d) =>
        d.balance >= 0 ? y(0) - y(d.balance) : y(d.balance) - y(0)
      )
      .attr("fill", (d) => (d.balance >= 0 ? "#10b981" : "#ef4444"))
      .attr("rx", 3)
      .attr("opacity", 0.82);

    // Area chart for import/export overlay (line)
    const lineExport = d3
      .line()
      .x((d) => x(d.label) + x.bandwidth() / 2)
      .y((d) => y(d.export))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#f59e0b")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,3")
      .attr("d", lineExport);

    // Axes
    const showEvery = view === "daily" ? Math.ceil(data.length / 8) : 1;
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(data.filter((_, i) => i % showEvery === 0).map((d) => d.label))
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(6)
          .tickFormat((d) => `${d.toFixed(1)} kW`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Annotations
    g.append("text")
      .attr("x", 6)
      .attr("y", y(maxAbs * 0.9))
      .attr("fill", "#10b981")
      .attr("font-size", "10px")
      .attr("font-weight", 600)
      .text("↑ Superávit");

    g.append("text")
      .attr("x", 6)
      .attr("y", y(-maxAbs * 0.9))
      .attr("fill", "#ef4444")
      .attr("font-size", "10px")
      .attr("font-weight", 600)
      .text("↓ Déficit");

    // Legend
    const leg = svg
      .append("g")
      .attr("transform", `translate(${margin.left + 10},${height - 14})`);

    [
      { label: "Superávit solar", color: "#10b981", rect: true },
      { label: "Déficit solar", color: "#ef4444", rect: true },
      { label: "Exportación a red", color: "#f59e0b", rect: false },
    ].forEach((item, i) => {
      const gItem = leg.append("g").attr("transform", `translate(${i * 155},0)`);
      if (item.rect) {
        gItem
          .append("rect")
          .attr("width", 12)
          .attr("height", 12)
          .attr("rx", 2)
          .attr("fill", item.color)
          .attr("opacity", 0.82);
      } else {
        gItem
          .append("line")
          .attr("x1", 0)
          .attr("x2", 18)
          .attr("y1", 6)
          .attr("y2", 6)
          .attr("stroke", item.color)
          .attr("stroke-width", 2)
          .attr("stroke-dasharray", "5,3");
      }
      gItem
        .append("text")
        .attr("x", item.rect ? 16 : 22)
        .attr("y", 10)
        .attr("fill", "#475569")
        .attr("font-size", "11px")
        .text(item.label);
    });

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".surplus-tooltip")
      .data([null])
      .join("div")
      .attr("class", "surplus-tooltip")
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

    g.selectAll(".bar")
      .on("mousemove", function (event, d) {
        const sign = d.balance >= 0 ? "Superávit" : "Déficit";
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>${d.label}</b><br/>${sign}: <b>${Math.abs(d.balance).toFixed(2)} kW</b><br/>
            Exportado: <b>${d.export.toFixed(2)} kW</b><br/>
            Importado: <b>${d.import.toFixed(2)} kW</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, [view]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          Superávit / Déficit energético
        </h3>
        <div style={{ display: "flex", gap: 6 }}>
          {["daily", "hourly"].map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                padding: "3px 12px",
                borderRadius: 20,
                border: "1.5px solid",
                borderColor: view === v ? "#10b981" : "#e2e8f0",
                background: view === v ? "#ecfdf5" : "#fff",
                color: view === v ? "#10b981" : "#64748b",
                fontSize: 12,
                cursor: "pointer",
                fontWeight: view === v ? 600 : 400,
              }}
            >
              {v === "daily" ? "Por día" : "Por hora"}
            </button>
          ))}
        </div>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
