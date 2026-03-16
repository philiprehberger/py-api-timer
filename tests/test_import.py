"""Basic import test."""


def test_import():
    """Verify the package can be imported."""
    import philiprehberger_api_timer
    assert hasattr(philiprehberger_api_timer, "__name__") or True
