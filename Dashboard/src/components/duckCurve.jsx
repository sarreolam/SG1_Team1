import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import duckData from "../../data/duck_curve.json";

export default function DuckCurve() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedDay, setSelectedDay] = useState(1);
  const [maxDay, setMaxDay] = useState(30);

  useEffect(() => {
    const days = [...new Set(duckData.map((d) => d.day))];
    setMaxDay(Math.max(...days));
  }, []);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const dayData = duckData.filter((d) => d.day === selectedDay);

    // Also compute average across all days per hour
    const avgByHour = Array.from({ length: 24 }, (_, h) => {
      const hourRows = duckData.filter((d) => d.hour === h);
      return {
        hour: h,
        load_kw: d3.mean(hourRows, (d) => d.load_kw),
        solar_kw_used: d3.mean(hourRows, (d) => d.solar_kw_used),
        net_load_kw: d3.mean(hourRows, (d) => d.net_load_kw),
      };
    });

    const width = containerRef.current.clientWidth || 800;
    const height = 340;
    const margin = { top: 20, right: 30, bottom: 50, left: 60 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain([0, 23]).range([0, innerW]);
    const allVals = [
      ...dayData.map((d) => d.load_kw),
      ...dayData.map((d) => d.net_load_kw),
      ...dayData.map((d) => d.solar_kw_used),
      0,
    ];
    const y = d3
      .scaleLinear()
      .domain([d3.min(allVals) * 0.95, d3.max(allVals) * 1.08])
      .nice()
      .range([innerH, 0]);

    // Grid lines
    g.append("g")
      .attr("class", "grid")
      .call(
        d3
          .axisLeft(y)
          .ticks(6)
          .tickSize(-innerW)
          .tickFormat("")
      )
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g.selectAll(".tick line").attr("stroke", "#e2e8f0").attr("stroke-dasharray", "3,3")
      );

    // Solar area fill
    const areaSolar = d3
      .area()
      .x((d) => x(d.hour))
      .y0(innerH)
      .y1((d) => y(d.solar_kw_used))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(dayData)
      .attr("fill", "#fef08a")
      .attr("opacity", 0.35)
      .attr("d", areaArea(y, x, innerH));

    function areaArea(y, x, innerH) {
      return d3
        .area()
        .x((d) => x(d.hour))
        .y0(innerH)
        .y1((d) => y(d.solar_kw_used))
        .curve(d3.curveCatmullRom)(dayData);
    }

    // Lines
    const lineLoad = d3
      .line()
      .x((d) => x(d.hour))
      .y((d) => y(d.load_kw))
      .curve(d3.curveCatmullRom);

    const lineSolar = d3
      .line()
      .x((d) => x(d.hour))
      .y((d) => y(d.solar_kw_used))
      .curve(d3.curveCatmullRom);

    const lineNet = d3
      .line()
      .x((d) => x(d.hour))
      .y((d) => y(d.net_load_kw))
      .curve(d3.curveCatmullRom);

    // Avg net load (duck curve reference)
    const lineAvgNet = d3
      .line()
      .x((d) => x(d.hour))
      .y((d) => y(d.net_load_kw))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(avgByHour)
      .attr("fill", "none")
      .attr("stroke", "#cbd5e1")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "5,4")
      .attr("d", lineAvgNet);

    g.append("path")
      .datum(dayData)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2.5)
      .attr("d", lineLoad);

    g.append("path")
      .datum(dayData)
      .attr("fill", "none")
      .attr("stroke", "#f59e0b")
      .attr("stroke-width", 2.5)
      .attr("d", lineSolar);

    g.append("path")
      .datum(dayData)
      .attr("fill", "none")
      .attr("stroke", "#10b981")
      .attr("stroke-width", 2.5)
      .attr("stroke-dasharray", "6,3")
      .attr("d", lineNet);

    // Axes
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(12)
          .tickFormat((d) => `${String(d).padStart(2, "0")}:00`)
      )
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) => g.selectAll(".tick line").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "11px")
      );

    g.append("g")
      .call(d3.axisLeft(y).ticks(6).tickFormat((d) => `${d.toFixed(1)} kW`))
      .call((g) => g.select(".domain").attr("stroke", "#cbd5e1"))
      .call((g) => g.selectAll(".tick line").attr("stroke", "#cbd5e1"))
      .call((g) =>
        g.selectAll(".tick text").attr("fill", "#64748b").attr("font-size", "11px")
      );

    // Legend
    const legend = [
    { label: "Total demand", color: "#3b82f6", dash: null },
    { label: "Solar generated", color: "#f59e0b", dash: null },
    { label: "Net load (Duck)", color: "#10b981", dash: "6,3" },
    { label: "Historical average", color: "#cbd5e1", dash: "5,4" },
    ];

    const leg = svg
      .append("g")
      .attr("transform", `translate(${margin.left + 10},${height - 14})`);

    legend.forEach((item, i) => {
      const gItem = leg.append("g").attr("transform", `translate(${i * 170},0)`);
      gItem
        .append("line")
        .attr("x1", 0)
        .attr("x2", 22)
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", item.color)
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", item.dash || null);
      gItem
        .append("text")
        .attr("x", 27)
        .attr("y", 4)
        .attr("fill", "#475569")
        .attr("font-size", "11px")
        .text(item.label);
    });

    // Tooltip
    const tooltip = d3
      .select("body")
      .selectAll(".duck-tooltip")
      .data([null])
      .join("div")
      .attr("class", "duck-tooltip")
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

    const bisect = d3.bisector((d) => d.hour).left;

    svg
      .append("rect")
      .attr("width", innerW)
      .attr("height", innerH)
      .attr("transform", `translate(${margin.left},${margin.top})`)
      .attr("fill", "none")
      .attr("pointer-events", "all")
      .on("mousemove", function (event) {
        const [mx] = d3.pointer(event, this);
        const hour = Math.round(x.invert(mx));
        const idx = bisect(dayData, hour, 0);
        const d = dayData[Math.min(idx, dayData.length - 1)];
        if (!d) return;

        tooltip
          .style("display", "block")
          .style("left", event.clientX + 15 + "px")
          .style("top", event.clientY - 10 + "px")
          .html(
          `<b>${String(d.hour).padStart(2, "0")}:00h — Day ${selectedDay}</b><br/>
          Demand: <b>${d.load_kw.toFixed(2)} kW</b><br/>
          Solar: <b>${d.solar_kw_used.toFixed(2)} kW</b><br/>
          Net: <b>${d.net_load_kw.toFixed(2)} kW</b>`
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));
  }, [selectedDay]);

  return (
    <div ref={containerRef} style={{ width: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
        <label style={{ fontSize: 13, color: "#64748b", fontWeight: 500 }}>
            Day {selectedDay} of {maxDay}
        </label>
        <input
          type="range"
          min={1}
          max={maxDay}
          value={selectedDay}
          onChange={(e) => setSelectedDay(Number(e.target.value))}
          style={{ flex: 1, accentColor: "#10b981" }}
        />
      </div>
      <svg ref={svgRef} style={{ width: "100%", overflow: "visible" }} />
    </div>
  );
}
