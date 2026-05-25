import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from solar_model import normalize, gradient_descent, compute_metrics, FEATURE_COLS, TARGET_COL

sns.set_theme(style="whitegrid")

print("Cargando datos limpios...")
df = pd.read_csv('Datasets/189871_Squaw_Valley_2006/merged_clean.csv')
df_day = df[df['is_daytime'] == 1].copy()

y_all = df_day[TARGET_COL].values.astype(float)
split = int(0.8 * len(y_all))
y_train, y_test = y_all[:split], y_all[split:]

# --- MODELO 1: Solo 1 variable (GHI) ---
X_1 = df_day[['GHI']].values.astype(float)
X_train_1, X_test_1 = X_1[:split], X_1[split:]
X_train_norm_1, mean_1, std_1 = normalize(X_train_1)
X_test_norm_1, _, _ = normalize(X_test_1, mean=mean_1, std=std_1)

w_1, b_1, cost_hist_1 = gradient_descent(X_train_norm_1, y_train, np.zeros(1), 0.0, 0.1, 1000)
pred_1 = np.clip(X_test_norm_1 @ w_1 + b_1, 0, None)
metrics_1 = compute_metrics(y_test, pred_1)

# --- MODELO 2: Todas las variables (7 Features) ---
X_7 = df_day[FEATURE_COLS].values.astype(float)
X_train_7, X_test_7 = X_7[:split], X_7[split:]
X_train_norm_7, mean_7, std_7 = normalize(X_train_7)
X_test_norm_7, _, _ = normalize(X_test_7, mean=mean_7, std=std_7)

w_7, b_7, cost_hist_7 = gradient_descent(X_train_norm_7, y_train, np.zeros(7), 0.0, 0.1, 1000)
pred_7 = np.clip(X_test_norm_7 @ w_7 + b_7, 0, None)
metrics_7 = compute_metrics(y_test, pred_7)

# ==========================================================
# GRÁFICAS DEL PROFESOR
# ==========================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gráfica A: Comparación de R2 (Modelos diferentes)
models = ['Modelo Básico\n(Solo Sol/GHI)', 'Modelo Completo\n(7 Variables)']
r2_scores = [metrics_1['R2']*100, metrics_7['R2']*100]

sns.barplot(x=models, y=r2_scores, ax=axes[0], palette='Blues')
axes[0].set_title('Justificación de Variables: Precisión del Modelo (R²)', fontweight='bold')
axes[0].set_ylabel('Precisión (%)')
axes[0].set_ylim(0, 100)
for i, v in enumerate(r2_scores):
    axes[0].text(i, v + 2, f"{v:.1f}%", ha='center', fontweight='bold', fontsize=12)

# Gráfica B: Predicción vs Realidad (Test Set)
axes[1].scatter(y_test, pred_7, alpha=0.3, color='dodgerblue', s=10)
axes[1].plot([0, y_test.max()], [0, y_test.max()], 'k--', linewidth=2) # Diagonal perfecta
axes[1].set_title('Modelo Final: Predicción vs Realidad', fontweight='bold')
axes[1].set_xlabel('Generación Real (MW)')
axes[1].set_ylabel('Generación Predicha por ML (MW)')

plt.tight_layout()
plt.savefig('4_ml_model_comparison.png', dpi=150)
print("¡Éxito! Gráfica '4_ml_model_comparison.png' guardada.")