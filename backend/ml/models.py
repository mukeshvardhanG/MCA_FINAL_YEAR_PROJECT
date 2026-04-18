"""
ML Models — BPNN (PyTorch) + Random Forest + XGBoost
Weighted ensemble prediction + Permutation Feature Importance
"""
import torch
import torch.nn as nn
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
import joblib
import json
import os


class BPNN(nn.Module):
    """Backpropagation Neural Network — 3-layer feedforward.

    Architecture notes:
      - BatchNorm BEFORE activation (standard ResNet convention, avoids
        BatchNorm+Dropout anti-pattern when Dropout comes after activation).
      - Dropout only on the two wider layers; final projection layer is clean.
      - Reduced dropout rate (0.1) since the dataset is small enough that
        heavier regularisation hurts convergence speed.
    """

    def __init__(self, input_dim: int = 21):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.1),          # FIX: lighter dropout
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.1),          # FIX: lighter dropout, only 2 layers
            nn.Linear(128, 64),
            nn.ReLU(),                # FIX: no BN+Dropout on final hidden layer
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


class MLEngine:
    """Manages training, inference, and PFI for the 3-model ensemble."""

    def __init__(self, model_dir: str = "models/"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.bpnn: BPNN = None
        self.rf: RandomForestRegressor = None
        self.xgb: XGBRegressor = None
        self.weights = {"bpnn": 0.40, "rf": 0.30, "xgb": 0.30}
        self.feature_names: list = []

    def train(self, X_train, y_train, X_val, y_val, feature_names: list):
        self.feature_names = feature_names
        input_dim = X_train.shape[1]

        # ── BPNN Training ──
        print("Training BPNN...")
        self.bpnn = BPNN(input_dim)

        # FIX: faster initial LR; scheduler will decay if plateau is hit
        optimizer = torch.optim.Adam(self.bpnn.parameters(), lr=0.001, weight_decay=1e-4)
        # FIX: reduce LR by 0.5 after 10 epochs without val improvement
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10
        )
        criterion = nn.MSELoss()

        X_t = torch.FloatTensor(X_train)
        y_t = torch.FloatTensor(y_train)
        X_v = torch.FloatTensor(X_val)
        y_v = torch.FloatTensor(y_val)

        # FIX: mini-batch training — weights update many times per epoch
        batch_size = 256
        n_samples  = X_t.shape[0]

        best_val_loss = float("inf")
        # FIX: patience 10 → 30 so the network gets enough time to converge
        patience, wait = 30, 0

        for epoch in range(500):          # FIX: allow up to 500 epochs
            self.bpnn.train()
            # Shuffle indices each epoch
            perm = torch.randperm(n_samples)
            epoch_loss = 0.0
            for start in range(0, n_samples, batch_size):
                idx = perm[start: start + batch_size]
                optimizer.zero_grad()
                pred = self.bpnn(X_t[idx])
                loss = criterion(pred, y_t[idx])
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * len(idx)

            self.bpnn.eval()
            with torch.no_grad():
                val_loss = criterion(self.bpnn(X_v), y_v).item()

            scheduler.step(val_loss)      # FIX: adaptive LR decay

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(self.bpnn.state_dict(), os.path.join(self.model_dir, "bpnn.pt"))
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    print(f"  BPNN early stop at epoch {epoch + 1}")
                    break

            if (epoch + 1) % 50 == 0:
                lr_now = optimizer.param_groups[0]['lr']
                print(f"  Epoch {epoch+1:>3d} | val_loss={val_loss:.4f} | lr={lr_now:.6f}")

        # Reload best weights
        self.bpnn.load_state_dict(
            torch.load(os.path.join(self.model_dir, "bpnn.pt"), map_location="cpu", weights_only=True)
        )
        print(f"  BPNN best val loss: {best_val_loss:.4f}")

        # ── Random Forest ──
        print("Training Random Forest...")
        self.rf = RandomForestRegressor(
            n_estimators=300, min_samples_split=4, random_state=42, n_jobs=-1
        )
        self.rf.fit(X_train, y_train)
        joblib.dump(self.rf, os.path.join(self.model_dir, "rf.pkl"))

        # ── XGBoost ──
        print("Training XGBoost...")
        self.xgb = XGBRegressor(
            n_estimators=800, learning_rate=0.02, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, random_state=42,
        )
        self.xgb.fit(X_train, y_train)
        self.xgb.save_model(os.path.join(self.model_dir, "xgb.json"))

        # ── Compute ensemble weights from MAE ──
        self._recompute_weights(X_val, y_val)

        # ── Save metadata ──
        with open(os.path.join(self.model_dir, "weights.json"), "w") as f:
            json.dump(self.weights, f, indent=2)
        with open(os.path.join(self.model_dir, "feature_names.json"), "w") as f:
            json.dump(feature_names, f, indent=2)

        print(f"  Ensemble weights: {self.weights}")
        print(f"  Feature names saved ({len(feature_names)} features)")

    def _recompute_weights(self, X_val, y_val):
        self.bpnn.eval()
        with torch.no_grad():
            p_bpnn = self.bpnn(torch.FloatTensor(X_val)).numpy()
        p_rf = self.rf.predict(X_val)
        p_xgb = self.xgb.predict(X_val)

        err_bpnn = mean_absolute_error(y_val, p_bpnn)
        err_rf = mean_absolute_error(y_val, p_rf)
        err_xgb = mean_absolute_error(y_val, p_xgb)

        print(f"  MAE — BPNN: {err_bpnn:.4f}, RF: {err_rf:.4f}, XGB: {err_xgb:.4f}")

        maes = np.array([err_bpnn, err_rf, err_xgb])
        weights = np.exp(-maes) / np.sum(np.exp(-maes))
        self.weights = {
            "bpnn": round(weights[0], 3),
            "rf": round(weights[1], 3),
            "xgb": round(weights[2], 3),
        }

    def load(self):
        with open(os.path.join(self.model_dir, "feature_names.json")) as f:
            self.feature_names = json.load(f)
        with open(os.path.join(self.model_dir, "weights.json")) as f:
            self.weights = json.load(f)

        input_dim = len(self.feature_names)
        self.bpnn = BPNN(input_dim)
        self.bpnn.load_state_dict(
            torch.load(os.path.join(self.model_dir, "bpnn.pt"), map_location="cpu", weights_only=True)
        )
        self.bpnn.eval()

        self.rf = joblib.load(os.path.join(self.model_dir, "rf.pkl"))

        self.xgb = XGBRegressor()
        self.xgb.load_model(os.path.join(self.model_dir, "xgb.json"))

    def predict(self, X: np.ndarray) -> dict:
        self.bpnn.eval()
        with torch.no_grad():
            s_bpnn = float(self.bpnn(torch.FloatTensor(X)).numpy()[0])
        s_rf = float(self.rf.predict(X)[0])
        s_xgb = float(self.xgb.predict(X)[0])

        final = (
            self.weights["bpnn"] * s_bpnn
            + self.weights["rf"] * s_rf
            + self.weights["xgb"] * s_xgb
        )
        final = round(max(0.0, min(100.0, final)), 2)
        grade = "A" if final >= 85 else "B" if final >= 70 else "C" if final >= 55 else "D"

        agreement = np.std([s_bpnn, s_rf, s_xgb])
        
        return {
            "bpnn_score": round(s_bpnn, 2),
            "rf_score": round(s_rf, 2),
            "xgb_score": round(s_xgb, 2),
            "final_score": final,
            "performance_grade": grade,
            "agreement_score": round(float(agreement), 4)
        }

    def compute_pfi(self, X_test: np.ndarray, y_test: np.ndarray) -> list:
        """Compute PFI averaged across RF + XGBoost over multiple runs."""
        results_list = {feat: [] for feat in self.feature_names}

        for i in range(5):
            for name, model in [("rf", self.rf), ("xgb", self.xgb)]:
                pfi = permutation_importance(
                    model, X_test, y_test,
                    n_repeats=5, random_state=42 + i,
                    scoring="neg_mean_absolute_error",
                )
                for j, feat in enumerate(self.feature_names):
                    results_list[feat].append(pfi.importances_mean[j])

        # Average, std, and rank
        ranked = []
        for feat, scores in results_list.items():
            ranked.append({
                "feature_name": feat,
                "importance_score": round(float(np.mean(scores)), 4),
                "importance_std": round(float(np.std(scores)), 4)
            })
            
        ranked = sorted(ranked, key=lambda x: x["importance_score"], reverse=True)
        for i, item in enumerate(ranked):
            item["rank"] = i + 1
        return ranked
