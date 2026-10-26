from metrics import safe_div, percentile, is_success, over_limit

def test_safe_div():
    assert safe_div(3, 4) == 0.75
    assert safe_div(0, 5) == 0.0
    assert safe_div(5, 0) is None


def test_percentile():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 95) is None
    assert percentile([7], 99) == 7
    assert percentile([100, 200, 300, 400, 500], 95) == 480.0

def test_is_success():
    assert is_success(200)
    assert is_success(204)
    assert not is_success(429)
    assert not is_success(500)

def test_over_limit():
    assert over_limit(3, 2) is True
    assert over_limit(2, 5) is False
    assert over_limit(2, 2) is False
    assert over_limit(1, None) is None