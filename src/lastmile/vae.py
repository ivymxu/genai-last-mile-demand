"""Optional CPU conditional VAE for joint daily district log counts."""
import numpy as np
import torch
from torch import nn
from .model import features, DemandModel


class Network(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(15, 32), nn.Tanh())
        self.mu = nn.Linear(32, 4)
        self.logvar = nn.Linear(32, 4)
        self.decoder = nn.Sequential(nn.Linear(16, 32), nn.Tanh(), nn.Linear(32, 6))

    def decode(self, z, context):
        mean, logscale = self.decoder(torch.cat([z, context], -1)).chunk(2, -1)
        return mean, logscale.clamp(-4, 2)


class ConditionalVAE:
    def fit(self, rows, y, epochs=150, seed=42):
        # Reuse the statistical model's shape/count checks; no holdout statistics.
        DemandModel().fit(rows, y)
        if epochs < 1 or seed < 0:
            raise ValueError("positive epochs and nonnegative seed required")
        torch.set_num_threads(1)
        with torch.random.fork_rng():
            torch.manual_seed(seed)
            self.net = Network()
            values = np.log1p(y)
            self.center = values.mean(0)
            self.scale = np.maximum(values.std(0), .01)
            target = torch.tensor((values-self.center)/self.scale, dtype=torch.float32)
            context = torch.tensor(features(rows), dtype=torch.float32)
            optimizer = torch.optim.Adam(self.net.parameters(), lr=.01)
            self.losses = []
            for _ in range(epochs):
                hidden = self.net.encoder(torch.cat([target, context], -1))
                mu = self.net.mu(hidden)
                logvar = self.net.logvar(hidden).clamp(-8, 8)
                z = mu + torch.exp(.5*logvar)*torch.randn_like(mu)
                mean, logscale = self.net.decode(z, context)
                nll = (.5*((target-mean)*torch.exp(-logscale))**2 + logscale).sum(-1).mean()
                kl = -.5*(1+logvar-mu.square()-logvar.exp()).sum(-1).mean()
                loss = nll + kl
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite VAE training loss")
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                self.losses.append(float(loss.detach()))
        self.net.eval()
        return self

    def sample(self, rows, samples=200, seed=42, multiplier=1.):
        if samples < 1 or seed < 0 or not np.isfinite(multiplier) or multiplier <= 0:
            raise ValueError("positive samples/multiplier and nonnegative seed required")
        generator = torch.Generator().manual_seed(seed)
        context = torch.tensor(features(rows), dtype=torch.float32).repeat(samples, 1)
        with torch.no_grad():
            z = torch.randn((samples*len(rows), 4), generator=generator)
            mean, logscale = self.net.decode(z, context)
            noise = torch.randn(mean.shape, generator=generator)
            logcounts = (mean + logscale.exp()*noise).numpy()*self.scale + self.center
        # Bound numerical tails; this is a pragmatic safeguard, not tail calibration.
        counts = np.maximum(0, np.expm1(np.clip(logcounts, -20, 20)))*multiplier
        if counts.max(initial=0) > np.iinfo(np.int64).max:
            raise ValueError("multiplier exceeds count range")
        return np.rint(counts).astype(np.int64).reshape(samples, len(rows), 3)

    def save(self, path):
        arrays = {f"weight_{k}": v.detach().numpy() for k, v in self.net.state_dict().items()}
        np.savez_compressed(path, center=self.center, scale=self.scale, losses=self.losses, **arrays)

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path, allow_pickle=False) as data:
            model.center, model.scale = data['center'], data['scale']
            model.losses = data['losses'].tolist()
            with torch.random.fork_rng():
                model.net = Network()
            model.net.load_state_dict({k: torch.tensor(data[f'weight_{k}']) for k in model.net.state_dict()})
        model.net.eval()
        return model
