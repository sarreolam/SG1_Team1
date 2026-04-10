import { useEffect, useRef } from "react";
import * as d3 from "d3";
import data from "../../../energy_simulations.json";

const WealthLevelChart = () => {
    const ref = useRef();

    useEffect(()=> {
        const byWealth = d3.rollups(data.simulations, (sims) => ({
            production: d3.sum(sims, (s)=> s.summary.total_gen_kwh),
            consumption: d3.sum(sims, (s)=> s.summary.total_load_kwh),
        }), (s)=> s.metadata.wealth_level).map(([wealth, vals]) => ({wealth, ...vals}));

        const subgroups = ["production", "consumption"];
        const colors = {production: "#f0c040", consumption: "#e07b39"}
        
        const margin = { top: 30, right: 30, bottom: 80, left: 65 };
        const width  = 560 - margin.left - margin.right;
        const height = 320 - margin.top  - margin.bottom;

        const svg = d3.select(ref.current).attr("width",  width  + margin.left + margin.right).attr("height", height + margin.top  + margin.bottom);
        svg.selectAll("*").remove();

        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        
        const x0 = d3.scaleBand().domain(byWealth.map((d)=> d.wealth)).range([0,width]).padding(0.3);
        const x1 = d3.scaleBand().domain(subgroups).range([0, x0.bandwidth()]).padding(0.05);
        const y = d3.scaleLinear().domain([0, d3.max(byWealth, (d)=> Math.max(d.production, d.consumption)) * 1.15]).nice().range([height,0]);

        g.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x0));
        g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat((d)=> `${d.toFixed(0)} kwH`));

        const groups = g.selectAll("g.group")
        .data(byWealth)
        .enter()
        .append("g")
        .attr("class", "group")
        .attr("transform", (d) => `translate(${x0(d.wealth)}, 0)`);

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

        const legend = g.append("g").attr("transform", `translate(${width - 120}, 0)`);
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

    }, [])

    return <svg ref={ref}/>
}

export default WealthLevelChart;