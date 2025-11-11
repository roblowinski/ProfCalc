import builtins


def run_menu_with_sequence(monkeypatch, seq):
    """Helper to run main_menu with a predefined sequence of inputs.

    The sequence must include a terminating '9' to exit the main loop.
    """
    import profcalc.cli.menu_system as ms

    it = iter(seq)

    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))
    # Run the menu; it will exit when '9' is provided in seq
    ms.main_menu()


def test_main_menu_calls_data_management(monkeypatch):
    import profcalc.cli.menu_system as ms

    called = {}

    def fake_data():
        called["data"] = True

    monkeypatch.setattr(ms, "data_management_menu", fake_data)
    run_menu_with_sequence(monkeypatch, ["1", "9"])
    assert called.get("data") is True


def test_main_menu_calls_annual_monitoring(monkeypatch):
    import profcalc.cli.menu_system as ms

    called = {}

    def fake_annual():
        called["annual"] = True

    monkeypatch.setattr(ms, "annual_monitoring_menu", fake_annual)
    run_menu_with_sequence(monkeypatch, ["2", "9"])
    assert called.get("annual") is True


def test_main_menu_calls_conversion_submenu(monkeypatch):
    import profcalc.cli.menu_system as ms

    called = {}

    def fake_conv():
        called["conv"] = True

    monkeypatch.setattr(ms, "conversion_submenu", fake_conv)
    run_menu_with_sequence(monkeypatch, ["3", "9"])
    assert called.get("conv") is True


def test_main_menu_calls_profile_analysis(monkeypatch):
    import profcalc.cli.menu_system as ms

    called = {}

    def fake_prof():
        called["prof"] = True

    monkeypatch.setattr(ms, "profcalc_profcalc_menu", fake_prof)
    run_menu_with_sequence(monkeypatch, ["4", "9"])
    assert called.get("prof") is True


def test_batch_and_config_prints(monkeypatch, capsys):
    # Options 5 and 6 only print a stub message
    run_menu_with_sequence(monkeypatch, ["5", "6", "9"])
    # capture combined output and ensure stub lines present
    out = capsys.readouterr().out
    assert "Batch Processing - Coming Soon!" in out
    assert "Configuration & Settings - Coming Soon!" in out


def test_quick_tools_and_about(monkeypatch, capsys):
    import profcalc.cli.menu_system as ms

    called = {}

    def fake_quick():
        called["quick"] = True

    monkeypatch.setattr(ms, "quick_tools_menu", fake_quick)

    # run sequence: invoke quick tools, invoke about, then exit
    run_menu_with_sequence(monkeypatch, ["7", "8", "9"])
    assert called.get("quick") is True

    out = capsys.readouterr().out
    assert "ProfCalc" in out


def test_exit_only(monkeypatch):
    # Ensure providing '9' immediately exits the menu cleanly
    run_menu_with_sequence(monkeypatch, ["9"])
