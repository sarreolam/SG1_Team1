import { useEffect, useRef } from "react";
import * as d3 from "d3";
import data from "../../../energy_simulations.json";

const PeakTimes = () => {
    const ref = useRef();

    useEffect(()=> {
        const peakData = data.simulations.map((sim)=>{
            const peakSolar = d3.greatest(sim.timeseries, (d)=> d.solar_kw);
            const peakLoad = d3.greatest(sim.timeseries, (d)=> d.load_kw);
            return {
                label:  sim.id,
                peakSolarHour: peakSolar.hour,
                peakSolarVal: peakSolar.solar_kw,
                peakLoadHour: peakLoad.hour,
                peakLoadVal: peakLoad.load_kw,
            };
        });
        
        const margin = { top: 30, right: 30, bottom: 70, left: 65 };
        const width  = 500 - margin.left - margin.right;
        const height = 320 - margin.top  - margin.bottom;

        const svg = d3.select(ref.current)
        .attr("width",  width  + margin.left + margin.right)
        .attr("height", height + margin.top  + margin.bottom);
        svg.selectAll("*").remove();

        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

        const x = d3.scaleLinear().domain([0, 23]).range([0, width]);
        const y = d3.scaleBand()
        .domain(peakData.map((d) => d.label)).range([0, height]).padding(0.4);

        g.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(12).tickFormat((d) => `${d}:00`))
        .selectAll("text").attr("transform", "rotate(-35)").style("text-anchor", "end");

        g.append("g").call(d3.axisLeft(y));

        peakData.forEach((d) => {
        g.append("line")
            .attr("x1", x(d.peakSolarHour))
            .attr("x2", x(d.peakLoadHour))
            .attr("y1", y(d.label) + y.bandwidth() / 2)
            .attr("y2", y(d.label) + y.bandwidth() / 2)
            .attr("stroke", "#555")
            .attr("stroke-dasharray", "3 2");
        });

        g.selectAll("circle.solar")
        .data(peakData)
        .enter()
        .append("circle")
        .attr("class", "solar")
        .attr("cx", (d) => x(d.peakSolarHour))
        .attr("cy", (d) => y(d.label) + y.bandwidth() / 2)
        .attr("r", 8)
        .attr("fill", "#f0c040");

        g.selectAll("circle.load")
        .data(peakData)
        .enter()
        .append("circle")
        .attr("class", "load")
        .attr("cx", (d) => x(d.peakLoadHour))
        .attr("cy", (d) => y(d.label) + y.bandwidth() / 2)
        .attr("r", 8)
        .attr("fill", "#e07b39");

        ["solar", "load"].forEach((type) => {
        g.selectAll(`text.${type}`)
            .data(peakData)
            .enter()
            .append("text")
            .attr("class", type)
            .attr("x", (d) => x(type === "solar" ? d.peakSolarHour : d.peakLoadHour))
            .attr("y", (d) => y(d.label) + y.bandwidth() / 2 - 12)
            .attr("text-anchor", "middle")
            .style("font-size", "10px")
            .text((d) => `${type === "solar" ? d.peakSolarHour : d.peakLoadHour}:00`);
        });

        const legend = g.append("g").attr("transform", `translate(${width - 120}, 0)`);
        [["#f0c040", "Peak solar"], ["#e07b39", "Peak load"]].forEach(([color, label], i) => {
        legend.append("circle").attr("cx", 6).attr("cy", i * 20 + 6).attr("r", 6).attr("fill", color);
        legend.append("text").attr("x", 16).attr("y", i * 30 + 10).style("font-size", "11px").text(label);
        });

    }, []);

  return <svg ref={ref} />;
    
}


export default PeakTimes