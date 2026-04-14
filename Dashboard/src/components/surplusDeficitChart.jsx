import { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import sim_data from "../../../Simulation/Dashboard/data/all_energy_simulations.json";

const SurplusDeficitChart = () => {
    const ref = useRef();
    const [householdType, setHouseholdType] = useState("all");

    const householdTypes = useMemo(() => {
        const values = sim_data.simulations.map((sim) => sim.metadata.household_type);
        return ["all", ...new Set(values)];
    }, []);
    
    useEffect(()=>{
        const filtered = sim_data.simulations.filter((sim) => 
            householdType === "all" || sim.metadata.household_type === householdType
        );

        const chartData = filtered.map((sim) => ({
            label:  sim.id,
            surplus: d3.sum(sim.timeseries.filter((d)=> d.net_kwh > 0 ), (d)=> d.net_kwh),
            deficit: d3.sum(sim.timeseries.filter((d)=> d.net_kwh < 0 ), (d)=> -d.net_kwh),
        }));
        
        const margin = { top: 30, right: 30, bottom: 70, left: 70 };
        const width  = 500 - margin.left - margin.right;
        const height = 320 - margin.top  - margin.bottom;

        const svg = d3.select(ref.current)
            .attr("width",  width  + margin.left + margin.right)
            .attr("height", height + margin.top  + margin.bottom);
        svg.selectAll("*").remove();

        if (chartData.length === 0) {
            svg.append("text").attr("x", 20).attr("y", 40).style("fill", "#CCC").text("No data for this filter.");
            return;
        }
        
        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

        const subgroups = ["surplus", "deficit"];
        const colors    = { surplus: "#4caf7d", deficit: "#e05c5c" };

        const x0 = d3.scaleBand()
        .domain(chartData.map((d) => d.label))
        .range([0, width])
        .padding(0.3);

        const x1 = d3.scaleBand()
        .domain(subgroups)
        .range([0, x0.bandwidth()])
        .padding(0.05);

        const y = d3.scaleLinear()
        .domain([0, d3.max(chartData, (d) => Math.max(d.surplus, d.deficit)) * 1.15])
        .nice()
        .range([height, 0]);

        g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x0))
        .selectAll("text")
        .attr("transform", "rotate(-25)")
        .style("text-anchor", "end");

        g.append("g")
        .call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d.toFixed(0)} kWh`));

        const groups = g.selectAll("g.group")
        .data(chartData)
        .enter()
        .append("g")
        .attr("class", "group")
        .attr("transform", (d) => `translate(${x0(d.label)}, 0)`);

        groups.selectAll("rect")
        .data((d) => subgroups.map((key) => ({ key, value: d[key] })))
        .enter()
        .append("rect")
        .attr("x",      (d) => x1(d.key))
        .attr("y",      (d) => y(d.value))
        .attr("width",  x1.bandwidth())
        .attr("height", (d) => height - y(d.value))
        .attr("fill",   (d) => colors[d.key])
        .attr("rx", 3);

        // Legend
        const legend = g.append("g").attr("transform", `translate(${width - 100}, 0)`);
        subgroups.forEach((key, i) => {
        legend.append("rect")
            .attr("x", 0).attr("y", i * 20)
            .attr("width", 12).attr("height", 12)
            .attr("fill", colors[key]).attr("rx", 2);
        legend.append("text")
            .attr("x", 16).attr("y", i * 20 + 10)
            .style("font-size", "11px")
            .text(key.charAt(0).toUpperCase() + key.slice(1));
        });
    }, [householdType])

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

}

export default SurplusDeficitChart;