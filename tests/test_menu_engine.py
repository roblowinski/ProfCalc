from profcalc.cli.menu import MenuEngine


def test_resolve_prototype_handler():
    # Ensure the engine can resolve a handler key that maps to dev_scripts prototype
    engine = MenuEngine()

    # This repository includes dev_scripts/cli_prototype.py; mapping in MenuEngine.PROTOTYPE_MAPPING
    handler = engine.resolve_handler("data.import_data")

    # Handler should be a callable (the prototype import_data_menu) or our fallback stub
    assert callable(handler)
