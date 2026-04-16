"""
Plot LE (latent heat flux) as evapotranspiration (ET) in mm 30min⁻¹
"""

import importlib.metadata
import warnings
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from diive.core.io.files import load_parquet
from diive.core.plotting.dielcycle import DielCycle

warnings.filterwarnings('ignore')
version_diive = importlib.metadata.version("diive")
print(f"diive version: v{version_diive}")

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
LE_COL = "LE_L3.1_L3.3_CUT_NONE_QCF_gfXG"

# Unit conversion: W m⁻² → mm 30min⁻¹ (evapotranspiration)
# ET (mm) = LE (W m⁻²) × time (s) / (λ (J/kg) × ρ (kg/m³))
# λ = 2.45 MJ/kg (latent heat of vaporization)
# ρ = 1000 kg/m³ (water density)
# 30 min = 1800 seconds
# = 1800 / (2.45e6 × 1000) = 7.3469e-4 mm/W
LE_TO_ET_30MIN = 7.3469e-4

script_id = "08"

# ============================================================================
# Load data
# ============================================================================

filepath = DATA_OUT_DIR / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

# ============================================================================
# Extract and convert LE to ET
# ============================================================================

print(f"\nExtracting column: {LE_COL}")
le_wm2 = df[LE_COL].copy()
print(f"Original units: W m⁻²")
print(f"Valid data points: {le_wm2.notna().sum()} / {len(le_wm2)}")
print(f"Mean: {le_wm2.mean():.3f}")
print(f"Std: {le_wm2.std():.3f}")

# Convert to ET mm 30min⁻¹
et_mm = le_wm2 * LE_TO_ET_30MIN
print(f"\nConverted units: mm 30min⁻¹ (evapotranspiration)")
print(f"Mean: {et_mm.mean():.6f}")
print(f"Std: {et_mm.std():.6f}")

# Calculate cumulative ET (replacing NaN with 0 for accumulation)
et_mm_filled = et_mm.fillna(0)
et_cumulative = et_mm_filled.cumsum()
print(f"Cumulative range: {et_cumulative.min():.3f} to {et_cumulative.max():.3f} mm")

# ============================================================================
# Plot
# ============================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [1, 1]})

# Get year boundaries for vertical lines
years = et_mm.index.year.unique()
year_starts = [pd.Timestamp(year, 1, 1) for year in years if pd.Timestamp(year, 1, 1) >= et_mm.index[0]]


# Custom date formatter: show all months as Jan Feb Mar etc
def date_formatter(x, pos):
    d = mdates.num2date(x)
    return d.strftime('%b')


# Top: Time series (mm)
ax1.plot(et_mm.index, et_mm, alpha=0.8, c='#0d6efd', linewidth=0.7)
ax1.fill_between(et_mm.index, et_mm, alpha=0.15, color='#0d6efd')
ax1.axhline(0, color='#212529', linewidth=1, alpha=0.5, linestyle='-', zorder=5)
for year_start in year_starts:
    ax1.axvline(year_start, color='#6c757d', linewidth=1, alpha=0.4, linestyle='--', zorder=2)
ax1.set_title(r"LE Time Series (mm 30min$^{-1}$)", fontsize=14, fontweight='bold')
ax1.set_ylabel(r"ET (mm 30min$^{-1}$)")
ax1.grid(True, alpha=0.2)

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
ax2.plot(et_cumulative.index, et_cumulative, alpha=0.85, c='#0d6efd', linewidth=1.2)
ax2.fill_between(et_cumulative.index, et_cumulative, alpha=0.15, color='#0d6efd')
ax2.axhline(0, color='#212529', linewidth=1, alpha=0.5, linestyle='-', zorder=5)
for year_start in year_starts:
    ax2.axvline(year_start, color='#6c757d', linewidth=1, alpha=0.4, linestyle='--', zorder=2)

# Calculate total and yearly statistics
total_et = et_cumulative.iloc[-1]
total_days = (et_cumulative.index[-1] - et_cumulative.index[0]).days + 1
total_avg = total_et / total_days if total_days > 0 else 0

# Calculate per-year totals and days
years_unique = sorted(et_cumulative.index.year.unique())
yearly_text = ""
for year in years_unique:
    year_data = et_cumulative[et_cumulative.index.year == year]
    if len(year_data) > 0:
        year_total = year_data.iloc[-1] - (year_data.iloc[0] if len(year_data) > 1 else 0)
        if year == years_unique[0]:
            # First year: total is just the last value
            year_total = year_data.iloc[-1]
        else:
            # Subsequent years: difference from previous year
            prev_year_data = et_cumulative[et_cumulative.index.year == year - 1]
            year_total = year_data.iloc[-1] - prev_year_data.iloc[-1]

        year_days = (year_data.index[-1] - year_data.index[0]).days + 1
        year_avg = year_total / year_days if year_days > 0 else 0
        yearly_text += f"{year}: {year_total:.0f} ({year_days} days, {year_avg:.1f} mm/day)\n"

# Display total and yearly info
textstr = f'Total: {total_et:.0f} mm ({total_days} days, {total_avg:.1f} mm/day)\n\n{yearly_text}'
ax2.text(0.05, 0.92, textstr, transform=ax2.transAxes, fontsize=11, fontweight='bold',
         verticalalignment='top', horizontalalignment='left',
         color='#0c63e4', alpha=0.95, family='monospace',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#ffffff', alpha=0.05, edgecolor='none'))

ax2.set_title(r"Cumulative LE (mm)", fontsize=14, fontweight='bold')
ax2.set_ylabel(r"Cumulative ET (mm)")
ax2.grid(True, alpha=0.2)

# Y-axis: start at zero
ax2.set_ylim(bottom=0)


# Date formatter for bottom panel: show year at January, months otherwise
def year_formatter(x, pos):
    d = mdates.num2date(x)
    if d.month == 1:
        return f'{d.year}'
    else:
        return d.strftime('%b')


# Improve date formatting on x-axis
ax2.xaxis.set_major_locator(mdates.MonthLocator())  # Major ticks every month
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(year_formatter))  # Apply year formatter
ax2.xaxis.set_minor_locator(mdates.MonthLocator())  # Minor ticks every month (same for visibility)

# Show tick marks on all months
ax2.tick_params(axis='x', which='major', length=6, width=1.0)
ax2.tick_params(axis='y', which='major', length=5, width=0.8)
ax2.tick_params(axis='both', which='major', pad=5)

# Format x-axis labels (no rotation)
plt.setp(ax2.xaxis.get_majorticklabels(), fontsize=9, ha='center')

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
ax1.set_xlim(et_mm.index[0], et_mm.index[-1])
ax2.set_xlim(et_cumulative.index[0], et_cumulative.index[-1])

plt.tight_layout()
outfile = DATA_OUT_DIR / f"08_LE_timeseries_{et_mm.index[0].date()}_{et_mm.index[-1].date()}.png"
fig.savefig(outfile, dpi=150, bbox_inches='tight')
print(f"\nSaved: {outfile}")

fig.show()

# ============================================================================
# Diel Cycle Analysis
# ============================================================================

fig = plt.figure(facecolor='#ffffff', figsize=(14, 10), dpi=150)
gs = gridspec.GridSpec(1, 1)
gs.update(wspace=0.3, hspace=0.3, left=0.08, right=0.95, top=0.95, bottom=0.08)
ax_dc = fig.add_subplot(gs[0, 0])

# Plot diel cycle for LE
dc_le = DielCycle(series=et_mm)
units = r'(mm 30min$^{-1}$)'
dc_le.plot(ax=ax_dc, title=f"Mean Diel Cycle", txt_ylabel_units=units,
           each_month=True, legend_n_col=4, ylabel=r"Mean ET",
           showgrid=True, show_xticklabels=True, show_xlabel=True)

# Add variable name in upper right corner
fig.text(0.94, 0.96, LE_COL, ha='right', va='top', fontsize=10,
         style='italic', color='#6c757d', weight='normal')

# Remove ticks on secondary (right and top) spines
ax_dc.tick_params(axis='x', which='both', top=False)
ax_dc.tick_params(axis='y', which='both', right=False)

plt.tight_layout()
outfile_dc = DATA_OUT_DIR / f"08_LE_DielCycle_{et_mm.index[0].date()}_{et_mm.index[-1].date()}.png"
fig.savefig(outfile_dc, dpi=150, bbox_inches='tight')
print(f"Saved: {outfile_dc}")

fig.show()
