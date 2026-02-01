from sec10k.filing_finder import _first_index


def test_first_index_found():
    forms = ["8-K", "10-Q", "10-K", "10-K/A"]
    idx = _first_index(forms, "10-K")

    assert idx == 2


def test_first_index_not_found():
    forms = ["8-K", "10-Q"]
    idx = _first_index(forms, "10-K")

    assert idx is None
