from integrations import towing


def test_classify_light_duty_by_default() -> None:
    assert towing.classify("2015 Honda Accord") == "light"
    assert towing.classify("2019 Ford F-150") == "light"
    assert towing.classify("") == "light"
    assert towing.classify(None) == "light"


def test_classify_medium_duty_keywords() -> None:
    assert towing.classify("Ford Transit box truck") == "medium"
    assert towing.classify("Mercedes Sprinter cargo van") == "medium"
    assert towing.classify("F-350 dually flatbed") == "medium"


def test_rate_for_picks_class_then_falls_back() -> None:
    rates = [
        {"class": "light", "base_price": 85.0},
        {"class": "medium", "base_price": 199.0},
    ]
    assert towing.rate_for(rates, "medium")["base_price"] == 199.0
    assert towing.rate_for(rates, "light")["base_price"] == 85.0
    # Unknown class → first row; empty → None.
    assert towing.rate_for(rates, "heavy")["base_price"] == 85.0
    assert towing.rate_for([], "light") is None
