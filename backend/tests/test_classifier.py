"""Unit tests for the rule-based weak labeller and the trained classifier."""
from app.services.classifier import JobClassifier, rule_label


def test_rule_label_software_engineering():
    assert rule_label("Senior Software Engineer") == "Software Engineering"


def test_rule_label_data_analytics():
    assert rule_label("Lead Data Scientist") == "Data & Analytics"


def test_rule_label_finance():
    assert rule_label("Senior Accountant") == "Finance & Accounting"


def test_rule_label_unknown_defaults_to_other():
    assert rule_label("Zookeeper") == "Other"


def test_trained_model_predicts_known_class():
    clf = JobClassifier()
    if clf.load():  # model artefact present
        category, confidence = clf.predict_proba("Backend Developer")
        assert isinstance(category, str) and category
        assert 0.0 <= confidence <= 1.0
