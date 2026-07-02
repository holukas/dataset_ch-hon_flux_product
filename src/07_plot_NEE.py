"""
Plot NEE daily-mean time series and cumulative flux in g CO2 m-2 30min-1
"""

import importlib.metadata
import warnings
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from diive.core.io.files import load_parquet

warnings.filterwarnings('ignore')
version_diive = importlib.metadata.version("diive")
print(f"diive version: v{version_diive}")

# Apply modern plot style
plt.style.use('seaborn-v0_8-darkgrid')
# Single font family and size for all text elements
FONT_FAMILY = 'sans-serif'
FONT_SIZE = 13

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
# For 30-minute flux data:
# = umol to min (x60) to 30min (x30) to ug CO2 (x44.0095) to g (x10-6)
# = 60 x 30 x 44.0095 x 10-6 = 0.0792171
UMOL_TO_G_CO2_30MIN = 0.0792171

script_id = "07"

# ============================================================================
# Load data
# ============================================================================

filepath = Path(r"F:\Sync\luhk_work\dev-data\datasets-data\dataset_ch-hon_flux_product-data\data\out") / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

# ============================================================================
# Extract and convert NEE
# ============================================================================

print(f"\nExtracting column: {NEE_COL}")
nee_umol = df[NEE_COL].copy()
print(f"Original units: umol m-2 s-1")
print(f"Valid data points: {nee_umol.notna().sum()} / {len(nee_umol)}")
print(f"Mean: {nee_umol.mean():.3f}")
print(f"Std: {nee_umol.std():.3f}")

# Convert to g CO2 m-2 30min-1
nee_co2 = nee_umol * UMOL_TO_G_CO2_30MIN
print(f"\nConverted units: g CO2 m-2 30min-1")
print(f"Mean: {nee_co2.mean():.6f}")
print(f"Std: {nee_co2.std():.6f}")

# Calculate cumulative flux (replacing NaN with 0 for accumulation)
nee_co2_filled = nee_co2.fillna(0)
nee_cumulative = nee_co2_filled.cumsum()
print(f"Cumulative range: {nee_cumulative.min():.3f} to {nee_cumulative.max():.3f} g CO2 m-2")

# ============================================================================
# Plot
# ============================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [1, 1]})

# Get year boundaries for vertical lines
years = nee_co2.index.year.unique()
year_starts = [pd.Timestamp(year, 1, 1) for year in years if pd.Timestamp(year, 1, 1) >= nee_co2.index[0]]


# German month abbreviations (avoids relying on system locale)
MONTHS_DE = {1: 'Jan', 2: 'Feb', 3: 'Mär', 4: 'Apr', 5: 'Mai', 6: 'Jun',
             7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Dez'}


# Custom date formatter: show all months as Jan Feb Mär etc
def date_formatter(x, pos):
    d = mdates.num2date(x)
    return MONTHS_DE[d.month]


# Top: Half-hourly time series as a line (g CO2 m-2 30min-1)
ax1.plot(nee_co2.index, nee_co2, color='#388E3C', alpha=0.8, linewidth=0.7)
ax1.axhline(0, color='#212529', linewidth=1, alpha=0.5, linestyle='-', zorder=5)
for year_start in year_starts:
    ax1.axvline(year_start, color='#6c757d', linewidth=1, alpha=0.4, linestyle='--', zorder=2)
ax1.text(0.01, 0.97, r"Halbstündlicher CO$_2$-Austausch", transform=ax1.transAxes,
         ha='left', va='top', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', alpha=0.7, edgecolor='none'))
ax1.set_ylabel(r"CO$_2$-Austausch (g CO$_2$ m$^{-2}$ 30min$^{-1}$)")
ax1.grid(True, alpha=0.2)

# Direction hints: positive NEE = release, negative NEE = uptake (right edge)
ARROW_COLOR = '#495057'
ax1.annotate('', xy=(0.985, 0.95), xytext=(0.985, 0.62), xycoords='axes fraction',
             arrowprops=dict(arrowstyle='-|>', color=ARROW_COLOR, lw=1.6))
ax1.text(0.955, 0.785, 'CO$_2$-Abgabe', transform=ax1.transAxes, rotation=90,
         ha='right', va='center', color=ARROW_COLOR, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', alpha=0.7, edgecolor='none'))
ax1.annotate('', xy=(0.985, 0.05), xytext=(0.985, 0.38), xycoords='axes fraction',
             arrowprops=dict(arrowstyle='-|>', color=ARROW_COLOR, lw=1.6))
ax1.text(0.955, 0.215, 'CO$_2$-Aufnahme', transform=ax1.transAxes, rotation=90,
         ha='right', va='center', color=ARROW_COLOR, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', alpha=0.7, edgecolor='none'))

# Format x-axis for top panel (same as bottom)
ax1.xaxis.set_major_locator(mdates.MonthLocator())
ax1.xaxis.set_major_formatter(ticker.FuncFormatter(date_formatter))
ax1.tick_params(axis='x', which='major', length=6, width=1.0, labelbottom=False)
ax1.tick_params(axis='y', which='major', length=5, width=0.8)
ax1.tick_params(axis='both', which='major', pad=5)

# Show spines
ax1.spines['left'].set_visible(True)
ax1.spines['bottom'].set_visible(True)
ax1.spines['right'].set_visible(False)
ax1.spines['top'].set_visible(False)
ax1.spines['left'].set_linewidth(1.0)
ax1.spines['bottom'].set_linewidth(1.0)
ax1.spines['left'].set_color('#212529')
ax1.spines['bottom'].set_color('#212529')

# Bottom: Cumulative curve
ax2.plot(nee_cumulative.index, nee_cumulative, alpha=0.85, c='#388E3C', linewidth=1.2)
ax2.fill_between(nee_cumulative.index, nee_cumulative, alpha=0.15, color='#388E3C')
ax2.axhline(0, color='#212529', linewidth=1, alpha=0.5, linestyle='-', zorder=5)
for year_start in year_starts:
    ax2.axvline(year_start, color='#6c757d', linewidth=1, alpha=0.4, linestyle='--', zorder=2)

# Calculate total and yearly statistics
total_nee = nee_cumulative.iloc[-1]
total_days = (nee_cumulative.index[-1] - nee_cumulative.index[0]).days + 1
total_avg = total_nee / total_days if total_days > 0 else 0

# Calculate per-year totals and days
years_unique = sorted(nee_cumulative.index.year.unique())
yearly_text = ""
for year in years_unique:
    year_data = nee_cumulative[nee_cumulative.index.year == year]
    if len(year_data) > 0:
        year_total = year_data.iloc[-1] - (year_data.iloc[0] if len(year_data) > 1 else 0)
        if year == years_unique[0]:
            # First year: total is just the last value
            year_total = year_data.iloc[-1]
        else:
            # Subsequent years: difference from previous year
            prev_year_data = nee_cumulative[nee_cumulative.index.year == year - 1]
            year_total = year_data.iloc[-1] - prev_year_data.iloc[-1]

        year_days = (year_data.index[-1] - year_data.index[0]).days + 1
        year_avg = year_total / year_days if year_days > 0 else 0
        yearly_text += f"{year}: {year_total:.0f} ({year_days} Tage, {year_avg:.1f} g CO$_2$/Tag)\n"

# Display total and yearly info
textstr = f'Gesamt: {total_nee:.0f} g CO$_2$ m$^{{-2}}$ ({total_days} Tage, {total_avg:.1f} g CO$_2$/Tag)\n\n{yearly_text}'
ax2.text(0.05, 0.82, textstr, transform=ax2.transAxes, fontweight='bold',
         verticalalignment='top', horizontalalignment='left',
         color='#1b5e20', alpha=0.95,
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#ffffff', alpha=0.05, edgecolor='none'))

ax2.text(0.01, 0.97, r"Kumulativer CO$_2$-Austausch", transform=ax2.transAxes,
         ha='left', va='top', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', alpha=0.7, edgecolor='none'))
ax2.set_ylabel(r"Kumulativ (g CO$_2$ m$^{-2}$)")
ax2.grid(True, alpha=0.2)

# Y-axis: start at zero
ax2.set_ylim(bottom=0)


# Date formatter for bottom panel: show year at January, months otherwise
def year_formatter(x, pos):
    d = mdates.num2date(x)
    if d.month == 1:
        return f'{d.year}'
    else:
        return MONTHS_DE[d.month]


# Improve date formatting on x-axis
ax2.xaxis.set_major_locator(mdates.MonthLocator())  # Major ticks every month
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(year_formatter))  # Apply year formatter
ax2.xaxis.set_minor_locator(mdates.MonthLocator())  # Minor ticks every month (same for visibility)

# Show tick marks on all months
ax2.tick_params(axis='x', which='major', length=6, width=1.0)
ax2.tick_params(axis='y', which='major', length=5, width=0.8)
ax2.tick_params(axis='both', which='major', pad=5)

# Format x-axis labels (no rotation)
plt.setp(ax2.xaxis.get_majorticklabels(), ha='center')

# Show spines
ax2.spines['left'].set_visible(True)
ax2.spines['bottom'].set_visible(True)
ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_linewidth(1.0)
ax2.spines['bottom'].set_linewidth(1.0)
ax2.spines['left'].set_color('#212529')
ax2.spines['bottom'].set_color('#212529')

# Remove whitespace by setting x-axis limits to data range
ax1.set_xlim(nee_co2.index[0], nee_co2.index[-1])
ax2.set_xlim(nee_cumulative.index[0], nee_cumulative.index[-1])

plt.tight_layout()
outfile = DATA_OUT_DIR / f"07_NEE_timeseries_{nee_co2.index[0].date()}_{nee_co2.index[-1].date()}.png"
fig.savefig(outfile, dpi=150, bbox_inches='tight')
print(f"\nSaved: {outfile}")

fig.show()
