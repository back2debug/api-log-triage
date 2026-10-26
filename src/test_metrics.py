from normalize import to_float, to_int, to_str, parse_ts
from metrics import safe_div, percentile, is_success


def test_to_float_basic():
    assert to_float("640") == 640.0
    assert to_float(640) == 640.0
    assert to_float("1,234.5") == 1234.5


def test_to_float_blanks():
    assert to_float("n/a") is None
    assert to_float("") is None
    assert to_float(None) is None
    assert to_float(None, default=0.0) == 0.0


def test_to_int():
    assert to_int("42") == 42
    assert to_int("42.7") == 42
    assert to_int("n/a") is None
    assert to_int("n/a", default=0) == 0


def test_safe_div():
    assert safe_div(3, 4) == 0.75
    assert safe_div(0, 5) == 0.0
    assert safe_div(5, 0) is None


def test_percentile():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 95) is None
    assert percentile([7], 99) == 7
    assert percentile([100, 200, 300, 400, 500], 95) == 480.0

def test_to_str():
    assert to_str("") is None
    assert to_str(None) is None
    assert to_str(" x ") == "x"


def test_parse_ts():
    assert parse_ts("") is None
    assert parse_ts("garbage") is None
    assert parse_ts("2026-10-19T14:00:05Z").minute == 0

def test_is_success():
    assert is_success(200)
    assert is_success(204)
    assert not is_success(429)
    assert not is_success(500)