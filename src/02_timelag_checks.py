import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import pandas as pd
from diive.core.io.files import load_parquet
from diive.core.plotting.plotfuncs import default_format
from diive.pkgs.analyses.histogram import Histogram

from funcs import detect_peak_range, adjust_range_for_eddypro

# Apply modern plot style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams.update({
    'figure.facecolor': '#f8f9fa',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#dee2e6',
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'axes.titleweight': 'bold',
    'axes.titlepad': 6,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.framealpha': 0.97,
    'legend.edgecolor': '#dee2e6',
    'legend.fontsize': 9,
    'grid.alpha': 0.25,
    'grid.color': '#dee2e6',
})

# ============================================================================
# Configuration
# ============================================================================

SOURCEFILE = r"..\data\out\FLUXES_L0_ALL.parquet"
OUTDIR = r"..\data\out"

gases = ['CO2', 'H2O']

# Ignore fringe bins where unclear lags accumulate
# (edge bins tend to collect non-physical lag values)
IGNORE_FRINGE_BINS = [5, 10]

# Reference acceptable lag window (for visualization)
LAG_WINDOW_MIN = 0.10  # seconds - lower bound of physically acceptable lag
LAG_WINDOW_MAX = 1.00  # seconds - upper bound of physically acceptable lag

# Histogram display range
HISTOGRAM_STARTBIN = 0
HISTOGRAM_ENDBIN = 10

# Gradient-based edge detection: controls boundary sensitivity (lower = stricter)
GRADIENT_THRESHOLD = 0.15

# Zoom range around peak in zoomed subplots [min_offset, max_offset] in seconds
ZOOM_MARGIN = [0.5, 1.5]

# ============================================================================
# Load and prepare data
# ============================================================================

df = load_parquet(filepath=SOURCEFILE)

tlag_cols = [c for c in df.columns if "TLAG" in c]
print(tlag_cols)

tlag_actual_cols = [c for c in tlag_cols if c.endswith("_ACTUAL")]
tlag_actual = df[tlag_actual_cols].copy()
first_date = tlag_actual.index[0].date()
last_date = tlag_actual.index[-1].date()

# ============================================================================
# Analysis loop
# ============================================================================

for gas in gases:
    gascol = f'{gas}_TLAG_ACTUAL'
    series = tlag_actual[gascol].copy()

    hist = Histogram(s=series, method='uniques', ignore_fringe_bins=IGNORE_FRINGE_BINS)
    results = hist.results
    peakbins = hist.peakbins

    locs = (results['BIN_START_INCL'] >= HISTOGRAM_STARTBIN) & (results['BIN_START_INCL'] <= HISTOGRAM_ENDBIN)
    results = results[locs].copy()

    peak = peakbins[0]
    peak_min, peak_max = detect_peak_range(results, peakbins, GRADIENT_THRESHOLD)
    eddypro_min, eddypro_max = adjust_range_for_eddypro(peak_min, peak_max, step=0.05)

    hist_bins = results['BIN_START_INCL'].copy()
    hist_counts = results['COUNTS'].copy()
    bar_args = dict(width=0.05, align='edge')
    zoom_min = peak - ZOOM_MARGIN[0]
    zoom_max = peak + ZOOM_MARGIN[1]

    # ========================================================================
    # Figure layout
    # ========================================================================

    fig = plt.figure(facecolor='#f8f9fa', figsize=(18, 9))

    # Header band
    fig.text(0.5, 0.97, f"Time Lag Analysis  ·  {gascol}",
             ha='center', va='top', fontsize=18, fontweight='bold', color='#212529')
    fig.text(0.5, 0.935, f"{first_date}  –  {last_date}",
             ha='center', va='top', fontsize=11, color='#6c757d')

    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        left=0.06, right=0.97, top=0.89, bottom=0.07,
        hspace=0.32, wspace=0.22
    )
    ax = fig.add_subplot(gs[0, 0])       # Overview histogram
    ax2 = fig.add_subplot(gs[1, 0])      # Overview time series
    ax_z = fig.add_subplot(gs[0, 1])     # Zoomed histogram
    ax2_z = fig.add_subplot(gs[1, 1])    # Zoomed time series

    # ========================================================================
    # Shared line/span helpers
    # ========================================================================

    def _add_range_markers(a, orient='v'):
        vline = a.axvline if orient == 'v' else a.axhline
        vspan = a.axvspan if orient == 'v' else a.axhspan
        vline(peak,      color='#212529', linewidth=2.2, alpha=0.9, zorder=5)
        vline(peak_min,  color='#17a2b8', linewidth=2.0, alpha=0.85, zorder=4)
        vline(peak_max,  color='#17a2b8', linewidth=2.0, alpha=0.85, zorder=4)
        vspan(peak_min,  peak_max,  alpha=0.12, color='#17a2b8', zorder=2)
        vline(eddypro_min, color='#fd7e14', linestyle=':', linewidth=2.0, alpha=0.8, zorder=3)
        vline(eddypro_max, color='#fd7e14', linestyle=':', linewidth=2.0, alpha=0.8, zorder=3)
        vspan(eddypro_min, eddypro_max, alpha=0.07, color='#fd7e14', zorder=1)
        vline(LAG_WINDOW_MIN, color='#6f42c1', linestyle='--', linewidth=1.4, alpha=0.6, zorder=3)
        vline(LAG_WINDOW_MAX, color='#6f42c1', linestyle='--', linewidth=1.4, alpha=0.6, zorder=3)

    # ========================================================================
    # Overview histogram (top-left)
    # ========================================================================

    ax.bar(x=hist_bins, height=hist_counts, color='#6c757d', zorder=90, **bar_args)
    _add_range_markers(ax, orient='v')

    # Legend on overview histogram only
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legend_handles = [
        Line2D([0], [0], color='#212529',  linewidth=2.2, label=f'Peak: {peak:.2f}s'),
        Patch(facecolor='#17a2b8', alpha=0.4,  label=f'Detected: {peak_min:.2f}–{peak_max:.2f}s'),
        Patch(facecolor='#fd7e14', alpha=0.35, label=f'EddyPro: {eddypro_min:.2f}–{eddypro_max:.2f}s'),
        Line2D([0], [0], color='#6f42c1',  linewidth=1.4, linestyle='--',
               label=f'Window: {LAG_WINDOW_MIN:.2f}–{LAG_WINDOW_MAX:.2f}s'),
    ]
    legend = ax.legend(handles=legend_handles, loc='upper right', frameon=True, fancybox=False)
    legend.get_frame().set_linewidth(0.8)

    default_format(ax=ax, ax_xlabel_txt="Lag (s)", ax_ylabel_txt="Counts")
    ax.set_title("Overview — Histogram")
    ax.locator_params(axis='both', nbins=15)

    # ========================================================================
    # Overview time series (bottom-left)
    # ========================================================================

    ax2.plot(series.index, series, alpha=0.55, c='#0d6efd', marker='.', ms=3.5, ls='none')
    _add_range_markers(ax2, orient='h')

    default_format(ax=ax2, ax_xlabel_txt="Date", ax_ylabel_txt="Lag (s)")
    ax2.set_title("Overview — Time Series")
    ax2.set_ylim([0, 10])
    ax2.locator_params(axis='y', nbins=10)

    # ========================================================================
    # Zoomed histogram (top-right)
    # ========================================================================

    ax_z.bar(x=hist_bins, height=hist_counts, color='#6c757d', zorder=90, **bar_args)
    _add_range_markers(ax_z, orient='v')

    default_format(ax=ax_z, ax_xlabel_txt="Lag (s)", ax_ylabel_txt="Counts")
    ax_z.set_title(f"Zoom [{ZOOM_MARGIN[0]}s, +{ZOOM_MARGIN[1]}s] — Histogram")
    ax_z.set_xlim(zoom_min, zoom_max)
    ax_z.locator_params(axis='both', nbins=12)

    # ========================================================================
    # Zoomed time series (bottom-right)
    # ========================================================================

    ax2_z.plot(series.index, series, alpha=0.55, c='#0d6efd', marker='.', ms=3.5, ls='none')
    _add_range_markers(ax2_z, orient='h')

    default_format(ax=ax2_z, ax_xlabel_txt="Date", ax_ylabel_txt="Lag (s)")
    ax2_z.set_title(f"Zoom [{ZOOM_MARGIN[0]}s, +{ZOOM_MARGIN[1]}s] — Time Series")
    ax2_z.set_ylim(zoom_min, zoom_max)
    ax2_z.locator_params(axis='y', nbins=12)

    outfile = f"{OUTDIR}/02_{gascol}_{first_date}_{last_date}.png"
    fig.savefig(outfile, dpi=150, bbox_inches='tight')
    print(f"Saved: {outfile}")
    fig.show()
