from pathlib import Path
from anndata import AnnData as ad 
import anndata

# Use relative path from this script to find the data
# Script is in stimulus_onboarding/case_study_analysis/
# Data is in data/
data_path = Path(__file__).parent.parent.parent / "data" / "vcc_training_subset.h5ad"

anndataset = anndata.read_h5ad(data_path)
print(anndataset)