import { useEffect, useRef } from "react";
import * as d3 from "d3";
import sim_data from "../../../Simulation/Dashboard/data/all_energy_simulations.json";

const BarChart = () => {
    const ref = useRef();

    useEffect(()=> {
        const data = sim_data.simulations.map((sim)=>({label: sim.id, value: d3.sum(sim.timeseries, (d)=> d.load_kw)}));
        
        const margin = {top: 20, bottom: 80, left: 55, right: 20}
        const width = 500 - margin.left - margin.right;
        const height = 300 - margin.bottom - margin.top;

        const svg = d3.select(ref.current).attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom);
        svg.selectAll("*").remove(); //Borra todo antes de renderizar el componente
        
        const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`)

        const x = d3.scaleBand().domain(data.map((d)=> d.label)).range([0,width]).padding(0.3)
        const y = d3.scaleLinear().domain([0, d3.max(data, (d)=>d.value)]).nice().range([height, 0]);
        
        g.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x)).selectAll("text").attr("transform", "rotate(-25)").style("text-anchor", "end");
        g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d.toFixed(0)} kW`));
        
        g.selectAll("rect")
        .data(data)
        .enter()
        .append("rect")
        .attr("x",      (d) => x(d.label))
        .attr("y",      (d) => y(d.value))
        .attr("width",  x.bandwidth())
        .attr("height", (d) => height - y(d.value))
        .attr("fill",   "steelblue")
        .attr("rx", 3);

        g.selectAll("text.label")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "label")
        .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
        .attr("y", (d) => y(d.value) - 5)
        .attr("text-anchor", "middle")
        .style("font-size", "11px")
        .text((d) => d.value.toFixed(1));
  }, []);

  return <svg ref={ref}></svg>;
}
export default BarChart;