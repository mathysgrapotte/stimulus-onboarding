import torch
from torch import nn 

def get_activation_function(act_fn: str | nn.Module) -> nn.Module:
    """Handle activation function, converting a string to a nn.Module by lookup in torch.nn."""
    if isinstance(act_fn, str):
        if hasattr(nn, act_fn):
            act_fn_module = getattr(nn, act_fn)()
            # If the module has parameters (like PReLU), this minimal init might not be enough
            # and might need arguments. But standard activations are usually parameterless.
        else:
            logger.warning(f"Activation {act_fn} not found in torch.nn, using SiLU")
            act_fn_module = nn.SiLU()

    return act_fn_module

class Model(PCAReconstructorBase):
    """Unified wrapper for PCA Reconstructor models."""
    
    # Class attributes for hybrid model
    PCA_COMPONENTS: torch.Tensor | None = None
    PCA_MEAN: torch.Tensor | None = None
    
    def __init__(
        self, 
        model_type: str, 
        pca_dim: int, 
        gene_dim: int, 
        act_fn: str | nn.Module = "SiLU",
        **kwargs
    ):
        super().__init__(pca_dim, gene_dim)

        act_fn_module = get_activation_function(act_fn)

        if model_type == "mlp":
            # Filter kwargs for MLP. MLPBlock in this file takes 'act_last_layer' but not used in Unified args
            # Actually MLPPCAReconstructor __init__ takes: pca_dim, gene_dim, hidden_dims, dropout_rate, act_fn
            mlp_kwargs = {k: v for k, v in kwargs.items() if k in ['hidden_dims', 'dropout_rate']}
            
            # Note: hidden_dims might come as string from Optuna if deserialized? No, json loads handles it.
            # But the code provided for MLPPCAReconstructor uses Sequence[int].
            
            self.model = MLPPCAReconstructor(
                pca_dim, gene_dim, 
                act_fn=act_fn_module,
                **mlp_kwargs
            )

        elif model_type == "linear":
            # here implement self.model = LinearPCAReconstructor()
            pass