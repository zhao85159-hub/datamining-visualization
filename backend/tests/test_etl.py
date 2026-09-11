"""Unit tests for the ETL transformation helpers (salary + timestamp logic)."""
from etl.import_data import _annualise, _clean_salary, _to_dt


def test_clean_salary_keeps_plausible_values():
    assert _clean_salary(50000) == 50000


def test_clean_salary_rejects_out_of_band():
    assert _clean_salary(5) is None            # placeholder $5
    assert _clean_salary(10_000_000) is None   # corrupt value


def test_annualise_hourly_to_annual():
    row = {"normalized_salary": None, "pay_period": "HOURLY",
           "med_salary": 50, "max_salary": None, "min_salary": None}
    assert _annualise(row) == 50 * 2080


def test_annualise_prefers_precomputed_normalized():
    row = {"normalized_salary": 120000, "pay_period": "YEARLY"}
    assert _annualise(row) == 120000


def test_annualise_returns_none_without_salary():
    row = {"normalized_salary": None, "pay_period": "YEARLY",
           "med_salary": None, "max_salary": None, "min_salary": None}
    assert _annualise(row) is None


def test_to_dt_parses_epoch_milliseconds():
    dt = _to_dt(1700000000000)
    assert dt is not None and dt.year == 2023


def test_to_dt_handles_missing():
    assert _to_dt(None) is None
