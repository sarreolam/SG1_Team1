import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import rankData from "../../data/household_rankings.json";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"];

const METRICS = [
  { key: "total_generation_kwh", label: "Generation (kWh)" },
  { key: "total_load_kwh", label: "Consumption (kWh)" },
  { key: "total_import_kwh", label: "Import (kWh)" },
  { key: "total_export_kwh", label: "Export (kWh)" },
  { key: "avg_soc_pct", label: "Average battery (%)" },
];

const NAME_MAP = {
  studio_low_01: "Studio (Low)",
  family_high_01: "Small family (High)",
  family_mid_01: "Small family (Medium)",
  large_luxury_01: "Large family (Luxury)",
};

export default function HouseholdComparison() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 700;
    const height = 340;
    const margin = { top: 20, right: 20, bottom: 60, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const households = rankData.map((d) => ({
      ...d,
      name: NAME_MAP[d.household_name] || d.household_name,
    }));

    const x0 = d3
      .scaleBand()
      .domain(METRICS.map((m) => m.label))
      .range([0, innerW])
      .paddingInner(0.18)
      .paddingOuter(0.08);

    const x1 = d3
      .scaleBand()
      .domain(households.map((h) => h.name))
      .range([0, x0.bandwidth()])
      .padding(0.06);

    // Normalize each metric separately
    const yScales = {};
    METRICS.forEach((m) => {
      const maxVal = d3.max(households, (h) => h[m.key]);
      yScales[m.key] = d3.scaleLinear().domain([0, maxVal * 1.12]).nice().range([innerH, 0]);
    });

    // We'll use a shared y scale based on normalized (0-100) values for grouped view
    const yShared = d3.scaleLinear().domain([0, 100]).range([innerH, 0]);

    // Normalize values to 0-100 per metric
    const normalized = METRICS.map((m) => {
      const maxVal = d3.max(households, (h) => h[m.key]);
      return households.map((h) => ({
        metric: m.label,
        metricKey: m.key,
        household: h.name,
        raw: h[m.key],
        norm: maxVal > 0 ? (h[m.key] / maxVal) * 100 : 0,
      }));
    }).flat();

    // Grid
    g.append("g")
      .call(d3.axisLeft(yShared).ticks(5).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Draw bars
    const metricGroups = g
      .selectAll(".metric-group")
      .data(METRICS)
      .join("g")
      .attr("class", "metric-group")
      .attr("transform", (d) => `translate(${x0(d.label)},0)`);

    metricGroups
      .selectAll("rect")
      .data((m) =>
        households.map((h) => {
          const maxVal = d3.max(households, (hh) => hh[m.key]);
          return {
            household: h.name,
            raw: h[m.key],
            norm: maxVal > 0 ? (h[m.key] / maxVal) * 100 : 0,
            metricKey: m.key,
          };
        })
      )
      .join("rect")
      .attr("x", (d) => x1(d.household))
      .attr("y", (d) => yShared(d.norm))
      .attr("width", x1.bandwidth())
      .attr("height", (d) => innerH - yShared(d.norm))
      .attr("fill", (d, i) => COLORS[i % COLORS.length])
      .attr("rx", 3)
      .attr("opacity", 0.85);

    // X axis - metric labels
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x0))
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g
          .selectAll(".tick text")
          .attr("fill", "#475569")
          .attr("font-size", "10px")
          .call(wrapText, x0.bandwidth())
      );

    // Y axis
    g.append("g")
      .call(
        d3.axisLeft(yShared).ticks(5).tickFormat((d) => `${d.toFixed(0)}%`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Y axis label
    svg
      .append("text")
      .attr("transform", `rotate(-90)`)
      .attr("y", 12)
      .attr("x", -(margin.top + innerH / 2))
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#94a3b8")
      .text("Relative value (100% = max)");

    // Legend
    const leg = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${height - 14})`);

    households.forEach((h, i) => {
      const gItem = leg
        .append("g")
        .attr("transform", `translate(${i * (innerW / 4)},0)`);
      gItem
        .append("rect")
        .attr("width", 12)
        .attr("height", 12)
        .attr("rx", 2)
        .attr("fill", COLORS[i])
        .attr("opacity", 0.85);
      gItem
        .append("text")
        .attr("x", 16)
        .attr("y", 10)
        .attr("fill", "#475569")
        .attr("font-size", "10px")
        .text(h.name);
    });

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".hh-tooltip")
      .data([null])
      .join("div")
      .attr("class", "hh-tooltip")
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

    metricGroups
      .selectAll("rect")
      .on("mousemove", function (event, d) {
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>${d.household}</b><br/>Value: <b>${d.raw.toFixed(2)}</b><br/>Relative: <b>${d.norm.toFixed(1)}%</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));

    function wrapText(text, width) {
      text.each(function () {
        const t = d3.select(this);
        const words = t.text().split(/\s+/).reverse();
        let word,
          line = [],
          lineNumber = 0,
          lineHeight = 1.1,
          y = t.attr("y"),
          dy = parseFloat(t.attr("dy") || 0);
        let tspan = t
          .text(null)
          .append("tspan")
          .attr("x", 0)
          .attr("y", y)
          .attr("dy", dy + "em");
        while ((word = words.pop())) {
          line.push(word);
          tspan.text(line.join(" "));
          if (tspan.node().getComputedTextLength() > width - 4) {
            line.pop();
            tspan.text(line.join(" "));
            line = [word];
            tspan = t
              .append("tspan")
              .attr("x", 0)
              .attr("y", y)
              .attr("dy", ++lineNumber * lineHeight + dy + "em")
              .text(word);
          }
        }
      });
    }
  }, []);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          Household comparison (relative to maximum values)
        </h3>
        <p style={{ margin: "4px 0 0", fontSize: 12, color: "#94a3b8" }}>
          Each bar shows the percentage of the maximum value among households for that metric
        </p>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
