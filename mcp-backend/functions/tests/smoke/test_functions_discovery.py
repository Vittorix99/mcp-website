def test_functions_discovery_with_fake_providers():
    import main
    for name in ("get_all_events", "get_membership_price_public", "member_get_me", "on_purchase_written", "on_membership_created"):
        assert callable(getattr(main,name))
    assert main.runtime_settings.environment.value == "test"
    assert main.runtime_settings.providers.sender.value == "disabled"
