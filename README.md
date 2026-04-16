# dataset_ch-hon_flux_product

Flux data processing pipeline for the CH-HON forest station.
Produces a final ecosystem flux dataset from eddy covariance and meteorological measurements.

## Status
- [Current progress (Google Docs)](https://docs.google.com/spreadsheets/d/15jmOvfX0WIRGg2_N4bnhIOrvpsJkGhBQ296hzo7W0eU/edit?gid=0#gid=0)
- Fluxes: preliminary calculations done (Level-0)
- Meteo: meteoscreening in progress

---

## Project Structure

```
.
├── src/                          # Production scripts (run in order)
│   ├── funcs.py                  # Shared utility functions
│   ├── 01_merge_files_to_parquet.py
│   ├── 02_timelag_checks.py
│   ├── 03_winddir_check.py
│   ├── 04_fluxprocessingchain_NEE.py
│   ├── 05_fluxprocessingchain_LE.py
│   ├── 06_merge_data.py
│   ├── 07_plot_NEE.py
│   ├── 08_plot_LE.py
│   └── 09_march_comparison.py
│
├── data/
│   ├── OPENLAG-IRGA-Level-0_.../  # Raw EddyPro FLUXNET CSV input files
│   └── out/                       # All script outputs (parquet, CSV, plots)
│
└── notebooks/
    ├── 00_PRELIMINARY_L0/         # L0 flux processing and QC
    └── 10_METEO/                  # Meteorological data screening
```

---

## Pipeline

### src/ scripts

| Script | Input | Output | Description |
|--------|-------|--------|-------------|
| `01_merge_files_to_parquet.py` | EddyPro FLUXNET CSVs | `FLUXES_L0_ALL.parquet/.csv` | Merges raw EddyPro output files into a single dataset |
| `02_timelag_checks.py` | `FLUXES_L0_ALL.parquet` | `02_*_TLAG_ACTUAL_*.png` | Time lag distribution analysis; detects peak and search range for EddyPro final run |
| `03_winddir_check.py` | `FLUXES_L0_ALL.parquet` | — | Wind direction offset check across years using `WindDirOffset`; identifies per-year corrections |
| `04_fluxprocessingchain_NEE.py` | `FLUXES_L0_ALL.parquet` | L4 NEE parquet + plots | Full NEE flux processing chain (QCF, USTAR filtering, gap-filling) via `FluxProcessingChain` |
| `05_fluxprocessingchain_LE.py` | `FLUXES_L0_ALL.parquet` | L4 LE parquet + plots | Full LE flux processing chain via `FluxProcessingChain` |
| `06_merge_data.py` | L4 NEE + LE parquets | `06_L4.1_FLUXES_MERGED.parquet/.csv` | Merges NEE and LE L4 datasets into single output file |
| `07_plot_NEE.py` | L4 merged parquet | `07_NEE_timeseries_*.png`, `07_NEE_DielCycle_*.png` | NEE visualization with time series, cumulative flux, and mean diel cycle analysis |
| `08_plot_LE.py` | L4 merged parquet | `08_LE_timeseries_*.png`, `08_LE_DielCycle_*.png` | LE visualization as evapotranspiration (ET in mm) with time series, cumulative ET, and mean diel cycle analysis |
| `09_march_comparison.py` | L4 merged parquet | `09_March_comparison.png` | Interannual March comparison: cumulative NEE and ET (2024-2026) overlaid on same plot with half-hourly resolution |

### Notebooks — 00_PRELIMINARY_L0

| Notebook | Description |
|----------|-------------|
| `01_L0_merge_output_to_parquet` | Merge raw flux output (exploratory version of script 01) |
| `02_L0_timelags_check` | Time lag QC (exploratory version of script 02) |
| `03_L0_winddir_check` | Wind direction quality check |
| `20.1_FluxProcessingChain_NEE_L0_3-USTAR-SCENARIOS` | NEE processing with 3 USTAR threshold scenarios |
| `21.1_FluxProcessingChain_NEE-L0` | Full NEE flux processing chain → L4 preliminary |
| `22.1_FluxProcessingChain_LE-L0` | Full LE flux processing chain → L4 preliminary |
| `50_PLOT_Cumulative_NEE_PRELIMINARY` | Cumulative NEE plots |
| `51_PLOT_DielCycles_NEE_LE` | Diel cycle plots for NEE and LE |

### Notebooks — 10_METEO

| Notebook | Description |
|----------|-------------|
| `_StepwiseMeteoScreeningFromDatabase` | Stepwise quality screening of meteorological variables |
| `TA_T1_4_1/2_...` | Air temperature sensor screening |

---

## Domain Notes

### Time Lags (EddyPro)
- EddyPro outputs time lags in **0.05s discrete steps**
- EddyPro **excludes boundary values** of the specified search range
  - e.g. a range of `0.10–1.00s` results in EddyPro using `0.15–0.95s`
  - The scripts automatically expand detected ranges by ±0.05s before reporting EddyPro input values
- **Fringe bins** at the edges of the lag search window accumulate non-physical lags and are excluded from peak detection

### Processing Levels
| Level | Description |
|-------|-------------|
| L0 | Preliminary fluxes — raw EddyPro output, open lag window, no final QC |
| L4 | Gap-filled, quality-filtered flux product (target output) |

---

## Dependencies

Managed with [Poetry](https://python-poetry.org/). Install environment:

```bash
poetry install
```

Primary libraries: [`diive`](https://github.com/holukas/diive) · `pandas` · `matplotlib` · `numpy`
