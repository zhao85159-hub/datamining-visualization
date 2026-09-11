"""Unit tests for the skills-extraction NLP module."""
from app.services.nlp import SkillExtractor, default_extractor


def test_extracts_known_skills():
    skills = default_extractor.extract("We need strong Python, SQL and AWS experience")
    assert {"Python", "SQL", "AWS"}.issubset(set(skills))


def test_empty_and_none_inputs():
    assert default_extractor.extract("") == []
    assert default_extractor.extract(None) == []


def test_word_boundary_prevents_false_positive():
    # 'javascript' must map to JavaScript, never to the Java entry.
    skills = default_extractor.extract("experienced javascript engineer")
    assert "JavaScript" in skills
    assert "Java" not in skills


def test_aliases_normalise_to_canonical():
    skills = SkillExtractor().extract("k8s and golang on gcp")
    assert "Kubernetes" in skills
    assert "Go" in skills
    assert "GCP" in skills


def test_extract_counts_aggregates():
    counts = default_extractor.extract_counts([
        "Python role", "Python and SQL role", "SQL analyst",
    ])
    assert counts["Python"] == 2
    assert counts["SQL"] == 2
