from app.risk.sizing import position_size_from_stop


def test_position_size_from_stop_obeys_1pct_rule() -> None:
    size = position_size_from_stop(
        equity=100000,
        entry_price=100,
        stop_price=98,
        risk_per_trade=0.01,
    )
    assert size == 500


def test_position_size_zero_when_no_stop_distance() -> None:
    size = position_size_from_stop(
        equity=100000,
        entry_price=100,
        stop_price=100,
        risk_per_trade=0.01,
    )
    assert size == 0

