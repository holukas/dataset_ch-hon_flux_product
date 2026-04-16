"""
Compare March cumulative NEE and ET across 3 years (2024, 2025, 2026)
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from diive.core.io.files import load_parquet

warnings.filterwarnings('ignore')

# Apply modern plot style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams.update({
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#212529',
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'axes.spines.right': False,
    'axes.spines.top': False,
})

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_OUT_DIR = SCRIPT_DIR.parent / "data" / "out"

FILENAME = "06_L4.1_FLUXES_MERGED.parquet"
NEE_COL = "NEE_L3.1_L3.3_CUT_50_QCF_gfXG"
LE_COL = "LE_L3.1_L3.3_CUT_NONE_QCF_gfXG"

# Unit conversion factors
# NEE: umol CO2 m-2 s-1 to g C m-2 30min-1
NEE_UMOL_TO_G_C_30MIN = 0.02161926

# LE: W m-2 to mm 30min-1 (evapotranspiration)
LE_TO_ET_30MIN = 7.3469e-4

# Color scheme - Material Design colors per year
COLOR_2024 = "#3f51b5"  # Indigo
COLOR_2025 = "#ff6f00"  # Deep Orange
COLOR_2026 = "#00796b"  # Teal Dark

GREY_COLOR = "#6c757d"
DARK_COLOR = "#212529"

script_id = "09"

# ============================================================================
# Load data
# ============================================================================

filepath = DATA_OUT_DIR / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

# ============================================================================
# Filter for months and prepare data
# ============================================================================

months_to_plot = [3]  # March only
month_names = {3: "March"}

df['month'] = df.index.month
df['year'] = df.index.year

# Extract and convert variables
nee_umol = df[NEE_COL].copy()
nee = nee_umol * NEE_UMOL_TO_G_C_30MIN  # Convert to g C m-2 30min-1

le = df[LE_COL].copy()
et = le * LE_TO_ET_30MIN  # Convert to mm 30min-1

# Get available years
years = sorted(df['year'].unique())
print(f"Years available: {years}")

# Calculate cumulative for each month and year
cumulative_data_by_month = {}

for month in months_to_plot:
    month_data = df[df['month'] == month].copy()
    print(f"\n{month_names[month]} records: {len(month_data)}")

    # Add day of month and fractional day for half-hourly alignment
    month_data['day_of_month'] = month_data.index.day
    # Fractional day: day + hour/24 + minute/1440
    month_data['day_fraction'] = (month_data.index.day +
                                  month_data.index.hour / 24.0 +
                                  month_data.index.minute / 1440.0)

    nee_month = nee[month_data.index]
    et_month = et[month_data.index]

    cumulative_data_by_month[month] = {}

    for year in years:
        year_mask = month_data['year'] == year
        year_data = month_data[year_mask].copy()

        if len(year_data) == 0:
            continue

        nee_year = nee_month[year_mask]
        et_year = et_month[year_mask]

        nee_filled = nee_year.fillna(0)
        et_filled = et_year.fillna(0)

        nee_cum = nee_filled.cumsum()
        et_cum = et_filled.cumsum()

        # Use fractional day for x-axis alignment
        day_fraction = year_data['day_fraction'].values

        cumulative_data_by_month[month][year] = {
            'day_fraction': day_fraction,
            'nee_cum': nee_cum.values,
            'et_cum': et_cum.values,
            'nee_total': nee_cum.iloc[-1] if len(nee_cum) > 0 else 0,
            'et_total': et_cum.iloc[-1] if len(et_cum) > 0 else 0,
            'days_count': len(year_data),
        }

        print(f"  {year}: {cumulative_data_by_month[month][year]['days_count']} days, "
              f"NEE={cumulative_data_by_month[month][year]['nee_total']:.1f} g C m-2, "
              f"ET={cumulative_data_by_month[month][year]['et_total']:.1f} mm")

# ============================================================================
# Plot March NEE & ET Comparison (side by side)
# ============================================================================

fig, (ax_nee, ax_et) = plt.subplots(1, 2, figsize=(16, 6))

colors = {2024: COLOR_2024, 2025: COLOR_2025, 2026: COLOR_2026}
month = 3

# Plot NEE
for year in years:
    if month in cumulative_data_by_month and year in cumulative_data_by_month[month]:
        day_frac = cumulative_data_by_month[month][year]['day_fraction']
        nee_cum = cumulative_data_by_month[month][year]['nee_cum']
        color = colors.get(year, "#999999")
        ax_nee.plot(day_frac, nee_cum, alpha=0.9, c=color, linewidth=1.8, label=str(year))
        ax_nee.fill_between(day_frac, nee_cum, alpha=0.15, color=color)

ax_nee.axhline(0, color=DARK_COLOR, linewidth=1, alpha=0.5, linestyle='-', zorder=5)
ax_nee.set_title(r"March Cumulative NEE Comparison (3 Years)", fontsize=14, fontweight='bold')
ax_nee.set_xlabel("Day of March")
ax_nee.set_ylabel(r"Cumulative NEE (g C m$^{-2}$)")
ax_nee.grid(True, alpha=0.2)
ax_nee.legend(title="Year", loc='upper left', fontsize=10)

# Set axis limits
all_days_nee = []
all_nee = []
for year in years:
    if month in cumulative_data_by_month and year in cumulative_data_by_month[month]:
        all_days_nee.extend(cumulative_data_by_month[month][year]['day_fraction'])
        all_nee.extend(cumulative_data_by_month[month][year]['nee_cum'])

if all_days_nee:
    ax_nee.set_xlim(min(all_days_nee), max(all_days_nee))
    ax_nee.set_ylim(0, max(all_nee) * 1.02)

# Styling for NEE
ax_nee.spines['left'].set_visible(True)
ax_nee.spines['bottom'].set_visible(True)
ax_nee.spines['right'].set_visible(False)
ax_nee.spines['top'].set_visible(False)
ax_nee.spines['left'].set_linewidth(1.0)
ax_nee.spines['bottom'].set_linewidth(1.0)
ax_nee.spines['left'].set_color(DARK_COLOR)
ax_nee.spines['bottom'].set_color(DARK_COLOR)
ax_nee.tick_params(axis='both', which='major', length=6, width=1.2, colors=DARK_COLOR)

# Plot ET
for year in years:
    if month in cumulative_data_by_month and year in cumulative_data_by_month[month]:
        day_frac = cumulative_data_by_month[month][year]['day_fraction']
        et_cum = cumulative_data_by_month[month][year]['et_cum']
        color = colors.get(year, "#999999")
        ax_et.plot(day_frac, et_cum, alpha=0.9, c=color, linewidth=1.8, label=str(year))
        ax_et.fill_between(day_frac, et_cum, alpha=0.15, color=color)

ax_et.axhline(0, color=DARK_COLOR, linewidth=1, alpha=0.5, linestyle='-', zorder=5)
ax_et.set_title(r"March Cumulative ET Comparison (3 Years)", fontsize=14, fontweight='bold')
ax_et.set_xlabel("Day of March")
ax_et.set_ylabel(r"Cumulative ET (mm)")
ax_et.grid(True, alpha=0.2)
ax_et.legend(title="Year", loc='upper left', fontsize=10)

# Set axis limits
all_days_et = []
all_et = []
for year in years:
    if month in cumulative_data_by_month and year in cumulative_data_by_month[month]:
        all_days_et.extend(cumulative_data_by_month[month][year]['day_fraction'])
        all_et.extend(cumulative_data_by_month[month][year]['et_cum'])

if all_days_et:
    ax_et.set_xlim(min(all_days_et), max(all_days_et))
    ax_et.set_ylim(0, max(all_et) * 1.02)

# Styling for ET
ax_et.spines['left'].set_visible(True)
ax_et.spines['bottom'].set_visible(True)
ax_et.spines['right'].set_visible(False)
ax_et.spines['top'].set_visible(False)
ax_et.spines['left'].set_linewidth(1.0)
ax_et.spines['bottom'].set_linewidth(1.0)
ax_et.spines['left'].set_color(DARK_COLOR)
ax_et.spines['bottom'].set_color(DARK_COLOR)
ax_et.tick_params(axis='both', which='major', length=6, width=1.2, colors=DARK_COLOR)

plt.tight_layout()
outfile = DATA_OUT_DIR / "09_March_comparison.png"
fig.savefig(outfile, dpi=150, bbox_inches='tight')
print(f"\nSaved: {outfile}")
fig.show()

print("\nComparison complete.")
