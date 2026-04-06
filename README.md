## Installation & Running the Simulation

### Prerequisites
- **Python 3.10+** (3.11 recommended)
- `pip` (comes with most Python installs)

### 1) Clone the repository
```bash
git clone https://github.com/sarreolam/SG1_Team1.git
cd SG1_Team1
```

Windows (CMD)
```bash
python -m venv .venv
.\.venv\Scripts\activate.bat
```

macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Run the simulation
```bash
cd simulation
python green_grid_sim.py
```

Outputs:
- After the run finishes, CSV files are generated in:
output/log.csv (timestep-by-timestep measurements)
- output/events.csv (events such as inverter failures, battery full/low, curtailment)
