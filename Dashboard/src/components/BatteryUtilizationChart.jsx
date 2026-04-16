import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import tsData from "../../data/timeseries_neighborhood.json";

export default function BatteryUtilizationChart() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedDay, setSelectedDay] = useState(1);
  const [showAll, setShowAll] = useState(false);

  const days = [...new Set(tsData.map((d) => d.day))].sort((a, b) => a - b);
  const maxDay = Math.max(...days);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const filtered = showAll ? tsData : tsData.filter((d) => d.day === selectedDay);

    const width = containerRef.current.clientWidth || 450;
    const height = 300;
    const margin = { top: 20, right: 20, bottom: 55, left: 55 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleLinear()
      .domain([0, filtered.length - 1])
      .range([0, innerW]);

    const maxSOC = d3.max(tsData, (d) => d.battery_soc_kwh);
    const y = d3.scaleLinear().domain([0, maxSOC * 1.08]).nice().range([innerH, 0]);

    // Color zones
    const dangerY = y(maxSOC * 0.15);
    const safeY = y(maxSOC * 0.8);

    // Zone fills
    g.append("rect")
      .attr("x", 0)
      .attr("width", innerW)
      .attr("y", dangerY)
      .attr("height", innerH - dangerY)
      .attr("fill", "#fef2f2")
      .attr("opacity", 0.6);

    g.append("rect")
      .attr("x", 0)
      .attr("width", innerW)
      .attr("y", 0)
      .attr("height", safeY)
      .attr("fill", "#f0fdf4")
      .attr("opacity", 0.5);

    // Zone labels
    g.append("text")
      .attr("x", innerW - 4)
      .attr("y", dangerY - 4)
      .attr("text-anchor", "end")
      .attr("fill", "#ef4444")
      .attr("font-size", "10px")
      .text("Critical zone");

    g.append("text")
      .attr("x", innerW - 4)
      .attr("y", safeY + 12)
      .attr("text-anchor", "end")
      .attr("fill", "#10b981")
      .attr("font-size", "10px")
      .text("Optimal zone");

    // Grid
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // SOC area
    const area = d3
      .area()
      .x((_, i) => x(i))
      .y0(innerH)
      .y1((d) => y(d.battery_soc_kwh))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(filtered)
      .attr("fill", "url(#soc-grad)")
      .attr("d", area);

    // SOC line
    const line = d3
      .line()
      .x((_, i) => x(i))
      .y((d) => y(d.battery_soc_kwh))
      .curve(d3.curveCatmullRom);

    // Gradient
    const defs = svg.append("defs");
    const grad = defs
      .append("linearGradient")
      .attr("id", "soc-grad")
      .attr("x1", "0%")
      .attr("x2", "0%")
      .attr("y1", "0%")
      .attr("y2", "100%");
    grad.append("stop").attr("offset", "0%").attr("stop-color", "#8b5cf6").attr("stop-opacity", 0.4);
    grad.append("stop").attr("offset", "100%").attr("stop-color", "#8b5cf6").attr("stop-opacity", 0.02);

    g.append("path")
      .datum(filtered)
      .attr("fill", "none")
      .attr("stroke", "#8b5cf6")
      .attr("stroke-width", 2.5)
      .attr("d", line);

    // Solar generation line
    const lineSolar = d3
      .line()
      .x((_, i) => x(i))
      .y((d) => y(Math.min(d.solar_kw_used * (maxSOC / 10), maxSOC)))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(filtered)
      .attr("fill", "none")
      .attr("stroke", "#f59e0b")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "5,3")
      .attr("opacity", 0.7)
      .attr("d", lineSolar);

    // Axes
    const xAxisData = showAll
      ? d3
          .axisBottom(x)
          .ticks(8)
          .tickFormat((i) => {
            const d = filtered[Math.round(i)];
            return d ? `D${d.day}` : "";
          })
      : d3
          .axisBottom(x)
          .ticks(6)
          .tickFormat((i) => {
            const d = filtered[Math.round(i)];
            return d ? `${String(d.hour).padStart(2, "0")}:00` : "";
          });

    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(xAxisData)
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d.toFixed(1)} kWh`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Stats
    const avgSOC = d3.mean(filtered, (d) => d.battery_soc_kwh);
    const minSOC = d3.min(filtered, (d) => d.battery_soc_kwh);

    // Avg line
    g.append("line")
      .attr("x1", 0)
      .attr("x2", innerW)
      .attr("y1", y(avgSOC))
      .attr("y2", y(avgSOC))
      .attr("stroke", "#8b5cf6")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "8,4")
      .attr("opacity", 0.5);

    g.append("text")
      .attr("x", 4)
      .attr("y", y(avgSOC) - 4)
      .attr("fill", "#8b5cf6")
      .attr("font-size", "10px")
      .text(`Average: ${avgSOC.toFixed(1)} kWh`);

    // Legend
    const leg = svg.append("g").attr("transform", `translate(${margin.left},${height - 14})`);
    [
      { label: "State of charge (SOC)", color: "#8b5cf6", dash: null },
      { label: "Solar generated (scaled)", color: "#f59e0b", dash: "5,3" },
    ].forEach((item, i) => {
      const gItem = leg.append("g").attr("transform", `translate(${i * 190},0)`);
      gItem
        .append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 4)
        .attr("y2", 4)
        .attr("stroke", item.color)
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", item.dash);
      gItem
        .append("text")
        .attr("x", 24)
        .attr("y", 8)
        .attr("fill", "#475569")
        .attr("font-size", "11px")
        .text(item.label);
    });

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".batt-tooltip")
      .data([null])
      .join("div")
      .attr("class", "batt-tooltip")
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

    svg
      .append("rect")
      .attr("width", innerW)
      .attr("height", innerH)
      .attr("transform", `translate(${margin.left},${margin.top})`)
      .attr("fill", "none")
      .attr("pointer-events", "all")
      .on("mousemove", function (event) {
        const [mx] = d3.pointer(event, this);
        const idx = Math.round(x.invert(mx));
        const d = filtered[Math.max(0, Math.min(idx, filtered.length - 1))];
        if (!d) return;
        const soc_pct = ((d.battery_soc_kwh / maxSOC) * 100).toFixed(1);
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>Day ${d.day} · ${String(d.hour).padStart(2, "0")}:00h</b><br/>
            SOC: <b>${d.battery_soc_kwh.toFixed(2)} kWh (${soc_pct}%)</b><br/>
            Solar: <b>${d.solar_kw_used.toFixed(2)} kW</b><br/>
            Cloud: <b>${(d.cloud_coverage_avg * 100).toFixed(0)}%</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, [selectedDay, showAll]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          Battery utilization
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#64748b" }}>
            <input
              type="checkbox"
              checked={showAll}
              onChange={(e) => setShowAll(e.target.checked)}
              style={{ accentColor: "#8b5cf6" }}
            />
            show full month
          </label>
          {!showAll && (
            <>
              <span style={{ fontSize: 12, color: "#64748b" }}>Day {selectedDay}</span>
              <input
                type="range"
                min={1}
                max={maxDay}
                value={selectedDay}
                onChange={(e) => setSelectedDay(Number(e.target.value))}
                style={{ flex: 1, minWidth: 80, accentColor: "#8b5cf6" }}
              />
            </>
          )}
        </div>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
