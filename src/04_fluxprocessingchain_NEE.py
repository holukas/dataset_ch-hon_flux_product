import numpy as np
import importlib.metadata
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats
import seaborn as sns

from diive.core.dfun.stats import sstats  # Time series stats
from diive.core.io.files import save_parquet, load_parquet
from diive.core.plotting.timeseries import TimeSeries  # For simple (interactive) time series plotting
from diive.pkgs.flux.hqflux import analyze_highest_quality_flux
from diive.pkgs.fluxprocessingchain.fluxprocessingchain import FluxProcessingChain
from diive.pkgs.fluxprocessingchain.fluxprocessingchain import LoadEddyProOutputFiles

warnings.filterwarnings(action='ignore', category=FutureWarning)
warnings.filterwarnings(action='ignore', category=UserWarning)
version_diive = importlib.metadata.version("diive")
print(f"diive version: v{version_diive}")

# Site settings
FLUXVAR = "FC"
SITE_LAT = 47.41887
SITE_LON = 8.491318
UTC_OFFSET = 1
NIGHTTIME_THRESHOLD = 20
DAYTIME_ACCEPT_QCF_BELOW = 1
NIGHTTIMETIME_ACCEPT_QCF_BELOW = 1
SOURCEDIR = r"..\data\out"
FILENAME = r"FLUXES_L0_ALL.parquet"
OUTDIR = r"..\data\out"
script_id = "04"

# Load data
FILEPATH = Path(SOURCEDIR) / FILENAME
print(f"Data will be loaded from the following file:\n{FILEPATH}")
maindf = load_parquet(filepath=FILEPATH)

# Remove wind directions
locs = (maindf['WD'] > 180) & (maindf['WD'] < 350)
maindf.loc[locs, :] = np.nan

# Plot
TimeSeries(series=maindf[FLUXVAR]).plot()

# Flux Processing Chain (FPC)
fpc = FluxProcessingChain(
    df=maindf,
    fluxcol=FLUXVAR,
    site_lat=SITE_LAT,
    site_lon=SITE_LON,
    utc_offset=UTC_OFFSET,
    nighttime_threshold=NIGHTTIME_THRESHOLD,
    daytime_accept_qcf_below=DAYTIME_ACCEPT_QCF_BELOW,
    nighttimetime_accept_qcf_below=NIGHTTIMETIME_ACCEPT_QCF_BELOW
)

# ----------------------
# LEVEL-2
# ----------------------
TEST_SSITC = True  # True or False (default: True)
TEST_SSITC_SETFLAG_TIMEPERIOD = None
TEST_GAS_COMPLETENESS = False  # True or False (default: True)
TEST_SPECTRAL_CORRECTION_FACTOR = True  # True or False (default: True)

# Signal strength
TEST_SIGNAL_STRENGTH = True  # True or False (default: True)
TEST_SIGNAL_STRENGTH_COL = 'CUSTOM_AGC_MEAN'  # Variable name in fluxnet files
TEST_SIGNAL_STRENGTH_METHOD = 'discard above'  # 'discard above' or 'discard below'
TEST_SIGNAL_STRENGTH_THRESHOLD = 90
# TimeSeries(series=maindf[TEST_SIGNAL_STRENGTH_COL]).plot()

TEST_RAWDATA = True  # Default True
TEST_RAWDATA_SPIKES = True  # Default True
TEST_RAWDATA_AMPLITUDE = False  # Default True
TEST_RAWDATA_DROPOUT = True  # Default True
TEST_RAWDATA_ABSLIM = False  # Default False
TEST_RAWDATA_SKEWKURT_HF = False  # Default False
TEST_RAWDATA_SKEWKURT_SF = False  # Default False
TEST_RAWDATA_DISCONT_HF = False  # Default False
TEST_RAWDATA_DISCONT_SF = False  # Default False
TEST_RAWDATA_ANGLE_OF_ATTACK = False  # Default False
TEST_RAWDATA_ANGLE_OF_ATTACK_APPLICATION_DATES = []
TEST_RAWDATA_STEADINESS_OF_HORIZONTAL_WIND = False  # Default False
LEVEL2_SETTINGS = {
    'signal_strength': {
        'apply': TEST_SIGNAL_STRENGTH,
        'signal_strength_col': TEST_SIGNAL_STRENGTH_COL,
        'method': TEST_SIGNAL_STRENGTH_METHOD,
        'threshold': TEST_SIGNAL_STRENGTH_THRESHOLD},
    'raw_data_screening_vm97': {
        'apply': TEST_RAWDATA,
        'spikes': TEST_RAWDATA_SPIKES,
        'amplitude': TEST_RAWDATA_AMPLITUDE,
        'dropout': TEST_RAWDATA_DROPOUT,
        'abslim': TEST_RAWDATA_ABSLIM,
        'skewkurt_hf': TEST_RAWDATA_SKEWKURT_HF,
        'skewkurt_sf': TEST_RAWDATA_SKEWKURT_SF,
        'discont_hf': TEST_RAWDATA_DISCONT_HF,
        'discont_sf': TEST_RAWDATA_DISCONT_SF},
    'ssitc': {
        'apply': TEST_SSITC,
        'setflag_timeperiod': TEST_SSITC_SETFLAG_TIMEPERIOD},
    'gas_completeness': {
        'apply': TEST_GAS_COMPLETENESS},
    'spectral_correction_factor': {
        'apply': TEST_SPECTRAL_CORRECTION_FACTOR},
    'angle_of_attack': {
        'apply': TEST_RAWDATA_ANGLE_OF_ATTACK,
        'application_dates': TEST_RAWDATA_ANGLE_OF_ATTACK_APPLICATION_DATES},
    'steadiness_of_horizontal_wind': {
        'apply': TEST_RAWDATA_STEADINESS_OF_HORIZONTAL_WIND}
}
fpc.level2_quality_flag_expansion(**LEVEL2_SETTINGS)
fpc.finalize_level2()
# print([x for x in fpc.fpc_df.columns if 'L2' in x])
# fpc.level2_qcf.showplot_qcf_heatmaps()
# fpc.level2_qcf.report_qcf_evolution()

# ----------------------
# LEVEL-3.1
# ----------------------
fpc.level31_storage_correction(gapfill_storage_term=True)
fpc.finalize_level31()
# print([x for x in fpc.fpc_df.columns if 'L3.1' in x])
# fpc.level31.showplot()
# fpc.level31.report()
# print(f"{fpc.filteredseries.name} \n(quality-controlled Level-3.1 version of {fpc.fluxcol})")
# TimeSeries(series=fpc.fpc_df[fpc.filteredseries.name]).plot()

# analyze_highest_quality_flux(flux=fpc.fpc_df[fpc.filteredseries_hq.name], nighttime_flag=fpc.fpc_df['NIGHTTIME'])

# ----------------------
# LEVEL-3.2
# ----------------------
fpc.level32_stepwise_outlier_detection()
WINDOW_LENGTH = 48 * 13
N_SIGMA_DT = 5.5
N_SIGMA_NT = 5.5
USE_DIFFERENCING = True
SEPARATE_DAY_NIGHT = True
fpc.level32_flag_outliers_hampel_dtnt_test(window_length=WINDOW_LENGTH, n_sigma_dt=N_SIGMA_DT, n_sigma_nt=N_SIGMA_NT, use_differencing=USE_DIFFERENCING, separate_day_night=SEPARATE_DAY_NIGHT,
                                           showplot=True, verbose=True, repeat=True)
fpc.level32_addflag()
fpc.finalize_level32()
# print([x for x in fpc.fpc_df.columns if 'L3.2' in x])
# fpc.level32_qcf.showplot_qcf_heatmaps()
# TimeSeries(series=fpc.filteredseries).plot()
# fpc.level32_qcf.report_qcf_evolution()
# fpc.level32_qcf.report_qcf_flags()

# ----------------------
# LEVEL-3.3
# ----------------------
USTAR_SCENARIOS = ['CUT_50']
USTAR_THRESHOLDS = [0.1]
fpc.level33_constant_ustar(thresholds=USTAR_THRESHOLDS,
                           threshold_labels=USTAR_SCENARIOS,
                           showplot=False)
fpc.finalize_level33()

print(x for x in fpc.fpc_df.columns if 'L3.3' in x)
for key, value in fpc.level33_qcf.items():
    fpc.level33_qcf[key].report_qcf_evolution()
for key, value in fpc.level33_qcf.items():
    fpc.level33_qcf[key].report_qcf_series()
# for key, value in fpc.level33_qcf.items():
#     fpc.level33_qcf[key].report_qcf_flags()

# Flux variable names
fluxes_qcf = [c for c in fpc.fpc_df.columns if str(c).endswith("_QCF") and not str(c).startswith("FLAG_") and "L3.3" in c]
fluxes_qcf0 = [c for c in fpc.fpc_df.columns if
               str(c).endswith("_QCF0") and not str(c).startswith("FLAG_") and "L3.3" in c]
print(f"Quality-controlled fluxes: {fluxes_qcf}")
print(f"Quality-controlled fluxes, HIGHEST QUALITY: {fluxes_qcf0}")
if (DAYTIME_ACCEPT_QCF_BELOW == 1) & (NIGHTTIMETIME_ACCEPT_QCF_BELOW == 1):
    print(f"{'*' * 100}\nNote that since only QCF below 1 is accepted for daytime and nighttime data, "
          f"the _QCF and _QCF0 variables are identical.")

FLUXVAR2QCF = fpc.filteredseries_level2_qcf.name
FLUXVAR31QCF = fpc.filteredseries_level31_qcf.name
FLUXVAR32QCF = fpc.filteredseries_level32_qcf.name
FLUXVAR32QCF_HQ = f"{FLUXVAR32QCF}0"
FLUXVAR33QCF = fpc.filteredseries_level33_qcf

print("--------------------------")
print("OVERVIEW OF FLUX VARIABLES")
print("--------------------------")
print(
    f""
    f"{FLUXVAR} ... original input flux\n"
    f"{FLUXVAR2QCF} ... flux quality-controlled with Level-2 flags\n    -->  not used in any further processing steps\n"
    f"{FLUXVAR31QCF} ... flux quality-controlled with Level-2 flags, including Level-3.1 storage correction\n   -->  not used in any further processing steps\n"
    f"{FLUXVAR32QCF} ... flux quality-controlled with Level-2 and Level-3.2 flags, including Level-3.1 storage correction)\n    -->  not used in any further processing steps\n"
    f"{FLUXVAR32QCF_HQ} ... highest-quality flux (QCF=0), quality-controlled with Level-2 and Level-3.2 flags, including Level-3.1 storage correction)\n    -->  not used in any further processing steps\n"
)
print("Variables for further steps:")
for key, value in FLUXVAR33QCF.items():
    print(
        f"{FLUXVAR33QCF[key].name} ... flux quality-controlled with Level-2 and Level-3.2 flags, and after Level-3.3 USTAR filtering ({key}), including Level-3.1 storage correction\n-->   to be used in gap-filling and all further steps")

if (DAYTIME_ACCEPT_QCF_BELOW == 1) & (NIGHTTIMETIME_ACCEPT_QCF_BELOW == 1):
    print(f"{'*' * 100}\nNote that since only QCF below 1 is accepted for daytime and nighttime data, "
          f"the _QCF and _QCF0 variables are identical.")

_fluxcols = [x for x in fpc.fpc_df.columns if 'L3.1' and 'L3.3' in x and str(x).endswith('_QCF') and not str(x).startswith('FLAG_')]
fpc.fpc_df[_fluxcols].plot(subplots=True, x_compat=True, title="Available Level-3.3 fluxes after application of all quality checks", figsize=(12, 4.5))
plt.show()

# Draw boxplots
_fluxcols = [x for x in fpc.fpc_df.columns if 'L3.1' and 'L3.3' in x and str(x).endswith('_QCF') and not str(x).startswith('FLAG_')]
for _f in _fluxcols:
    boxplots_df = fpc.fpc_df[[_f, "DAYTIME"]].copy()
    boxplots_df["MONTH"] = boxplots_df.index.month
    # sns.set_theme(style="ticks", palette="pastel")
    plt.figure(figsize=(8, 5), dpi=72)
    sns.boxplot(x="MONTH", y=_f, palette=["r", "b"], hue="DAYTIME", data=boxplots_df).set_title(f"Boxplot of {_f}")
    sns.despine(offset=10, trim=True)
    plt.axhline(0, color="black")
plt.show()

# Creating a dictionary by passing Series objects as values
frame = {
    f'original ({FLUXVAR})': fpc.fpc_df[FLUXVAR],
    f'+ flux quality flags ({FLUXVAR2QCF})': fpc.fpc_df[FLUXVAR2QCF],
    f'++ storage correction ({FLUXVAR31QCF})': fpc.fpc_df[FLUXVAR31QCF],
    f'+++ outlier removal ({FLUXVAR32QCF})': fpc.fpc_df[FLUXVAR32QCF]
}
for key, value in FLUXVAR33QCF.items():
    frame[f'+++ USTAR filtering ({key}, {FLUXVAR33QCF[key].name})'] = FLUXVAR33QCF[key]

overview = pd.DataFrame(frame)
overview.cumsum().plot(title=f"Cumulative", figsize=(14, 7), x_compat=True, alpha=1)
plt.show()

for key, value in fpc.level33_qcf.items():
    fpc.level33_qcf[key].showplot_qcf_heatmaps()



# ----------------------
# LEVEL-4.1
# ----------------------
FEATURES = ["TA_EP", "SW_IN_POT", "VPD_EP"]

# Level-4.1: XGBoost Gap-Filling with Feature Engineering (v0.91.0, optional alternative)
fpc.level41_longterm_xgboost(
    features=FEATURES,
    # Feature Engineering Parameters (same as Random Forest for fair comparison)
    features_lag=[-1, 1],
    features_lag_stepsize=1,
    features_lag_exclude_cols=None,
    features_rolling=[12, 24, 48],
    features_rolling_exclude_cols=None,
    features_rolling_stats=['median', 'min', 'max'],
    features_diff=[1, 2],
    features_diff_exclude_cols=None,
    features_ema=[6, 12, 24],
    features_ema_exclude_cols=None,
    features_poly_degree=2,
    features_poly_exclude_cols=None,
    features_stl=False,
    features_stl_method='stl',
    features_stl_seasonal_period=None,
    features_stl_exclude_cols=None,
    features_stl_components=None,
    vectorize_timestamps=True,
    add_continuous_record_number=True,
    sanitize_timestamp=True,
    # Gap-Filling Parameters
    reduce_features=False,
    verbose=True,
    # XGBoost Hyperparameters
    n_estimators=3000,
    max_depth=6,
    learning_rate=0.5,
    min_child_weight=99,
    early_stopping_rounds=100,
    n_jobs=-1,
    random_state=42,
)
# Access results: fpc.level41['long_term_xgboost']['CUT_50']
results = fpc.get_data(verbose=1)
# Show train/test details
print(fpc.report_traintest_model_scores())
print(fpc.report_traintest_details())
print(fpc.report_gapfilling_model_scores())
fpc.report_gapfilling_poolyears()
fpc.report_gapfilling_feature_importances()
print("Used model, USTAR scenario, non-gapfilled variable and gap-filled variable:")
fpc.report_gapfilling_variables()
gapfilled_names = fpc.get_gapfilled_names()
gapfilled_vars = fpc.get_gapfilled_variables()
nongapfilled_names = fpc.get_nongapfilled_names()

fpc.showplot_gapfilled_heatmap()
fpc.showplot_gapfilled_cumulative(gain=0.02161926, units=r'($\mathrm{gC\ m^{-2}}$)', per_year=True, show_reference=False)
fpc.showplot_gapfilled_cumulative(gain=0.02161926, units=r'($\mathrm{gC\ m^{-2}}$)', per_year=False)
# fpc.showplot_feature_ranks_per_year()
fpc.showplot_mds_gapfilling_qualities()

# Save to files
filename = f"{script_id}_FluxProcessingChain_L4.1_{FLUXVAR}"
save_parquet(data=results, filename=filename, outpath=OUTDIR)
results.to_csv(f"{OUTDIR}/{filename}.csv")
