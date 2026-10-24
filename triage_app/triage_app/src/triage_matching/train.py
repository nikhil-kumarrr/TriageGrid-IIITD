"""Train the triage models and write the .pkl artifacts.

    python -m triage_matching.train            # from repo root with PYTHONPATH=src  (or: make train)
"""
import argparse
import json
from datetime import datetime, timezone

import joblib
import matplotlib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402
from .model import make_pipeline  # noqa: E402

C_GRID = [0.3, 1, 3, 10, 30, 100]


def load_training_frame(path=None) -> pd.DataFrame:
    df = pd.read_csv(path or config.TRIAGE_CSV)
    df["text"] = df.user_input.astype(str).str.strip()
    df["y_care"] = df.care_type.fillna(config.NEEDS_CLARIFICATION)
    df["y_urg"] = df.urgency.fillna(config.NEEDS_CLARIFICATION)
    df["group"] = df.text.str.lower()      # same sentence => same fold (prevents leakage)
    return df


def train_and_save(data_path=None, verbose: bool = True) -> dict:
    log = print if verbose else (lambda *a, **k: None)
    df = load_training_frame(data_path)
    X, y, y_u, g = (df[c].to_numpy(dtype=object) for c in ("text", "y_care", "y_urg", "group"))
    cv = StratifiedGroupKFold(5, shuffle=True, random_state=config.SEED)
    classes = np.array(sorted(set(y)))

    log(f"rows={len(df)} unique_texts={df.group.nunique()} classes={[str(c) for c in classes]}")

    # 1) choose C by group-wise CV macro-F1
    rows = []
    for C in C_GRID:
        p = cross_val_predict(make_pipeline(C), X, y, cv=cv, groups=g)
        rows.append({"C": C, "accuracy": accuracy_score(y, p), "macro_f1": f1_score(y, p, average="macro")})
    tune = pd.DataFrame(rows)
    best_c = float(tune.sort_values(["macro_f1", "C"], ascending=[False, True]).iloc[0].C)
    log(tune.round(3).to_string(index=False), f"\nbest C = {best_c}")

    # 2) out-of-fold probabilities -> report, confusion matrix, confidence threshold
    proba = cross_val_predict(make_pipeline(best_c), X, y, cv=cv, groups=g, method="predict_proba")
    pred = classes[proba.argmax(1)]
    report = classification_report(y, pred, output_dict=True, zero_division=0)
    maxp, correct = proba.max(1), pred == y
    threshold = 0.45
    for th in np.arange(0.30, 0.81, 0.05):
        m = maxp >= th
        if m.any() and correct[m].mean() >= 0.95:
            threshold = round(float(th), 2); break

    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay(confusion_matrix(y, pred, labels=classes), display_labels=classes).plot(
        ax=ax, xticks_rotation=35, colorbar=False, cmap="Blues")
    ax.set_title("care_type - out-of-fold (group-wise CV)")
    config.ART_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(config.CM_PATH, dpi=130); plt.close(fig)

    # 3) final fit on all data + save pickles
    care = make_pipeline(best_c).fit(X, y)
    urg = make_pipeline(best_c).fit(X, y_u)
    joblib.dump(care, config.CARE_PIPE_PATH, compress=3)
    joblib.dump(urg, config.URG_PIPE_PATH, compress=3)

    meta = {
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "best_C": best_c, "conf_threshold": threshold,
        "n_rows": int(len(df)), "n_unique_texts": int(df.group.nunique()),
        "care_type_classes": list(care.classes_), "urgency_classes": list(urg.classes_),
        "cv_group_accuracy": round(float(accuracy_score(y, pred)), 4),
        "cv_group_macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
        "cv_per_class": {k: {m: round(v, 3) for m, v in d.items()} for k, d in report.items()
                         if isinstance(d, dict)},
        "c_search": tune.round(4).to_dict("records"),
        "note": "Pickles are sklearn-version specific; app auto-retrains on version mismatch.",
    }
    config.META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"saved -> {config.CARE_PIPE_PATH.name}, {config.URG_PIPE_PATH.name}, {config.META_PATH.name} "
        f"| CV acc={meta['cv_group_accuracy']} macroF1={meta['cv_group_macro_f1']} thr={threshold}")
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description="Train triage models and save .pkl artifacts")
    ap.add_argument("--data", default=None, help="path to triage csv (default: data/triage_dataset_flat.csv)")
    args = ap.parse_args(argv)
    train_and_save(args.data)


if __name__ == "__main__":
    main()
