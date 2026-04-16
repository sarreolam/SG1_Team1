import "./App.css";

import DuckCurve from "./components/duckCurve";
import BatteryUtilizationChart from "./components/BatteryUtilizationChart";
import ProductionVsConsumption from "./components/productionVsConsumption";
import HouseholdComparison from "./components/householdComparison";
import WealthLevelChart from "./components/wealthLevelChart";
import PeakTimes from "./components/peakTimes";
import SurplusDeficitChart from "./components/surplusDeficitChart";
import GridExportChart from "./components/gridExportChart";

function App() {
  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-eyebrow">GREENGRID ENERGY ANALYTICS</p>
          <h1>Neighborhood Solar Performance Dashboard</h1>
          <p className="dashboard-subtitle">
            Most households rely <i>heavily</i> on the city power grid during the most expensive
            part of the day. What does this mean? Higher emissions, increasing pressure on the
            power infrastructure, and most importantly, higher costs. 
          </p>
        </div>
      </header>

      <div style={{display:"flex", justifyContent:"center", margin:"20px"}}>
        <div className="dashboard-insight-main">
          <span className="insight-label">Key Insight</span>
          <p>
            But now, enter solar generation:
            During the middle of the day, the solar panels can produce
            enough energy for all household needs, and more.
            By the time the rest of the households need to tap into the 
            city grid, solar will have more than enough energy stored, maximizing savings.
          </p>
        </div>
      </div>
      
      <main className="dashboard-content">
        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Core Pattern</p>
              <h2>Duck Curve Overview</h2>
            </div>
            <p className="insight-label-hard">
              This chart shows how solar production reshapes net demand
              throughout the day and why evening hours remain the most critical: 
              When others buy energy, solar panels tap in to their reserve.
            </p>
          </div>

          <div className="card card-full">
            <div className="chart-shell">
              <DuckCurve />
            </div>
          </div>
        </section>

        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Comparative Performance</p>
              <h2>Consumption and Production Profiles</h2>
            </div>
            <p className="insight-label-hard">
              Let's take a look at a typical household in a neighborhood:
            </p>
          </div>

          <div className="grid-two">
            <div className="card">
              <div className="chart-shell">
                <ProductionVsConsumption />
              </div>
            </div>

            <div className="card">
              <div className="chart-shell">
                <WealthLevelChart />
              </div>
            </div>
          </div>
          <div>
              <p className="insight-label-hard">
                Here, the picture is painted in a clear way: Even the houses of highest usage can benefit from the addition of solar energy.
                No matter the consumption level, the house can reach higher levels of production of energy than needed.
              </p>
          </div>
          <div className="grid-one">
            <div className="card">
              <div className="chart-shell">
                <HouseholdComparison />
              </div>
            </div>
          </div>
          <div className="shock">
            <p>And the best part? The extra energy is sold, making you an extra source of income.</p>
          </div>
        </section>

        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Critical Timing</p>
              <h2>Peak Load and Energy Balance</h2>
            </div>
            <p className="section-description">
              Knowing when your energy use peaks allows you to reduce costs without reducing comfort.
            </p>
          </div>

          <div className="grid-two">
            <div className="card">
              <div className="chart-shell">
                <PeakTimes />
              </div>
            </div>

            <div className="card">
              <div className="chart-shell">
                <SurplusDeficitChart />
              </div>
            </div>
            
          </div>
          <div style={{display:"flex", justifyContent: "center"}}>
              <p className="insight-label-hard">
                Not only is solar capable of supplying you with what you need, it is capable of getting it before you need it.
                No need to worry about not having enough saved, you will have plenty.
              </p>
            </div>
        </section>

        <section style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", 
          gap: "30px", 
          alignItems: "center",
          margin: "40px 0" 
        }}>
          <div style={{ borderRadius: "20px", overflow: "hidden", height: "350px" }}>
            <img 
              src="https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&q=80&w=1000" 
              alt="Solar Panels" 
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
          <div>
            <p className="section-kicker">The Future of the Neighborhood</p>
            <h2 style={{ fontSize: "28px", margin: "10px 0" }}>Beyond Generation</h2>
            <p style={{ color: "#475569", lineHeight: "1.6" }}>
              Our simulation is not just about numbers; it is about the real-world transition 
              to energy independence. As more households adopt storage solutions, 
              the neighborhood moves from being a burden on the city grid to becoming 
              a resilient, self-sustaining power plant.
            </p>
          </div>
        </section>

        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Economic and Grid Impact</p>
              <h2>Operational Value</h2>
            </div>
            <p className="section-description">
              Review the benefits of self-consumption, exported energy, and
              battery behavior, and see why it is such a good choice.
            </p>
          </div>

          <div className="grid-three operational">
            <div className="card">
              <div className="chart-shell compact">
                <GridExportChart />
              </div>
            </div>

            <div className="card">
              <div className="chart-shell compact">
                <BatteryUtilizationChart />
              </div>
            </div>
          </div>
        </section>

        <section className="section-block">
          <div className="final-summary-card">
            <p className="section-kicker">Executive Summary</p>
            <h2>What the neighborhood data suggests</h2>
            <p>
              Solar adoption allows households to maintain the same energy reliability they are used to—while reducing costs and environmental impact.
              By combining solar generation with smarter energy usage and storage, neighborhoods can transition from passive consumers to active energy
              participants—benefiting both financially and sustainably; A win-win all the way. 
            </p>
          </div>
        </section>

        <div className="project-info">
        <h2>Solar Energy Simulation Dashboard</h2>

        <p className="project-sub">
          Simulation of household energy consumption, solar generation, and grid
          impact across different household types and socioeconomic levels.
        </p>

        <div className="project-meta">
          <div>
            <strong>Team:</strong>
            <p>
              Marco Antonio Manjarrez Fernández · 0253075 <br />
              Demián Velasco Gómez Llanos · 0253139 <br />
              Santiago Arreola Munguia · 0252028 <br />
              Sophia Alessandra Frias Piña · 0230148
            </p>
          </div>

          <div>
            <strong>Course:</strong>
            <p>Simulación gráfica</p>

            <strong>Program:</strong>
            <p>Ingeniería en Sistemas y Gráficas Computacionales</p>

            <strong>Professor:</strong>
            <p>Gabriel Castillo Cortés</p>
          </div>
        </div>

        <a
          className="project-link"
          href="https://github.com/sarreolam/SG1_Team1"
          target="_blank"
          rel="noreferrer"
        >
          View GitHub Repository →
        </a>
      </div>
      </main>
    </div>
  );
}

export default App;
