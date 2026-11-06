"""Conditional log-demand regression with joint empirical residual generation."""
from datetime import date, timedelta
import numpy as np

DISTRICTS = ("HK_Island", "Kowloon", "New_Territories")
SHARES = np.array([.22, .35, .43])


def calendar(start, days, seed):
    if days < 1:
        raise ValueError("days must be positive")
    start = date.fromisoformat(start)
    rng = np.random.default_rng(seed)
    return [{"date": (start + timedelta(days=i)).isoformat(),
             "promotion": int(rng.random() < .12),
             "rain": int(rng.random() < .25),
             "holiday": int(rng.random() < .04)} for i in range(days)]


def features(rows):
    result = []
    for row in rows:
        d = date.fromisoformat(row["date"])
        flags = [int(row[k]) for k in ("promotion", "rain", "holiday")]
        if any(v not in (0, 1) for v in flags):
            raise ValueError("context flags must be 0 or 1")
        result.append([1, *[int(d.weekday() == j) for j in range(1, 7)],
                       *flags, np.sin(2*np.pi*d.timetuple().tm_yday/365.25),
                       np.cos(2*np.pi*d.timetuple().tm_yday/365.25)])
    return np.asarray(result, dtype=float)


def history(start="2024-01-01", days=730, seed=42):
    rows = calendar(start, days, seed)
    rng = np.random.default_rng(seed + 1)
    y = []
    shock = 0.
    for row in rows:
        d = date.fromisoformat(row["date"])
        shock = .45*shock + rng.normal(0, .09)
        mean = 5000 * SHARES * np.exp(.22*row["promotion"] - .08*row["rain"]
               + .12*row["holiday"] + .10*np.sin(2*np.pi*d.timetuple().tm_yday/365.25)
               - .18*(d.weekday() == 6) + shock + rng.normal(0, .05, 3))
        y.append(rng.poisson(mean))
    return rows, np.asarray(y)


class DemandModel:
    def fit(self, rows, y):
        x = features(rows)
        y = np.asarray(y)
        if len(rows) < 28 or y.shape != (len(rows), 3) or not np.isfinite(y).all() or (y < 0).any():
            raise ValueError("need >=28 days of finite nonnegative three-district demand")
        self.beta = np.linalg.solve(x.T@x + .01*np.eye(x.shape[1]), x.T@np.log1p(y))
        self.residuals = np.log1p(y) - x@self.beta
        self.residuals -= self.residuals.mean(axis=0)
        return self

    def predict(self, rows):
        # Empirical smearing estimates the conditional mean on the count scale.
        return np.maximum(0, np.exp(features(rows)@self.beta)
                          * np.exp(self.residuals).mean(axis=0) - 1)

    def sample(self, rows, samples=200, seed=42, multiplier=1., block=7):
        if samples < 1 or block < 1 or not np.isfinite(multiplier) or multiplier <= 0:
            raise ValueError("positive samples, block and finite multiplier required")
        rng = np.random.default_rng(seed)
        n = len(rows)
        # Circular moving blocks retain local serial dependence; vectors retain district dependence.
        starts = rng.integers(len(self.residuals), size=(samples, (n+block-1)//block))
        idx = (starts[..., None] + np.arange(block)) % len(self.residuals)
        noise = self.residuals[idx.reshape(samples, -1)[:, :n]]
        draws = np.expm1(features(rows)@self.beta + noise)
        return np.rint(np.maximum(0, draws)*multiplier).astype(np.int64)

    def save(self, path):
        np.savez_compressed(path, beta=self.beta, residuals=self.residuals)

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path, allow_pickle=False) as data:
            model.beta, model.residuals = data["beta"], data["residuals"]
        return model


def baseline(train_rows, y, future_rows):
    weekdays = np.array([date.fromisoformat(r["date"]).weekday() for r in train_rows])
    return np.array([y[weekdays == date.fromisoformat(r["date"]).weekday()].mean(axis=0)
                     for r in future_rows])


def evaluate(train_rows, y_train, test_rows, y_test, seed=42):
    model = DemandModel().fit(train_rows, y_train)
    draws = model.sample(test_rows, samples=500, seed=seed)
    result = {}
    for name, pred in (("weekday_mean", baseline(train_rows, y_train, test_rows)),
                       ("conditional_mean", model.predict(test_rows))):
        error = np.abs(pred-y_test)
        result[name] = {"mae": float(error.mean()),
                        "rmse": float(np.sqrt(((pred-y_test)**2).mean())),
                        "wape": float(error.sum()/y_test.sum())}
    lo, hi = np.quantile(draws, [.05, .95], axis=0)
    result["generative"] = {
        "coverage_90": float(((y_test >= lo) & (y_test <= hi)).mean()),
        "mean_interval_width": float((hi-lo).mean()),
        "heldout_mean": float(y_test.mean()), "generated_mean": float(draws.mean()),
        "heldout_std": float(y_test.std()), "generated_std": float(draws.std()),
        "district_mean_relative_error": (np.abs(draws.mean(axis=(0,1))-y_test.mean(axis=0))
                                         / y_test.mean(axis=0)).tolist()}
    return model, result
