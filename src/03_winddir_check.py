"""
Check wind direction across years by comparing to reference
"""

from diive.core.io.files import load_parquet
from diive.core.plotting.heatmap_datetime import HeatmapDateTime
from diive.pkgs.corrections.winddiroffset import WindDirOffset

SOURCEFILE = r"..\data\out\FLUXES_L0_ALL.parquet"
df = load_parquet(filepath=SOURCEFILE)

col = 'WD'
wd = df[col].copy()

# Prepare input data
wd = wd.loc[wd.index.year >= 2024]
wd = wd.dropna()

wds = WindDirOffset(winddir=wd, offset_start=-50, offset_end=50, hist_ref_years=[2025], hist_n_bins=360)
yearlyoffsets_df = wds.get_yearly_offsets()
print(yearlyoffsets_df)
print(wd)
HeatmapDateTime(series=wd).show()

# s_corrected = wds.get_corrected_wind_directions()
# print(s_corrected)
# HeatmapDateTime(series=s_corrected).show()
