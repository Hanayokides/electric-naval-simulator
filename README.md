# Electric Vessel Simulator

Sizing and financial viability model for a passenger vessel (catamaran, 53 m), comparing different propulsion strategies:

- **Diesel** (internal combustion engine, baseline)
- **Fast Charging** (1 and 2 terminals)
- **Slow Charging** (overnight)
- **Mixed Charging** (fast + slow combination, with adjustable infrastructure power, 1 and 2 terminals)

For each configuration, the model sizes the hull (equilibrium draught via mass/buoyancy balance), calculates the route's energy demand, and estimates the Internal Rate of Return (IRR) and Net Present Value (NPV) of the investment.

## Code structure

| File | Content |
|---|---|
| `calculos_comuns.py` | Hydrostatics and structural mass equations for the hull (common to all configurations) |
| `recargas.py` | Energy demand and financial return models for Fast, Slow, and Mixed Charging |
| `diesel.py` | Financial return model for the Diesel configuration |
| `main.py` | Orchestrates the simulations, generates the reports (Excel and Word), and the sensitivity charts |

## How to run

### Dependencies

```bash
pip install pandas numpy matplotlib scipy numpy-financial python-docx openpyxl
```

### Execution

```bash
python main.py
```

The program asks for the execution mode:
- **O** — optimal results only (DOD that maximizes IRR for each configuration)
- **M** — also includes a sweep across multiple DOD values for comparison
- **ESC** — exits without running

### Outputs

- An Excel spreadsheet (`planilha_dimensionamento_completa_*.xlsx`) with detailed results for each simulated configuration, route, and speed.
- A Word report (`relatorio_graficos_completo_*.docx`) with summary results, sensitivity charts (IRR vs. DOD, IRR vs. infrastructure power), and summary tables.

## Main parameters

- Vessel length: 53 m (fixed)
- Simulated routes: 5, 7.5, 10, 12.5, and 15 km
- Simulated speeds: 8, 12, 16, and 20 knots
