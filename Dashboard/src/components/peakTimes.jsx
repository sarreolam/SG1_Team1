import { useEffect, useRef } from "react";
import * as d3 from "d3";
import tsData from "../../data/timeseries_neighborhood.json";

export default function PeakTimes() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 500;
    const height = 320;
    const margin = { top: 16, right: 20, bottom: 50, left: 46 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    // Build hour × day matrix (avg load_kw)
    const days = [...new Set(tsData.map((d) => d.day))].sort((a, b) => a - b);
    const hours = Array.from({ length: 24 }, (_, i) => i);

    const matrix = [];
    days.forEach((day) => {
      hours.forEach((hour) => {
        const rows = tsData.filter((d) => d.day === day && d.hour === hour);
        const load = rows.length ? d3.mean(rows, (r) => r.load_kw) : 0;
        const solar = rows.length ? d3.mean(rows, (r) => r.solar_kw_used) : 0;
        matrix.push({ day, hour, load, solar });
      });
    });

    const cellW = innerW / days.length;
    const cellH = innerH / hours.length;

    const maxLoad = d3.max(matrix, (d) => d.load);
    const colorScale = d3
      .scaleSequential()
      .domain([0, maxLoad])
      .interpolator(d3.interpolateYlOrRd);

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Cells
    g.selectAll(".cell")
      .data(matrix)
      .join("rect")
      .attr("class", "cell")
      .attr("x", (d) => (d.day - 1) * cellW)
      .attr("y", (d) => d.hour * cellH)
      .attr("width", cellW - 0.5)
      .attr("height", cellH - 0.5)
      .attr("fill", (d) => colorScale(d.load))
      .attr("rx", 0);

    // Hour axis (y)
    const yHour = d3
      .scaleLinear()
      .domain([0, 24])
      .range([0, innerH]);

    g.append("g")
      .call(
        d3
          .axisLeft(yHour)
          .tickValues([0, 6, 12, 18, 24])
          .tickFormat((d) => `${String(d).padStart(2, "0")}:00`)
      )
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      )
      .call((g) => g.selectAll(".tick line").attr("stroke", "none"));

    // Day axis (x)
    const xDay = d3
      .scaleLinear()
      .domain([1, days.length + 1])
      .range([0, innerW]);

    const showEvery = Math.ceil(days.length / 8);
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(xDay)
          .tickValues(days.filter((d) => d % showEvery === 1 || d === 1))
          .tickFormat((d) => `D${d}`)
      )
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Color legend bar
    const legendW = Math.min(innerW * 0.5, 160);
    const legG = svg
      .append("g")
      .attr(
        "transform",
        `translate(${margin.left + innerW - legendW},${height - margin.bottom + 28})`
      );

    const defs = svg.append("defs");
    const grad = defs
      .append("linearGradient")
      .attr("id", "peak-grad")
      .attr("x1", "0%")
      .attr("x2", "100%");
    grad.append("stop").attr("offset", "0%").attr("stop-color", colorScale(0));
    grad.append("stop").attr("offset", "100%").attr("stop-color", colorScale(maxLoad));

    legG
      .append("rect")
      .attr("width", legendW)
      .attr("height", 8)
      .attr("rx", 4)
      .attr("fill", "url(#peak-grad)");
    legG
      .append("text")
      .attr("y", 20)
      .attr("font-size", "10px")
      .attr("fill", "#94a3b8")
      .text("Bajo");
    legG
      .append("text")
      .attr("x", legendW)
      .attr("y", 20)
      .attr("text-anchor", "end")
      .attr("font-size", "10px")
      .attr("fill", "#94a3b8")
      .text(`Alto (${maxLoad.toFixed(1)} kW)`);

    // Title in legend area
    svg
      .append("text")
      .attr("x", margin.left)
      .attr("y", height - margin.bottom + 36)
      .attr("font-size", "10px")
      .attr("fill", "#94a3b8")
      .text("Intensidad de demanda (kW)");

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".peak-tooltip")
      .data([null])
      .join("div")
      .attr("class", "peak-tooltip")
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

    g.selectAll(".cell")
      .on("mousemove", function (event, d) {
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>Día ${d.day} · ${String(d.hour).padStart(2, "0")}:00h</b><br/>
            Demanda: <b>${d.load.toFixed(2)} kW</b><br/>
            Solar: <b>${d.solar.toFixed(2)} kW</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, []);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
          Mapa de calor — Picos de demanda
        </h3>
        <p style={{ margin: "3px 0 0", fontSize: 12, color: "#94a3b8" }}>
          Hora del día vs. día del mes · Color = intensidad de carga
        </p>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
