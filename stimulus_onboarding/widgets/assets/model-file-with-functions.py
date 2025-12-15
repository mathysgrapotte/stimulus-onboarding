import torch
from torch import nn 
from typing import Any

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
        # our previous __init__ implementation 

        pass

    def train_batch(
        self,
        batch: dict[str, torch.Tensor],
        optimizer: torch.optim.Optimizer,
        writer: Any,
        global_step: int,
    ) -> tuple[float, dict]:
        
        pca_scores = batch['X_avg_pca']
        raw_counts = batch['X']
        mse_loss = nn.MSELoss()(self.model(pca_scores), raw_counts)

        if writer is not None:
            writer.log_scalar('Train/MSE_Loss', mse_loss.item(), global_step)

            # Compute gradient norm
            grad_norm = torch.norm(
                torch.stack([p.grad.detach().data.norm(2) for p in self.parameters() if p.grad is not None]),
                2
            ).item()
            writer.log_scalar('Gradients/Total_Norm', grad_norm, global_step)

        metrics = {mse_loss: mse_loss.item()}

        return mse_loss.item(), metrics
        

    @torch.inference_mode()
    def inference(
        self,
        batch: dict[str, torch.Tensor],
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        
        # Implementation of a single inference step
        pass

    def validate(
        self,
        data_loader: torch.utils.data.DataLoader
    ) -> dict[str, float]:
        
        metrics = {'loss' : 0.0, 'differential_expression_accuracy' : 0.0, 'correlation' : 0.0}
        return metrics