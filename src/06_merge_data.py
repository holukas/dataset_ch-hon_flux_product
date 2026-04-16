"""
Merge NEE and LE L4 flux datasets into single output file
"""

from pathlib import Path

from diive.core.io.files import save_parquet, load_parquet

# ============================================================================
# Configuration
# ============================================================================

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent
SOURCEDIR = r"..\data\out"
FILENAME_NEE = "04_FluxProcessingChain_L4.1_FC.parquet"
FILENAME_LE = "05_FluxProcessingChain_L4.1_LE.parquet"

script_id = "06"

# ============================================================================
# Load data
# ============================================================================

filepath_nee = Path(SOURCEDIR) / FILENAME_NEE
filepath_le = Path(SOURCEDIR) / FILENAME_LE

print(f"Loading NEE: {filepath_nee}")
df_nee = load_parquet(filepath=str(filepath_nee))
[print(c) for c in df_nee.columns if "NEE" in c];

print(f"Loading LE: {filepath_le}")
df_le = load_parquet(filepath=str(filepath_le))

# ============================================================================
# Merge on index (datetime): NEE as main, add only new LE columns
# ============================================================================

print(f"\nNEE shape: {df_nee.shape}")
print(f"LE shape: {df_le.shape}")
print(f"NEE columns: {list(df_nee.columns)}")
print(f"LE columns: {list(df_le.columns)}")

# Identify columns in LE that are not in NEE
new_le_cols = [col for col in df_le.columns if col not in df_nee.columns]
print(f"New columns from LE: {new_le_cols}")

# Merge: use NEE as base, add only new LE columns
df_merged = df_nee.copy()
df_merged[new_le_cols] = df_le[new_le_cols]

print(f"\nMerged shape: {df_merged.shape}")
print(f"Merged columns: {list(df_merged.columns)}")

# ============================================================================
# Save merged dataset
# ============================================================================

filepath = save_parquet(filename="06_L4.1_FLUXES_MERGED", data=df_merged, outpath=str(SOURCEDIR))
print(f"\nSaved: {filepath}")

# # Also save as CSV for inspection
# csv_path = Path(filepath).with_suffix('.csv')
# df_merged.to_csv(csv_path)
# print(f"Saved: {csv_path}")
