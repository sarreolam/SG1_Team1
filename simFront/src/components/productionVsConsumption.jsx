import { useEffect, useRef } from "react";
import * as d3 from "d3";
import data from "../../../dummy_energy_simulations.json";

const ProductionVsConsumption = () => {
  const ref = useRef();

  useEffect(() => {
    const totals = [
      {
        label: "Production",
        value: d3.sum(data.simulations, (sim) =>
          d3.sum(sim.timeseries, (d) => d.solar_kw)
        ),
        color: "#f0c040",
      },
      {
        label: "Consumption",
        value: d3.sum(data.simulations, (sim) =>
          d3.sum(sim.timeseries, (d) => d.load_kw)
        ),
        color: "#e07b39",
      },
    ];

    const margin = { top: 30, right: 30, bottom: 50, left: 65 };
    const width  = 340 - margin.left - margin.right;
    const height = 300 - margin.top  - margin.bottom;

    const svg = d3.select(ref.current).attr("width",  width  + margin.left + margin.right).attr("height", height + margin.top  + margin.bottom);
    svg.selectAll("*").remove();

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(totals.map((d) => d.label)).range([0, width]).padding(0.4);
    const y = d3.scaleLinear().domain([0, d3.max(totals, (d) => d.value) * 1.15]).nice().range([height, 0]);

    g.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x));
    g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d.toFixed(0)} kW`));

    g.selectAll("rect")
      .data(totals)
      .enter()
      .append("rect")
      .attr("x",      (d) => x(d.label))
      .attr("y",      (d) => y(d.value))
      .attr("width",  x.bandwidth())
      .attr("height", (d) => height - y(d.value))
      .attr("fill",   (d) => d.color)
      .attr("rx", 3);

    g.selectAll("text.val")
      .data(totals)
      .enter()
      .append("text")
      .attr("class", "val")
      .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
      .attr("y", (d) => y(d.value) - 6)
      .attr("text-anchor", "middle")
      .style("font-size", "11px")
      .text((d) => d.value.toFixed(1));

  }, []);

  return <svg ref={ref} />;
};

export default ProductionVsConsumption;