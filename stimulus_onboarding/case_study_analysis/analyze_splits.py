from pathlib import Path
import anndata
import numpy as np
import textwrap

# Script location: stimulus-onboarding/stimulus_onboarding/case_study_analysis/
# Output location: stimulus-onboarding/output/vcc_split/

base_dir = Path(__file__).parent.parent.parent

train_path = base_dir / "output" / "vcc_split" / "train.h5ad"
val_path = base_dir / "output" / "vcc_split" / "val.h5ad"

def analyze_split(name, path):
    print(f"\n--- Analyzing {name} ---")
    if not path.exists():
        print(f"File not found: {path}")
        print("Please run the stimulus onboarding flow to generate the split data.")
        return

    try:
        adata = anndata.read_h5ad(path)
        print(f"Shape: {adata.shape}")
        
        if "target_gene" in adata.obs:
            unique_targets = sorted(adata.obs["target_gene"].unique())
            print(f"Unique target genes ({len(unique_targets)}):")
            
            # Format as horizontal list
            gene_list_str = ", ".join(unique_targets)
            wrapper = textwrap.TextWrapper(initial_indent="  ", subsequent_indent="  ", width=80)
            print(wrapper.fill(gene_list_str))
        else:
            print("Column 'target_gene' not found in obs.")
            
    except Exception as e:
        print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    analyze_split("Train Split", train_path)
    analyze_split("Validation Split", val_path)
