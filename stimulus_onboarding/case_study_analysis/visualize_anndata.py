from pathlib import Path
import anndata


def main():
    """Visualize the AnnData file."""
    data_path = Path.cwd() / "data" / "vcc_training_subset.h5ad"
    anndataset = anndata.read_h5ad(data_path)
    print(anndataset)


if __name__ == "__main__":
    main()