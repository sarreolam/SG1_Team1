import { useEffect, useRef } from "react";
import * as d3 from "d3";

const BarChart = () => {
    const ref = useRef();

    useEffect(()=> {
        const data = [10,20,30,40];
        const svg = d3.select(ref.current).attr("width", 300).attr("height", 200);
        svg.selectAll("*").remove(); //Borra todo antes de renderizar el componente
         svg.selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", (d, i) => i * 60)
      .attr("y", d => 200 - d * 4)
      .attr("width", 40)
      .attr("height", d => d * 4)
      .attr("fill", "steelblue");
  }, []);

  return <svg ref={ref}></svg>;
}
export default BarChart;