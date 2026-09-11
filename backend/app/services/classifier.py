"""Job classification / tagging module.

A two-stage approach is used:

1. **Weak labelling** - a transparent keyword taxonomy assigns an initial
   category to each posting from its title (and description as a fallback).
2. **Supervised model** - a TF-IDF + Logistic Regression pipeline is trained on
   the weak labels so the classifier generalises to titles the keyword rules do
   not cover and produces a probability/confidence per prediction.

The trained model is persisted with ``pickle`` and loaded lazily at runtime.
"""
from __future__ import annotations

import os
import pickle
import re

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Software Engineering": [
        "software engineer", "developer", "programmer", "full stack",
        "backend", "front end", "frontend", "web developer", "sde",
        "devops", "site reliability", "mobile developer", "ios", "android",
    ],
    "Data & Analytics": [
        "data scientist", "data analyst", "data engineer", "machine learning",
        "analytics", "business intelligence", "bi developer", "statistician",
        "data architect",
    ],
    "IT & Infrastructure": [
        "system administrator", "network", "it support", "help desk",
        "cloud engineer", "database administrator", "dba", "security analyst",
        "cybersecurity", "infrastructure",
    ],
    "Design": [
        "designer", "ux", "ui", "graphic", "creative", "art director",
        "product designer",
    ],
    "Product & Project Management": [
        "product manager", "project manager", "scrum master", "program manager",
        "product owner",
    ],
    "Marketing": [
        "marketing", "seo", "content", "social media", "brand", "communications",
        "copywriter", "growth",
    ],
    "Sales & Business": [
        "sales", "account executive", "business development", "account manager",
        "customer success",
    ],
    "Finance & Accounting": [
        "accountant", "financial", "finance", "auditor", "bookkeeper",
        "controller", "analyst", "investment",
    ],
    "Human Resources": [
        "human resources", "recruiter", "talent", "hr ", "people operations",
    ],
    "Healthcare": [
        "nurse", "physician", "medical", "clinical", "healthcare", "therapist",
        "pharmacist", "dental",
    ],
    "Education": [
        "teacher", "professor", "instructor", "tutor", "lecturer", "education",
    ],
    "Operations & Logistics": [
        "operations", "supply chain", "logistics", "warehouse", "driver",
        "manufacturing", "production",
    ],
    "Customer Service": [
        "customer service", "customer support", "call center", "client service",
    ],
}

_DEFAULT_CATEGORY = "Other"

# Pre-compile one alternation pattern per category. Word boundaries prevent
# short tokens such as "ui"/"ux"/"hr" from matching inside unrelated words
# (e.g. "b*ui*lding", "rec*r*uiter").
_CATEGORY_PATTERNS = {
    cat: re.compile("|".join(r"\b" + re.escape(kw.strip()) + r"\b" for kw in kws))
    for cat, kws in CATEGORY_KEYWORDS.items()
}


def rule_label(title: str | None, description: str | None = None) -> str:
    text = ((title or "") + " " + (description or "")[:200]).lower()
    best, best_score = _DEFAULT_CATEGORY, 0
    for category, pattern in _CATEGORY_PATTERNS.items():
        score = len(pattern.findall(text))
        if score > best_score:
            best, best_score = category, score
    return best


class JobClassifier:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "processed", "job_classifier.pkl",
        )
        self._pipeline = None

    # -- training -----------------------------------------------------------
    def train(self, titles, descriptions=None):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        descriptions = descriptions or [""] * len(titles) # fallback to empty strings if no descriptions provided
        labels = [rule_label(t, d) for t, d in zip(titles, descriptions)] # generate weak labels via keyword rules
        corpus = [self._clean(t) for t in titles]

        pipeline = Pipeline([       # chain feature extraction + classifier
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000)),# text -> TF-IDF vectors
            ("clf", LogisticRegression(max_iter=1000, C=4.0, class_weight="balanced")), # multi-class logistic regre
        ])
        pipeline.fit(corpus, labels)  # train the model on cleaned text + weak labels
        self._pipeline = pipeline # store trained pipeline for later prediction
        return self

    def save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self._pipeline, f)

    def load(self) -> bool:
        if self._pipeline is not None:
            return True
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self._pipeline = pickle.load(f)
            return True
        return False

    # -- inference ----------------------------------------------------------
    def predict(self, title: str | None, description: str | None = None) -> str:
        if self.load():
            try:
                return str(self._pipeline.predict([self._clean(title or "")])[0])
            except Exception:
                pass
        return rule_label(title, description)

    def predict_proba(self, title: str | None) -> tuple[str, float]:
        if self.load():
            import numpy as np
            probs = self._pipeline.predict_proba([self._clean(title or "")])[0]
            idx = int(np.argmax(probs))
            return str(self._pipeline.classes_[idx]), float(probs[idx])
        return rule_label(title), 0.0

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"[^a-zA-Z ]", " ", (text or "").lower()).strip()


default_classifier = JobClassifier()
