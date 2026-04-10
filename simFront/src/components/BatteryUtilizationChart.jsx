import { useEffect, useRef } from "react";
import * as d3 from "d3";
import data from "../../../energy_simulations.json";

const BatteryUtilizationChart = () => {
  const ref = useRef();

  useEffect(() => {
    const hours = d3.range(24);
    const width  = 560;
    const height = 340;

    const svg = d3.select(ref.current)
      .attr("width", width)
      .attr("height", height);
    svg.selectAll("*").remove();

    const colors = {
      studio_middle:       "#4a90d9",
      small_family_middle: "#f0c040",
      large_family_high:   "#e07b39",
    };

    const cx = width / 2;
    const cy = height / 2 - 10;
    const maxRadius = 120;
    const minRadius = 30;

    const simCount = data.simulations.length;

    data.simulations.forEach((sim, simIdx) => {
      const hourlySOC = hours.map((h) => {
        const points = sim.timeseries.filter((d) => d.hour === h);
        return {
          hour: h,
          soc:  d3.mean(points, (d) => d.battery_soc_pct),
        };
      });

      const outerR = maxRadius - simIdx * ((maxRadius - minRadius) / simCount);
      const innerR = outerR - (maxRadius - minRadius) / simCount - 2;

      const angleSlice = (2 * Math.PI) / 24;

      const radialArc = d3.arc()
        .innerRadius(innerR)
        .outerRadius((d) => innerR + (d.soc / 100) * (outerR - innerR))
        .startAngle((d) => d.hour * angleSlice - Math.PI / 2)
        .endAngle((d) => (d.hour + 0.85) * angleSlice - Math.PI / 2); 

      const g = svg.append("g").attr("transform", `translate(${cx}, ${cy})`);

      g.append("circle")
        .attr("r", outerR)
        .attr("fill", "none")
        .attr("stroke", "#333")
        .attr("stroke-width", outerR - innerR)
        .attr("opacity", 0.15);

      g.selectAll(`path.sim${simIdx}`)
        .data(hourlySOC)
        .enter()
        .append("path")
        .attr("class", `sim${simIdx}`)
        .attr("d", radialArc)
        .attr("fill", colors[sim.id])
        .attr("opacity", 0.85);
    });

    const labelG = svg.append("g").attr("transform", `translate(${cx}, ${cy})`);
    [0, 6, 12, 18].forEach((h) => {
      const angle = (h / 24) * 2 * Math.PI - Math.PI / 2;
      const r = maxRadius + 14;
      labelG.append("text")
        .attr("x", Math.cos(angle) * r)
        .attr("y", Math.sin(angle) * r + 4)
        .attr("text-anchor", "middle")
        .style("font-size", "10px")
        .style("fill", "#888")
        .text(`${h}:00`);
    });

    const legend = svg.append("g")
      .attr("transform", `translate(${width / 2 - 150}, ${height - 22})`);

    data.simulations.forEach((sim, i) => {
      legend.append("rect")
        .attr("x", i * 140).attr("y", 0)
        .attr("width", 10).attr("height", 10)
        .attr("fill", colors[sim.id]).attr("rx", 2);
      legend.append("text")
        .attr("x", i * 140 + 14).attr("y", 9)
        .style("font-size", "10px")
        .text(sim.id.replace(/_/g, " "));
    });

  }, []);

  return <svg ref={ref} />;
};

export default BatteryUtilizationChart;