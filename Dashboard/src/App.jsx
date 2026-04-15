import "./App.css";

import DuckCurve from "./components/duckCurve";
import BatteryUtilizationChart from "./components/BatteryUtilizationChart";
import ProductionVsConsumption from "./components/productionVsConsumption";
import HouseholdComparison from "./components/householdComparison";
import WealthLevelChart from "./components/wealthLevelChart";
import PeakTimes from "./components/peakTimes";
import SurplusDeficitChart from "./components/surplusDeficitChart";
import CostSavingsChart from "./components/CostSavingsChart";
import GridExportChart from "./components/gridExportChart";

function App() {
  return (
    <div className="dashboard-page">
      
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

      <header className="dashboard-header">
        <div>
          <p className="dashboard-eyebrow">GREENGRID ENERGY ANALYTICS</p>
          <h1>Neighborhood Solar Performance Dashboard</h1>
          <p className="dashboard-subtitle">
            Visual overview of household demand, solar generation, grid
            dependence, and energy performance across the neighborhood.
          </p>
        </div>

        <div className="dashboard-insight">
          <span className="insight-label">Key Insight</span>
          <p>
            Solar generation reduces grid pressure during midday, but evening
            demand still creates deficits, highlighting opportunities for
            storage and demand shifting.
          </p>
        </div>
      </header>

      <main className="dashboard-content">
        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Core Pattern</p>
              <h2>Duck Curve Overview</h2>
            </div>
            <p className="section-description">
              This chart shows how solar production reshapes net demand
              throughout the day and why evening hours remain the most critical.
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
            <p className="section-description">
              Compare how household categories and wealth levels affect energy
              usage, production, and overall pressure on the grid.
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

          <div className="grid-one">
            <div className="card">
              <div className="chart-shell">
                <HouseholdComparison />
              </div>
            </div>
          </div>
        </section>

        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Critical Timing</p>
              <h2>Peak Load and Energy Balance</h2>
            </div>
            <p className="section-description">
              These views highlight when demand peaks, when solar output is
              strongest, and where the neighborhood shifts into surplus or
              deficit.
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
        </section>

        <section className="section-block">
          <div className="section-title-row">
            <div>
              <p className="section-kicker">Economic and Grid Impact</p>
              <h2>Operational Value</h2>
            </div>
            <p className="section-description">
              Review the benefits of self-consumption, exported energy, and
              battery behavior to understand the value of local solar adoption.
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
              The simulation shows that distributed solar generation improves
              daytime energy balance across the neighborhood, but late-day
              consumption still pushes households back toward grid dependence.
              The strongest opportunity for future optimization lies in battery
              storage, smarter load timing, and targeted adoption strategies by
              household type.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;