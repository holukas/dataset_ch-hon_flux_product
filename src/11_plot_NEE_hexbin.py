"""
Plot NEE as hexbin: air temperature (TA_EP) vs vapor pressure deficit (VPD_EP)
Shows NEE response to environmental conditions (temperature stress and drought)
"""

import importlib.metadata
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from diive.core.io.files import load_parquet
import diive as dv


warnings.filterwarnings('ignore')
version_diive = importlib.metadata.version("diive")
print(f"diive version: v{version_diive}")

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_OUT_DIR = SCRIPT_DIR.parent / "data" / "out"

FILENAME = "06_L4.1_FLUXES_MERGED.parquet"
NEE_COL = "NEE_L3.1_L3.3_CUT_50_QCF_gfXG"
TA_COL = "TA_EP"      # Temperature (air temperature from energy balance)
VPD_COL = "VPD_EP"    # Vapor pressure deficit from energy balance

# Unit conversion: µmol CO₂ m⁻² s⁻¹ → g C m⁻² 30min⁻¹
NEE_UMOL_TO_G_C_30MIN = 0.02161926

# Hexbin settings
GRIDSIZE = 20         # Resolution of hexbin grid (lower = larger hexagons, better visibility)
CMAP = 'RdYlBu_r'       # Color map: Red (low NEE) → Yellow → Green (high NEE)
MINCNT = 5            # Minimum observations per hexagon for visibility

script_id = "11"

# ============================================================================
# Load data
# ============================================================================

filepath = DATA_OUT_DIR / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

df = df.loc[(df['SW_IN_POT'] > 20)].copy()

# ============================================================================
# Extract and prepare variables
# ============================================================================

print(f"\nExtracting variables:")
print(f"  NEE column: {NEE_COL}")
print(f"  Temperature column: {TA_COL}")
print(f"  VPD column: {VPD_COL}")

# NEE: convert to g C m-2 30min-1
nee_umol = df[NEE_COL].copy()
nee = nee_umol * NEE_UMOL_TO_G_C_30MIN

# Environmental variables
ta = df[TA_COL].copy()      # Temperature (C)
vpd = df[VPD_COL].copy()    # Vapor pressure deficit (kPa)

# Remove NaN for hexbin plot
valid = nee.notna() & ta.notna() & vpd.notna()
nee_clean = nee[valid]
ta_clean = ta[valid]
vpd_clean = vpd[valid]

print(f"\nData statistics:")
print(f"  Valid records: {len(nee_clean)} / {len(nee)}")
print(f"  NEE range: {nee_clean.min():.3f} to {nee_clean.max():.3f} g C m-2")
print(f"  TA range: {ta_clean.min():.1f} to {ta_clean.max():.1f} C")
print(f"  VPD range: {vpd_clean.min():.2f} to {vpd_clean.max():.2f} kPa")

# ============================================================================
# Create hexbin plot using diive
# ============================================================================

# Ensure series have names for automatic labeling
ta_clean.name = TA_COL
vpd_clean.name = VPD_COL
nee_clean.name = NEE_COL

# Create diive hexbin plot with mean aggregation for better visibility
import numpy as np
hex_plot = dv.hexbinplot(x=ta_clean, y=vpd_clean, z=nee_clean, normalize_axes=True,
                         gridsize=GRIDSIZE, cmap=CMAP, figsize=(12, 9),
                         reduce_C_function=np.mean, mincnt=MINCNT,
                         edgecolors='face',
                         cb_digits_after_comma=1,
                         vmin=-0.3,
                         # vmin=nee_clean.min(),
                         vmax=0.3)

# Plot the hexbin (important: must call plot() to render hexagons)
hex_plot.plot()

# Get figure and axes
fig = hex_plot.fig
ax = hex_plot.ax

# Customize plot
ax.set_title(r"NEE Response to Temperature and Vapor Pressure Deficit",
             fontsize=14, fontweight='bold')
ax.set_xlabel(r"Air Temperature TA_EP (°C)", fontsize=12)
ax.set_ylabel(r"Vapor Pressure Deficit VPD_EP (kPa)", fontsize=12)
ax.grid(True, alpha=0.2)

# Styling
ax.spines['left'].set_visible(True)
ax.spines['bottom'].set_visible(True)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_linewidth(1.0)
ax.spines['bottom'].set_linewidth(1.0)
ax.spines['left'].set_color('#212529')
ax.spines['bottom'].set_color('#212529')
ax.tick_params(axis='both', which='major', length=6, width=1.2, colors='#212529')

# Note: Skip tight_layout() due to colorbar compatibility with matplotlib layout engine
outfile = DATA_OUT_DIR / f"{script_id}_NEE_hexbin_TA_VPD_{nee_clean.index[0].date()}_{nee_clean.index[-1].date()}.png"
fig.savefig(outfile, dpi=150, bbox_inches='tight')
print(f"\nSaved: {outfile}")

fig.show()

# ============================================================================
# Print interpretation guide
# ============================================================================

print("\n" + "="*70)
print("INTERPRETATION GUIDE:")
print("="*70)
print(f"""
X-axis (Temperature, TA_EP in C):
  - Shows how NEE varies across temperature range ({ta_clean.min():.1f} to {ta_clean.max():.1f} C)
  - Optimal growth temperature visible as peak NEE
  - Cold/hot stress visible as reduced NEE at extremes

Y-axis (Vapor Pressure Deficit, VPD_EP in kPa):
  - Shows how NEE varies with atmospheric moisture demand
  - Low VPD: humid conditions, low evaporative stress
  - High VPD: dry conditions, potential stomatal closure and photosynthetic limitation

Color (NEE in g C m-2):
  - Red/Dark: Low carbon uptake (stress conditions)
  - Yellow: Moderate carbon uptake
  - Green/Bright: High carbon uptake (optimal conditions)

Patterns to look for:
  - Peak NEE at moderate temperature and low-moderate VPD
  - Reduced NEE at extreme temperatures or very high VPD (drought stress)
  - Data density shown by hexagon size (larger = more observations)
""")
print("="*70)
