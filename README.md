# dataset_ch-hon_flux_product

Flux data processing pipeline for the CH-HON forest station.
Produces a final ecosystem flux dataset from eddy covariance and meteorological measurements.

## Status

- [Current progress (Google Docs)](https://docs.google.com/spreadsheets/d/15jmOvfX0WIRGg2_N4bnhIOrvpsJkGhBQ296hzo7W0eU/edit?gid=0#gid=0)
- Fluxes: preliminary calculations done (Level-0)
- Meteo: meteoscreening in progress

---

## Study Site

**Location & Coordinates**
- Site: Hoenggerberg Research Station (CH-HON)
- Region: Canton of Zurich, Switzerland
- Coordinates: 47.41887°N, 8.491318°E
- Altitude: 527 m above sea level
- Part of Waldlabor Zürich (Zurich Forest Laboratory)

**Ecosystem & Vegetation**
The station is a test plantation comparing 8 tree species from multiple geographic origins to assess their suitability under future climate conditions. Each species is represented by 4 geographic provenances, arranged in 12×12 meter plots with protective fencing.

**Tested Species:**
- **Coniferous** (4): Norway spruce (*Picea abies*), Larch (*Larix decidua*), Silver fir (*Abies alba*), Douglas fir (*Pseudotsuga menziesii*)
- **Deciduous** (4): Wild service tree (*Sorbus torminalis*), English oak (*Quercus robur*), Sessile oak (*Quercus petraea*), Austrian oak (*Quercus cerris*)

**Data Availability**
- Eddy covariance and meteorological measurements recorded since 2024
- More information: [SwissFluxNet CH-HON](https://www.swissfluxnet.ethz.ch/index.php/sites/ch-hon-hoenggerberg/)

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
│   ├── 09_march_comparison.py
│   └── 10_plot_NEE_hexbin.py
│
├── data/
│   ├── OPENLAG-IRGA-Level-0_.../  # Raw EddyPro FLUXNET CSV input files
│   └── out/                       # All script outputs (parquet, CSV, plots)
│
└── _archive/
    └── notebooks/                 # Exploratory notebooks (archived, see git history)
```

---

## Pipeline

### src/ scripts

| Script                          | Input                   | Output                                              | Description                                                                                                       |
|---------------------------------|-------------------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `01_merge_files_to_parquet.py`  | EddyPro FLUXNET CSVs    | `FLUXES_L0_ALL.parquet/.csv`                        | Merges raw EddyPro output files into a single dataset                                                             |
| `02_timelag_checks.py`          | `FLUXES_L0_ALL.parquet` | `02_*_TLAG_ACTUAL_*.png`                            | Time lag distribution analysis; detects peak and search range for EddyPro final run                               |
| `03_winddir_check.py`           | `FLUXES_L0_ALL.parquet` | —                                                   | Wind direction offset check across years using `WindDirOffset`; identifies per-year corrections                   |
| `04_fluxprocessingchain_NEE.py` | `FLUXES_L0_ALL.parquet` | L4 NEE parquet + plots                              | Full NEE flux processing chain (QCF, USTAR filtering, gap-filling) via `FluxProcessingChain`                      |
| `05_fluxprocessingchain_LE.py`  | `FLUXES_L0_ALL.parquet` | L4 LE parquet + plots                               | Full LE flux processing chain via `FluxProcessingChain`                                                           |
| `06_merge_data.py`              | L4 NEE + LE parquets    | `06_L4.1_FLUXES_MERGED.parquet/.csv`                | Merges NEE and LE L4 datasets into single output file                                                             |
| `07_plot_NEE.py`                | L4 merged parquet       | `07_NEE_timeseries_*.png`, `07_NEE_DielCycle_*.png` | NEE visualization with time series, cumulative flux, and mean diel cycle analysis                                 |
| `08_plot_LE.py`                 | L4 merged parquet       | `08_LE_timeseries_*.png`, `08_LE_DielCycle_*.png`   | LE visualization as evapotranspiration (ET in mm) with time series, cumulative ET, and mean diel cycle analysis   |
| `09_march_comparison.py`        | L4 merged parquet       | `09_March_comparison.png`                           | Interannual March comparison: cumulative NEE and ET (2024-2026) overlaid on same plot with half-hourly resolution |
| `10_plot_NEE_hexbin.py`         | L4 merged parquet       | `10_NEE_hexbin_TA_VPD_*.png`                        | Hexbin plot showing NEE response to temperature and vapor pressure deficit; reveals photosynthetic limitations   |

---

## Domain Notes

### Time Lags (EddyPro)

- EddyPro outputs time lags in **0.05s discrete steps**
- EddyPro **excludes boundary values** of the specified search range
    - e.g. a range of `0.10–1.00s` results in EddyPro using `0.15–0.95s`
    - The scripts automatically expand detected ranges by ±0.05s before reporting EddyPro input values
- **Fringe bins** at the edges of the lag search window accumulate non-physical lags and are excluded from peak
  detection

### Processing Levels

| Level | Description                                                           |
|-------|-----------------------------------------------------------------------|
| L0    | Preliminary fluxes — raw EddyPro output, open lag window, no final QC |
| L4    | Gap-filled, quality-filtered flux product (target output)             |

---

## Dependencies

Managed with [uv](https://docs.astral.sh/uv/) (Python 3.12). Install environment:

```bash
uv sync
```

Run scripts inside the environment with `uv run`, e.g. `uv run python src/07_plot_NEE.py`.

Primary libraries: [`diive`](https://github.com/holukas/diive) · `pandas` · `matplotlib` · `numpy`
