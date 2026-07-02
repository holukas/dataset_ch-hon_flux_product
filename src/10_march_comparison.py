"""
Compare March cumulative CO2 exchange across 3 years (2024, 2025, 2026), in g CO2 m-2
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
from diive.core.io.files import load_parquet

warnings.filterwarnings('ignore')

# Apply modern plot style
plt.style.use('seaborn-v0_8-darkgrid')
# Single font family and size for all text elements
FONT_FAMILY = 'sans-serif'
FONT_SIZE = 15

plt.rcParams.update({
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#212529',
    'axes.spines.left': True,
    'axes.spines.bottom': True,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'font.family': FONT_FAMILY,
    'font.size': FONT_SIZE,
    'axes.titlesize': FONT_SIZE,
    'axes.labelsize': FONT_SIZE,
    'xtick.labelsize': FONT_SIZE,
    'ytick.labelsize': FONT_SIZE,
    'legend.fontsize': FONT_SIZE,
    'figure.titlesize': FONT_SIZE,
})

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_OUT_DIR = SCRIPT_DIR.parent / "data" / "out"

FILENAME = "06_L4.1_FLUXES_MERGED.parquet"
NEE_COL = "NEE_L3.1_L3.3_CUT_50_QCF_gfXG"

# Unit conversion: umol CO2 m-2 s-1 to g CO2 m-2 30min-1 (CO2 mass, no C conversion)
# = 60 x 30 x 44.0095 x 10-6 = 0.0792171
UMOL_TO_G_CO2_30MIN = 0.0792171

# Color scheme - Material Design colors per year
COLOR_2024 = "#3f51b5"  # Indigo
COLOR_2025 = "#ff6f00"  # Deep Orange
COLOR_2026 = "#00796b"  # Teal Dark

GREY_COLOR = "#6c757d"
DARK_COLOR = "#212529"

script_id = "10"

# ============================================================================
# Load data
# ============================================================================

filepath = Path(r"F:\Sync\luhk_work\dev-data\datasets-data\dataset_ch-hon_flux_product-data\data\out") / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

# ============================================================================
# Filter for March and prepare cumulative data
# ============================================================================

MONTH = 3
month_name = "März"

df['month'] = df.index.month
df['year'] = df.index.year

# Extract and convert NEE to g CO2 m-2 30min-1
nee = df[NEE_COL].copy() * UMOL_TO_G_CO2_30MIN

years = sorted(df['year'].unique())
print(f"Years available: {years}")

month_data = df[df['month'] == MONTH].copy()
print(f"\n{month_name} records: {len(month_data)}")

# Fractional day (day + hour/24 + minute/1440) for half-hourly alignment across years
month_data['day_fraction'] = (month_data.index.day +
                              month_data.index.hour / 24.0 +
                              month_data.index.minute / 1440.0)
nee_month = nee[month_data.index]

cumulative_by_year = {}
for year in years:
    year_mask = month_data['year'] == year
    year_data = month_data[year_mask]
    if len(year_data) == 0:
        continue

    nee_cum = nee_month[year_mask].fillna(0).cumsum()
    cumulative_by_year[year] = {
        'day_fraction': year_data['day_fraction'].values,
        'nee_cum': nee_cum.values,
        'nee_total': nee_cum.iloc[-1] if len(nee_cum) > 0 else 0,
        'days_count': len(year_data),
    }
    print(f"  {year}: {cumulative_by_year[year]['days_count']} days, "
          f"NEE={cumulative_by_year[year]['nee_total']:.1f} g CO2 m-2")

# ============================================================================
# Plot March cumulative CO2 comparison
# ============================================================================

fig, ax = plt.subplots(1, 1, figsize=(12, 7))

colors = {2024: COLOR_2024, 2025: COLOR_2025, 2026: COLOR_2026}

for year in years:
    if year not in cumulative_by_year:
        continue
    day_frac = cumulative_by_year[year]['day_fraction']
    nee_cum = cumulative_by_year[year]['nee_cum']
    color = colors.get(year, "#999999")
    ax.plot(day_frac, nee_cum, alpha=0.9, c=color, linewidth=1.8, label=str(year))
    ax.fill_between(day_frac, nee_cum, alpha=0.15, color=color)

ax.axhline(0, color=DARK_COLOR, linewidth=1, alpha=0.5, linestyle='-', zorder=5)
ax.text(0.01, 0.97, r"Kumulativer CO$_2$-Austausch im März – Vergleich (3 Jahre)",
        transform=ax.transAxes, ha='left', va='top', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', alpha=0.7, edgecolor='none'))
ax.set_xlabel("Tag im März")
ax.set_ylabel(r"Kumulativ (g CO$_2$ m$^{-2}$)")
ax.grid(True, alpha=0.2)
ax.legend(title="Jahr", loc='upper left', bbox_to_anchor=(0.01, 0.90), frameon=False)

# Positive cumulative -> net source: label the shaded area (lower right)
ax.text(0.98, 0.12, 'CO$_2$-Quelle', transform=ax.transAxes,
        ha='right', va='center', color='#212529', fontweight='bold', alpha=0.9)

# Axis limits from data range; y starts exactly on zero
all_days = [d for year in cumulative_by_year for d in cumulative_by_year[year]['day_fraction']]
all_nee = [v for year in cumulative_by_year for v in cumulative_by_year[year]['nee_cum']]
if all_days:
    ax.set_xlim(min(all_days), max(all_days))
    ax.set_ylim(0, max(all_nee) * 1.02)

# Spines + ticks (match other plots)
ax.spines['left'].set_visible(True)
ax.spines['bottom'].set_visible(True)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_linewidth(1.0)
ax.spines['bottom'].set_linewidth(1.0)
ax.spines['left'].set_color(DARK_COLOR)
ax.spines['bottom'].set_color(DARK_COLOR)
ax.tick_params(axis='x', which='major', length=6, width=1.0)
ax.tick_params(axis='y', which='major', length=5, width=0.8)
ax.tick_params(axis='both', which='major', pad=5)

plt.tight_layout()
outfile = DATA_OUT_DIR / "10_March_comparison.png"
fig.savefig(outfile, dpi=150, bbox_inches='tight')
print(f"\nSaved: {outfile}")
fig.show()

print("\nComparison complete.")
