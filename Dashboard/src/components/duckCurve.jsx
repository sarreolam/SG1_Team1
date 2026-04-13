import { useEffect, useRef } from "react";
import * as d3 from "d3";
import data from "../../data/duck_curve.json";


const DuckCurve = () => {
    const ref = useRef();

    useEffect(()=> {
        const hours = d3.range(24);

        const hourTotals = hours.map((h) => {
            const points = data.filter((d) => d.hour === h);

            return {
                hour: h,
                solar: d3.mean(points, (d) => d.solar_kw_used),
                load: d3.mean(points, (d) => d.load_kw),
                net: d3.mean(points, (d) => d.net_load_kw)
            };
        });
        const margin = { top: 30, right: 30, bottom: 50, left: 60 };
        const width  = 560 - margin.left - margin.right;
        const height = 320 - margin.top  - margin.bottom;

        const svg = d3.select(ref.current)
        .attr("width",  width  + margin.left + margin.right)
        .attr("height", height + margin.top  + margin.bottom);
        svg.selectAll("*").remove();
        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        const x = d3.scaleLinear().domain([0,23]).range([0, width]);
        const y = d3.scaleLinear().domain([d3.min(hourTotals, (d)=> Math.min(d.net, d.solar, d.load)) * 1.1, d3.max(hourTotals, (d)=> Math.max(d.net, d.solar, d.load)) * 1.1]).nice().range([height, 0]);
        g.append("line").attr("x1", 0).attr("x2", width).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", "#CCCCCC").attr("stroke-dasharray", "4 3");

        const line = (key) => d3.line().x((d)=> x(d.hour)).y((d)=>y(d[key])).curve(d3.curveCatmullRom);

        const series = [
        { key: "load",  color: "#e07b39", label: "Load"       },
        { key: "solar", color: "#f0c040", label: "Solar gen"  },
        { key: "net",   color: "#4a90d9", label: "Net demand" },
        ];

        series.forEach(({ key, color }) => {
            g.append("path").datum(hourTotals).attr("fill", "none").attr("stroke", color).attr("stroke-width", key === "net" ? 2.5 : 1.5).attr("stroke-dasharray", key === "net" ? "none" : "5 3").attr("d", line(key));
        });

        g.append("g").attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(12).tickFormat((d) => `${d}:00`))
        .selectAll("text").attr("transform", "rotate(-35)").style("text-anchor", "end");

        g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d.toFixed(2)} kW`));

        const legend = g.append("g").attr("transform", `translate(${width - 130}, 0)`);
        series.forEach(({ label, color }, i) => {
            legend.append("line")
                .attr("x1", 0).attr("x2", 18)
                .attr("y1", i * 20 + 6).attr("y2", i * 20 + 6)
                .attr("stroke", color).attr("stroke-width", 2);
            legend.append("text")
                .attr("x", 22).attr("y", i * 20 + 10)
                .style("font-size", "11px").text(label);
            });
    }, []);

    return <svg ref={ref}/>;

}

export default DuckCurve;