# Merge flux files to parquet

import pandas as pd
from diive.core.io.filereader import search_files, MultiDataFileReader
from diive.core.io.files import save_parquet

pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)

script_id = "01"

# Folders
INDIR = r"..\data\OPENLAG-IRGA-Level-0_fluxnet_2024-2026.03"
OUTDIR = r"..\data\out"

# Search original files and store filepaths in list
sourcefiles = search_files(searchdirs=INDIR, pattern='*')

# Read data from precip files to dataframe
d = MultiDataFileReader(filepaths=sourcefiles,
                        filetype='EDDYPRO-FLUXNET-CSV-30MIN',
                        output_middle_timestamp=True)
df = d.data_df

# Save to files
filepath = save_parquet(filename="FLUXES_L0_ALL", data=df, outpath=OUTDIR)
df.to_csv(f"{OUTDIR}/FLUXES_L0_ALL.csv")
