import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import sim_data from "../../../Simulation/Dashboard/data/all_energy_simulations.json";

const HouseholdComparison = () => {
  const ref = useRef();

  const [householdType, setHouseholdType] = useState("all");
  const [wealthLevel, setWealthLevel] = useState("all");

  const householdTypes = useMemo(() => {
    const values = sim_data.simulations.map((sim) => sim.metadata.household_type);
    return ["all", ...new Set(values)];
  }, []);

  const wealthLevels = useMemo(() => {
    const values = sim_data.simulations.map((sim) => sim.metadata.wealth_level);
    return ["all", ...new Set(values)];
  }, []);

  useEffect(() => {
    const filteredSims = sim_data.simulations.filter((sim) => {
      const matchesHousehold =
        householdType === "all" || sim.metadata.household_type === householdType;

      const matchesWealth =
        wealthLevel === "all" || sim.metadata.wealth_level === wealthLevel;

      return matchesHousehold && matchesWealth;
    });

    const chartData = filteredSims.map((sim) => ({
      label: sim.id,
      production: d3.sum(sim.timeseries, (d) => d.solar_kw),
      consumption: d3.sum(sim.timeseries, (d) => d.load_kw),
    }));

    const subgroups = ["production", "consumption"];
    const colors = { production: "#f0c040", consumption: "#e07b39" };

    const margin = { top: 30, right: 30, bottom: 80, left: 65 };
    const width = 560 - margin.left - margin.right;
    const height = 320 - margin.top - margin.bottom;

    const svg = d3
      .select(ref.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);

    svg.selectAll("*").remove();

    if (chartData.length === 0) {
      svg
        .append("text")
        .attr("x", 20)
        .attr("y", 40)
        .style("fill", "#ccc")
        .style("font-size", "14px")
        .text("No data for this filter.");
      return;
    }

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x0 = d3
      .scaleBand()
      .domain(chartData.map((d) => d.label))
      .range([0, width])
      .padding(0.3);

    const x1 = d3
      .scaleBand()
      .domain(subgroups)
      .range([0, x0.bandwidth()])
      .padding(0.05);

    const maxValue = d3.max(chartData, (d) => Math.max(d.production, d.consumption));

    const y = d3
      .scaleLinear()
      .domain([0, maxValue * 1.15])
      .nice()
      .range([height, 0]);

    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x0))
      .selectAll("text")
      .attr("transform", "rotate(-25)")
      .style("text-anchor", "end");

    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d.toFixed(0)} kW`));

    const groups = g
      .selectAll("g.group")
      .data(chartData)
      .enter()
      .append("g")
      .attr("class", "group")
      .attr("transform", (d) => `translate(${x0(d.label)}, 0)`);

    groups
      .selectAll("rect")
      .data((d) => subgroups.map((key) => ({ key, value: d[key] })))
      .enter()
      .append("rect")
      .attr("x", (d) => x1(d.key))
      .attr("y", (d) => y(d.value))
      .attr("width", x1.bandwidth())
      .attr("height", (d) => height - y(d.value))
      .attr("fill", (d) => colors[d.key])
      .attr("rx", 3);

    const legend = g.append("g").attr("transform", `translate(${width - 140}, 0)`);

    subgroups.forEach((key, i) => {
      legend
        .append("rect")
        .attr("x", 0)
        .attr("y", i * 20)
        .attr("width", 12)
        .attr("height", 12)
        .attr("fill", colors[key])
        .attr("rx", 2);

      legend
        .append("text")
        .attr("x", 16)
        .attr("y", i * 20 + 10)
        .style("font-size", "11px")
        .text(key.charAt(0).toUpperCase() + key.slice(1));
    });
  }, [householdType, wealthLevel]);

  return (
    <div>
      <div className="chart-filters">
        <select value={householdType} onChange={(e) => setHouseholdType(e.target.value)}>
          {householdTypes.map((type) => (
            <option key={type} value={type}>
              {type === "all" ? "All household types" : type}
            </option>
          ))}
        </select>

        <select value={wealthLevel} onChange={(e) => setWealthLevel(e.target.value)}>
          {wealthLevels.map((level) => (
            <option key={level} value={level}>
              {level === "all" ? "All wealth levels" : level}
            </option>
          ))}
        </select>
      </div>

      <svg ref={ref} />
    </div>
  );
};

export default HouseholdComparison;