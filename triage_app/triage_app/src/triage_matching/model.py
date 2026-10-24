"""Pipeline definition + loading. The .pkl files hold ONLY these sklearn pipelines."""
import json
from functools import lru_cache

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from . import config

TOKEN_PATTERN = r"[^\s\.,!?;:()\"'।]+"   # Devanagari-safe (default \w\w+ splits on matras)


def make_pipeline(C: float = 10.0) -> Pipeline:
    """TF-IDF (word 1-2gram + char_wb 2-5gram) -> Logistic Regression. Built-in sklearn objects only,
    so the pickle loads anywhere with the same sklearn version (no custom classes/lambdas)."""
    feats = FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", token_pattern=TOKEN_PATTERN, ngram_range=(1, 2),
                                 lowercase=True, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=True, sublinear_tf=True)),
    ])
    clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced", random_state=config.SEED)
    return Pipeline([("tfidf", feats), ("clf", clf)])


def artifacts_ready() -> bool:
    """True only if all artifacts exist AND were trained with the running sklearn version."""
    if not all(p.exists() for p in (config.CARE_PIPE_PATH, config.URG_PIPE_PATH, config.META_PATH)):
        return False
    meta = json.loads(config.META_PATH.read_text(encoding="utf-8"))
    return meta.get("sklearn_version") == sklearn.__version__


@lru_cache(maxsize=1)
def load_models():
    """Load pickles; if missing or sklearn-version mismatch, retrain automatically (deploy-safe)."""
    if not artifacts_ready():
        from .train import train_and_save
        train_and_save(verbose=False)
    care = joblib.load(config.CARE_PIPE_PATH)
    urg = joblib.load(config.URG_PIPE_PATH)
    meta = json.loads(config.META_PATH.read_text(encoding="utf-8"))
    return care, urg, meta
