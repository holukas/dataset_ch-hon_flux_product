"""
Plot NEE mean diel cycle (per month) in g C m-2 30min-1
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

# Unit conversion: umol CO2 m-2 s-1 to g C m-2 30min-1
# For 30-minute flux data:
# = umol to min (x60) to 30min (x30) to ug CO2 (x44.0095) to g (x10-6) to g C (x12/44)
# = 60 x 30 x 44.0095 x 10-6 x (12/44) = 0.02161926
UMOL_TO_G_C_30MIN = 0.02161926

script_id = "08"

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

# Convert to g C m-2 30min-1
nee_gc = nee_umol * UMOL_TO_G_C_30MIN
print(f"\nConverted units: g C m-2 30min-1")
print(f"Mean: {nee_gc.mean():.6f}")
print(f"Std: {nee_gc.std():.6f}")

# ============================================================================
# Diel Cycle Analysis
# ============================================================================

fig = plt.figure(facecolor='#ffffff', figsize=(14, 10), dpi=150)
gs = gridspec.GridSpec(1, 1)
gs.update(wspace=0.3, hspace=0.3, left=0.08, right=0.95, top=0.95, bottom=0.08)
ax_dc = fig.add_subplot(gs[0, 0])

# Plot diel cycle for NEE
dc_nee = DielCycle(series=nee_gc)
units = r'(g C m$^{-2}$ 30min$^{-1}$)'
dc_nee.plot(ax=ax_dc, each_month=True,
            show_xticklabels=True, show_xlabel=True)
ax_dc.set_title("Mittlerer Tagesgang", fontweight='bold')
ax_dc.set_ylabel(rf"Kohlenstoffaustausch {units}")
ax_dc.set_xlabel("Tageszeit (Stunden)")
ax_dc.grid(True, alpha=0.2)

# Translate the month legend (diive labels it in English)
EN_TO_DE_MONTH = {'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mär', 'Apr': 'Apr',
                  'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug',
                  'Sep': 'Sep', 'Oct': 'Okt', 'Nov': 'Nov', 'Dec': 'Dez'}
legend = ax_dc.get_legend()
if legend is not None:
    for text in legend.get_texts():
        text.set_text(EN_TO_DE_MONTH.get(text.get_text(), text.get_text()))

# Add variable name in upper right corner
fig.text(0.94, 0.96, NEE_COL, ha='right', va='top',
         style='italic', color='#6c757d', weight='normal')

# Remove ticks on secondary (right and top) spines
ax_dc.tick_params(axis='x', which='both', top=False)
ax_dc.tick_params(axis='y', which='both', right=False)

plt.tight_layout()
outfile_dc = DATA_OUT_DIR / f"08_NEE_DielCycle_{nee_gc.index[0].date()}_{nee_gc.index[-1].date()}.png"
fig.savefig(outfile_dc, dpi=150, bbox_inches='tight')
print(f"Saved: {outfile_dc}")

fig.show()
