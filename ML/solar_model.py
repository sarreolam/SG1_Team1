"""
solar_model.py
--------------
Multivariate Linear Regression with Gradient Descent — from scratch.
No scikit-learn or ML libraries used.

Predicts solar power output (MW) from weather features for Squaw Valley.
Saves the trained weights to model_weights.json so the simulator can
load them without retraining every run.

Usage:
    python solar_model.py           # train and save
    python solar_model.py --eval    # train and show sample predictions
"""

import numpy as np
import pandas as pd
import json, os, copy, math, sys

# ── City config ───────────────────────────────────────────────────────────────
CITY_CONFIG = {
    'Squaw_Valley': {'prefix': '189871', 'farm_mw': 112.9}
}

DEFAULT_CITY = 'Squaw_Valley'

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
DATASETS_DIR = os.path.join(PROJECT_ROOT, 'Datasets')
MODEL_PATH   = os.path.join(SCRIPT_DIR, 'model_weights.json')

# ── Features ─────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    'GHI',                # Global Horizontal Irradiance      r=0.95
    'Clearsky GHI',       # Max theoretical GHI               r=0.92
    'Solar Zenith Angle', # Sun angle (lower = more direct)   r=-0.80
    'Temperature',        # High temp reduces efficiency       r=0.50
    'Relative Humidity',  # Moisture reduces transmission      r=-0.63
    'clearsky_ratio',     # GHI/ClearskyGHI — cloud proxy
    'hour',               # Time of day
]
TARGET_COL = 'power_mw'


# ── Core math functions ───────────────────────────────────────────────────────

def normalize(X, mean=None, std=None):
    if mean is None: mean = X.mean(axis=0)
    if std  is None:
        std = X.std(axis=0)
        std[std == 0] = 1.0
    return (X - mean) / std, mean, std


def compute_cost(X, y, w, b):
    m = X.shape[0]
    errors = X @ w + b - y
    return (1 / (2 * m)) * np.sum(errors ** 2)


def compute_gradient(X, y, w, b):
    m = X.shape[0]
    errors = X @ w + b - y
    return (1 / m) * (X.T @ errors), (1 / m) * np.sum(errors)


def gradient_descent(X, y, w_init, b_init, alpha, num_iters):
    w, b = copy.deepcopy(w_init), b_init
    J_history = []
    for i in range(num_iters):
        dj_dw, dj_db = compute_gradient(X, y, w, b)
        w -= alpha * dj_dw
        b -= alpha * dj_db
        if i < 100_000:
            J_history.append(compute_cost(X, y, w, b))
        if i % math.ceil(num_iters / 10) == 0:
            print(f"  Iter {i:6d}: cost = {J_history[-1]:.6f}")
    return w, b, J_history


def compute_metrics(y_true, y_pred):
    errors = y_pred - y_true
    mse  = np.mean(errors ** 2)
    rmse = np.sqrt(mse)
    mae  = np.mean(np.abs(errors))
    r2   = 1 - np.sum(errors**2) / np.sum((y_true - y_true.mean())**2)
    return {'MSE': mse, 'RMSE': rmse, 'MAE': mae, 'R2': r2}


# ── SolarModel class ─────────────────────────────────────────────────────────

class SolarModel:
    """
    Trained linear regression model for solar power prediction.
    Used by components_ml.py inside the simulator.
    """
    def __init__(self):
        self.w = self.b = self.mean = self.std = None
        self.features = FEATURE_COLS
        self.trained  = False

    def predict(self, features: dict) -> float:
        """
        Predict solar power in MW from a dict of weather features.
        Returns a non-negative float.
        """
        if not self.trained:
            raise RuntimeError("Model not trained. Call train() or load() first.")
        x_raw  = np.array([features[col] for col in self.features], dtype=float)
        x_norm = (x_raw - self.mean) / self.std
        return max(0.0, float(np.dot(self.w, x_norm) + self.b))

    def save(self, path=MODEL_PATH):
        with open(path, 'w') as f:
            json.dump({'w': self.w.tolist(), 'b': float(self.b),
                       'mean': self.mean.tolist(), 'std': self.std.tolist(),
                       'features': self.features}, f, indent=2)
        print(f"Model saved: {path}")

    def load(self, path=MODEL_PATH):
        with open(path) as f:
            p = json.load(f)
        self.w, self.b  = np.array(p['w']), p['b']
        self.mean, self.std = np.array(p['mean']), np.array(p['std'])
        self.features   = p['features']
        self.trained    = True
        return self


# ── Training ─────────────────────────────────────────────────────────────────

def train(city_name=DEFAULT_CITY, show_eval=False):
    print("=" * 58)
    print(f"  GREEN GRID ML — Training on {city_name}")
    print("=" * 58)

    # Find city folder
    city_folder = next(
        (d for d in os.listdir(DATASETS_DIR)
         if city_name.split('_')[0] in d or CITY_CONFIG[city_name]['prefix'] in d),
        None
    )
    if city_folder is None:
        raise FileNotFoundError(f"Folder for '{city_name}' not found in {DATASETS_DIR}")

    data_path = os.path.join(DATASETS_DIR, city_folder, 'merged_clean.csv')
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"merged_clean.csv not found. Run prepare_ml_data.py --city {city_name} first."
        )

    df = pd.read_csv(data_path)
    print(f"  Loaded {len(df):,} rows")

    # Daytime only
    df_day = df[df['is_daytime'] == 1].copy()
    print(f"  Daytime rows: {len(df_day):,}")

    X_all = df_day[FEATURE_COLS].values.astype(float)
    y_all = df_day[TARGET_COL].values.astype(float)

    # Time-based split (no data leakage)
    split = int(0.8 * len(X_all))
    X_train, X_test = X_all[:split], X_all[split:]
    y_train, y_test = y_all[:split], y_all[split:]
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    X_train_norm, x_mean, x_std = normalize(X_train)
    X_test_norm, _, _           = normalize(X_test, mean=x_mean, std=x_std)

    alpha, num_iters = 0.1, 3_000
    print(f"\nGradient Descent (alpha={alpha}, iters={num_iters})...")
    w, b, J_hist = gradient_descent(
        X_train_norm, y_train, np.zeros(X_train_norm.shape[1]), 0.0,
        alpha, num_iters
    )

    # Metrics
    for label, X_n, y_true in [('Train', X_train_norm, y_train),
                                ('Test ', X_test_norm,  y_test)]:
        pred = np.clip(X_n @ w + b, 0, None)
        m    = compute_metrics(y_true, pred)
        print(f"\n--- {label} Metrics ---")
        for k, v in m.items():
            print(f"  {k}: {v:.4f}")

    print("\n--- Feature Weights (normalized) ---")
    for fname, wi in zip(FEATURE_COLS, w):
        print(f"  {fname:25s}: {wi:+.4f}")
    print(f"  {'bias (b)':25s}: {b:+.4f}")

    model = SolarModel()
    model.w, model.b, model.mean, model.std = w, b, x_mean, x_std
    model.trained = True
    model.save()

    if show_eval:
        print("\n--- Sample Predictions ---")
        print(f"{'GHI':>6} {'Temp':>6} {'Zenith':>7} | {'Actual':>8} {'Pred':>8} {'Err':>8}")
        print("-" * 50)
        for _, row in df_day.sample(10, random_state=42).sort_values('GHI').iterrows():
            feat = {c: row[c] for c in FEATURE_COLS}
            pred = model.predict(feat)
            print(f"{row['GHI']:6.0f} {row['Temperature']:6.1f} {row['Solar Zenith Angle']:7.1f}"
                  f" | {row[TARGET_COL]:8.3f} {pred:8.3f} {pred-row[TARGET_COL]:+8.3f}")

    return model


if __name__ == '__main__':
    train(DEFAULT_CITY, show_eval='--eval' in sys.argv)