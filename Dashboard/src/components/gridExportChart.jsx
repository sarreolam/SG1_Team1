import { useEffect, useRef } from "react";
import * as d3 from "d3";
import tsData from "../../data/timeseries_neighborhood.json";
import hhData from "../../data/by_household_type.json";

const HH_LABELS = {
  studio: "Studio",
  small_family: "Small family",
  large_family: "Large family",
};

const HH_COLORS = {
  studio: "#10b981",
  small_family: "#3b82f6",
  large_family: "#f59e0b",
};

export default function GridExportChart() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 450;
    const height = 300;
    const margin = { top: 20, right: 20, bottom: 60, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Daily export totals from timeseries
    const days = [...new Set(tsData.map((d) => d.day))].sort((a, b) => a - b);
    const dailyExport = days.map((day) => {
      const rows = tsData.filter((d) => d.day === day);
      return {
        day,
        export: d3.sum(rows, (r) => r.grid_export_kwh),
        import: d3.sum(rows, (r) => r.grid_import_kwh),
      };
    });

    // Stacked bars by household type for total export
    const hhTypes = hhData.map((d) => d.household_type);
    const stackData = hhData.map((d) => ({
      type: d.household_type,
      label: HH_LABELS[d.household_type],
      export: d.export_kwh,
      import: d.import_kwh,
      selfConsumption: d.generation_kwh - d.export_kwh,
    }));

    // Top: stacked donut-like view of grid interaction
    // Draw stacked horizontal bars for each hh type
    const maxImport = d3.max(hhData, (d) => d.import_kwh);

    // Left: daily import/export line chart
    const x = d3.scaleLinear().domain([1, d3.max(days)]).range([0, innerW]);
    const maxY = d3.max(dailyExport, (d) => Math.max(d.export, d.import));
    const y = d3.scaleLinear().domain([0, maxY * 1.1]).nice().range([innerH, 0]);

    // Grid
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Area: import
    const areaImport = d3
      .area()
      .x((d) => x(d.day))
      .y0(innerH)
      .y1((d) => y(d.import))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(dailyExport)
      .attr("fill", "#ef444420")
      .attr("d", areaImport);

    // Area: export
    const areaExport = d3
      .area()
      .x((d) => x(d.day))
      .y0(innerH)
      .y1((d) => y(d.export))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(dailyExport)
      .attr("fill", "#10b98120")
      .attr("d", areaExport);

    // Lines
    const lineImport = d3
      .line()
      .x((d) => x(d.day))
      .y((d) => y(d.import))
      .curve(d3.curveCatmullRom);

    const lineExport = d3
      .line()
      .x((d) => x(d.day))
      .y((d) => y(d.export))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(dailyExport)
      .attr("fill", "none")
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("d", lineImport);

    g.append("path")
      .datum(dailyExport)
      .attr("fill", "none")
      .attr("stroke", "#10b981")
      .attr("stroke-width", 2)
      .attr("d", lineExport);

    // Axes
    const showEvery = Math.ceil(days.length / 8);
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(days.filter((d) => d % showEvery === 1 || d === 1))
          .tickFormat((d) => `D${d}`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    g.append("g")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d.toFixed(1)}`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "10px")
      );

    // Y label
    svg
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 12)
      .attr("x", -(margin.top + innerH / 2))
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#94a3b8")
      .text("kWh per day");

    // Mini summary bars at bottom
    const barAreaY = height - 28;
    const barAreaX = margin.left;
    const barTotalW = innerW;
    const totalExport = d3.sum(hhData, (d) => d.export_kwh);
    const totalImport = d3.sum(hhData, (d) => d.import_kwh);
    const total = totalExport + totalImport;

    const leg = svg.append("g").attr("transform", `translate(${margin.left},${height - 22})`);
    [
      { label: "Grid import", color: "#ef4444" },
      { label: "Solar export", color: "#10b981" },
    ].forEach((item, i) => {
      const gItem = leg.append("g").attr("transform", `translate(${i * 160},0)`);
      gItem
        .append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 4)
        .attr("y2", 4)
        .attr("stroke", item.color)
        .attr("stroke-width", 2.5);
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
      .selectAll(".grid-tooltip")
      .data([null])
      .join("div")
      .attr("class", "grid-tooltip")
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
        const day = Math.round(x.invert(mx));
        const d = dailyExport.find((r) => r.day === day);
        if (!d) return;
        tooltip
          .style("display", "block")
          .style("left", event.clientX + 14 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
            `<b>Day ${d.day}</b><br/>
            Exported: <b>${d.export.toFixed(3)} kWh</b><br/>
            Imported: <b>${d.import.toFixed(3)} kWh</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, []);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ marginBottom: 10 }}>
      <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
        Grid export and import
      </h3>
      <p style={{ margin: "3px 0 0", fontSize: 12, color: "#94a3b8" }}>
        Daily energy flow to/from the grid
      </p>
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
