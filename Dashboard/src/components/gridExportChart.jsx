import { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import sim_data from "../../../Simulation/Dashboard/data/all_energy_simulations.json";

const GridExportChart = () => {
  const ref = useRef();
  const [householdType, setHouseholdType] = useState("all");

  const householdTypes = useMemo(() => {
    const values = sim_data.simulations.map((sim) => sim.metadata.household_type);
    return ["all", ...new Set(values)];
  }, []);

  useEffect(() => {
    const filtered = sim_data.simulations.filter((sim) =>
      householdType === "all" || sim.metadata.household_type === householdType
    );

    const chartData = filtered.map((sim) => ({
      label: sim.id,
      exported:   sim.summary.total_grid_export_kwh,
      selfUsed:   sim.summary.total_load_kwh - sim.summary.total_grid_import_kwh,
      imported:   sim.summary.total_grid_import_kwh,
    }));

    const width  = 560;
    const height = 320;
    const radius = Math.min(width / chartData.length, height) / 2 - 20;

    const svg = d3.select(ref.current)
      .attr("width", width)
      .attr("height", height);
    svg.selectAll("*").remove();

    if (chartData.length === 0) {
      svg.append("text").attr("x", 20).attr("y", 40)
          .style("fill", "#ccc").text("No data for this filter.");
      return;
    }

    const colors = {
      exported: "#4a90d9",
      selfUsed: "#4caf7d",
      imported: "#e05c5c",
    };
    const labels = {
      exported: "Exported",
      selfUsed: "Self-used",
      imported: "Imported",
    };

    const pie = d3.pie().value((d) => d.value).sort(null);
    const arc = d3.arc().innerRadius(radius * 0.55).outerRadius(radius);

    chartData.forEach((sim, i) => {
      const cx = (width / chartData.length) * i + (width / chartData.length) / 2;
      const cy = height / 2;

      const slices = [
        { key: "exported", value: sim.exported },
        { key: "selfUsed", value: sim.selfUsed },
        { key: "imported", value: sim.imported },
      ];

      const g = svg.append("g").attr("transform", `translate(${cx}, ${cy})`);

      g.selectAll("path")
        .data(pie(slices))
        .enter()
        .append("path")
        .attr("d", arc)
        .attr("fill", (d) => colors[d.data.key])
        .attr("stroke", "none")
        .attr("opacity", 0.9);

      g.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "-0.3em")
        .style("font-size", "11px")
        .style("font-weight", "600")
        .text(sim.label.replace("_", " "));

      g.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "1em")
        .style("font-size", "10px")
        .style("fill", "#888")
        .text(`${sim.exported.toFixed(1)} kWh out`);
    });

    const legend = svg.append("g")
      .attr("transform", `translate(${width / 2 - 120}, ${height - 18})`);

    Object.entries(labels).forEach(([key, label], i) => {
      legend.append("rect")
        .attr("x", i * 100).attr("y", 0)
        .attr("width", 10).attr("height", 10)
        .attr("fill", colors[key]).attr("rx", 2);
      legend.append("text")
        .attr("x", i * 100 + 14).attr("y", 9)
        .style("font-size", "10px")
        .text(label);
    });

  }, [householdType]);

  return (
        <div>
            <div className="chart-filters">
                <select value={householdType} onChange={(e) => setHouseholdType(e.target.value)}>
                    {householdTypes.map((t) => (
                        <option key={t} value={t}>
                            {t === "all" ? "All household types" : t.replace(/_/g, " ")}
                        </option>
                    ))}
                </select>
            </div>
            <svg ref={ref} />
        </div>
    );
};

export default GridExportChart;