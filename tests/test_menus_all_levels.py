import builtins


def run_with_sequence(monkeypatch, seq, target):
    it = iter(seq)
    monkeypatch.setattr(builtins, "input", lambda prompt='': next(it))
    # Run the provided callable (menu function)
    target()


def test_data_management_menu(monkeypatch):
    import profcalc.cli.menu_system as ms

    # Ensure no data source prompt
    ms.app_state.data_source = 'session'

    calls = {}

    def fake_list():
        calls['list'] = True

    def fake_select(dsid):
        calls['select'] = dsid

    def fake_summary():
        calls['summary'] = True

    # Patch data tools
    import profcalc.cli.tools.data as data_tools

    monkeypatch.setattr(data_tools, 'list_datasets', fake_list)
    monkeypatch.setattr(data_tools, 'select_dataset', fake_select)
    monkeypatch.setattr(data_tools, 'summary', fake_summary)

    # Sequence: list, select (provide id), view summary, back
    seq = ['3', '4', 'mydataset', '5', '6']
    run_with_sequence(monkeypatch, seq, ms.data_management_menu)

    assert calls.get('list') is True
    assert calls.get('select') == 'mydataset'
    assert calls.get('summary') is True


def test_annual_monitoring_and_submenus(monkeypatch):
    import profcalc.cli.menu_system as ms

    calls = {}

    def fake_compute_aer():
        calls['aer'] = True

    # Patch annual_tools.compute_aer
    import profcalc.cli.tools.annual as annual_tools

    monkeypatch.setattr(annual_tools, 'compute_aer', fake_compute_aer)

    # Patch profcalc and shoreline sub menus
    monkeypatch.setattr(ms, 'profcalc_profcalc_menu', lambda: calls.setdefault('profcalc', True))
    monkeypatch.setattr(ms, 'shoreline_analysis_menu', lambda: calls.setdefault('shoreline', True))

    seq = ['2', '3', '4', '7']
    run_with_sequence(monkeypatch, seq, ms.annual_monitoring_menu)

    assert calls.get('aer') is True
    assert calls.get('profcalc') is True
    assert calls.get('shoreline') is True


def test_shoreline_analysis_menu(monkeypatch, capsys):
    import profcalc.cli.menu_system as ms

    seq = ['1', '5']
    run_with_sequence(monkeypatch, seq, ms.shoreline_analysis_menu)
    out = capsys.readouterr().out
    assert '[STUB] Extract & Prepare Shoreline Data' in out


def test_profcalc_profile_menus(monkeypatch):
    import profcalc.cli.menu_system as ms

    calls = {}

    monkeypatch.setattr(ms, 'survey_vs_design_menu', lambda: calls.setdefault('design', True))
    monkeypatch.setattr(ms, 'survey_vs_survey_menu', lambda: calls.setdefault('survey', True))

    seq = ['1', '2', '3']
    run_with_sequence(monkeypatch, seq, ms.profcalc_profcalc_menu)

    assert calls.get('design') is True
    assert calls.get('survey') is True


def test_survey_vs_design_and_survey_menus(monkeypatch, capsys):
    import profcalc.cli.menu_system as ms

    # survey_vs_design_menu: choose a stub option then back
    run_with_sequence(monkeypatch, ['1', '6'], ms.survey_vs_design_menu)
    out1 = capsys.readouterr().out
    assert '[STUB] Option' in out1

    # survey_vs_survey_menu: choose a stub option then back
    run_with_sequence(monkeypatch, ['1', '7'], ms.survey_vs_survey_menu)
    out2 = capsys.readouterr().out
    assert '[STUB] Option' in out2


def test_quick_tools_and_conversion_submenus(monkeypatch):
    import profcalc.cli.menu_system as ms

    # Patch quick tool modules to avoid heavy work
    class FakeTool:
        def __init__(self, name):
            self.name = name

        def execute_from_menu(self):
            called.setdefault(self.name, True)

    called = {}

    fake_fix = FakeTool('fix')
    fake_bounds = FakeTool('bounds')
    fake_inventory = FakeTool('inventory')
    fake_assign = FakeTool('assign')
    fake_fix_mod = FakeTool('fixmod')
    fake_get_dates = FakeTool('getdates')
    fake_convert = FakeTool('convert')

    # Monkeypatch imports inside quick_tools_menu
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.fix_bmap', fake_fix)
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.bounds', fake_bounds)
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.inventory', fake_inventory)
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.assign', fake_assign)
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.get_profile_dates', fake_get_dates)
    # For fix_bmap.execute_modify_headers_menu call path, patch the module used in quick_tools_menu
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.fix_bmap', fake_fix)

    # For conversion submenu, module 'profcalc.cli.quick_tools.convert'
    monkeypatch.setitem(__import__('sys').modules, 'profcalc.cli.quick_tools.convert', fake_convert)

    # Run quick tools menu: call options 1-6 then return
    seq = ['1', '2', '3', '4', '5', '6', '', '7']
    run_with_sequence(monkeypatch, seq, ms.quick_tools_menu)

    # Ensure each fake tool was invoked
    assert called.get('fix') is True
    assert called.get('bounds') is True
    assert called.get('inventory') is True
    assert called.get('assign') is True
    # fixmod indirect path will call same module
    assert called.get('getdates') is True

    # Test conversion_submenu mapping 1-6 to convert tool
    seq2 = ['1', '2', '3', '4', '5', '6', '7']
    run_with_sequence(monkeypatch, seq2, ms.conversion_submenu)

    assert called.get('convert') is True
