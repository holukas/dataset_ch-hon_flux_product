"""
Plot LE (latent heat flux) mean diel cycle (per month) as evapotranspiration (ET) in mm 30min-1
"""

import importlib.metadata
import warnings
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from diive.core.io.files import load_parquet
from diive.core.plotting.dielcycle import DielCycle

warnings.filterwarnings('ignore')
version_diive = importlib.metadata.version("diive")
print(f"diive version: v{version_diive}")

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
LE_COL = "LE_L3.1_L3.3_CUT_NONE_QCF_gfXG"

# Unit conversion: W m-2 to mm 30min-1 (evapotranspiration)
# ET depth = LE (W m-2) x time (s) / (lambda (J/kg) x rho (kg/m3)), then m -> mm (x1000).
# rho = 1000 kg/m3 cancels the m->mm factor (1 kg/m2 of water = 1 mm), so:
# ET (mm) = LE x time / lambda,  lambda = 2.45 MJ/kg, time = 1800 s (30 min)
# = 1800 / 2.45e6 = 7.3469e-4 mm per (W m-2)
LE_TO_ET_30MIN = 7.3469e-4

script_id = "09"

# ============================================================================
# Load data
# ============================================================================

filepath = Path(r"F:\Sync\luhk_work\dev-data\datasets-data\dataset_ch-hon_flux_product-data\data\out") / FILENAME
print(f"Loading: {filepath}")
df = load_parquet(filepath=str(filepath))

# ============================================================================
# Extract and convert LE to ET
# ============================================================================

print(f"\nExtracting column: {LE_COL}")
le_wm2 = df[LE_COL].copy()
print(f"Original units: W m-2")
print(f"Valid data points: {le_wm2.notna().sum()} / {len(le_wm2)}")

# Convert to ET mm 30min-1
et_mm = le_wm2 * LE_TO_ET_30MIN
print(f"\nConverted units: mm 30min-1 (evapotranspiration)")
print(f"Mean: {et_mm.mean():.6f}")
print(f"Std: {et_mm.std():.6f}")

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
dc_le.plot(ax=ax_dc, each_month=True,
           show_xticklabels=True, show_xlabel=True)
ax_dc.text(0.01, 0.97, "Mittlerer Wasseraustausch im Tagesverlauf", transform=ax_dc.transAxes,
           ha='left', va='top', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', alpha=0.7, edgecolor='none'))
ax_dc.set_ylabel(rf"Wasseraustausch {units}", fontsize=FONT_SIZE)
ax_dc.set_xlabel("Tageszeit (Stunden)", fontsize=FONT_SIZE)
ax_dc.tick_params(axis='both', labelsize=FONT_SIZE)
ax_dc.grid(False)

# Translate the month legend (diive labels it in English)
EN_TO_DE_MONTH = {'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mär', 'Apr': 'Apr',
                  'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug',
                  'Sep': 'Sep', 'Oct': 'Okt', 'Nov': 'Nov', 'Dec': 'Dez'}
legend = ax_dc.get_legend()
if legend is not None:
    for text in legend.get_texts():
        text.set_text(EN_TO_DE_MONTH.get(text.get_text(), text.get_text()))
        text.set_fontsize(FONT_SIZE)

# Remove ticks on secondary (right and top) spines
ax_dc.tick_params(axis='x', which='both', top=False)
ax_dc.tick_params(axis='y', which='both', right=False)

ax_dc.set_ylim(0)

plt.tight_layout()
outfile_dc = DATA_OUT_DIR / f"09_LE_DielCycle_{et_mm.index[0].date()}_{et_mm.index[-1].date()}.png"
fig.savefig(outfile_dc, dpi=150, bbox_inches='tight')
print(f"Saved: {outfile_dc}")

fig.show()
