import importlib
import pkgutil


def iter_quick_tool_modules():
    pkg = 'profcalc.cli.quick_tools'
    # Use pkgutil to iterate submodules
    import profcalc.cli.quick_tools as qt_pkg

    prefix = qt_pkg.__name__ + '.'
    for finder, name, ispkg in pkgutil.iter_modules(qt_pkg.__path__, prefix):
        if name.endswith('__init__'):
            continue
        yield name


def test_quick_tools_cli_entrypoints_disabled():
    """Ensure quick-tool wrappers do not provide a runnable CLI entrypoint.

    For each quick_tools module, if it exposes `execute_from_cli`, calling it
    should raise NotImplementedError or ImportError (menu-only policy).
    """
    for modname in iter_quick_tool_modules():
        mod = importlib.import_module(modname)
        cli = getattr(mod, 'execute_from_cli', None)
        if callable(cli):
            try:
                # many execute_from_cli accept an args list; pass empty list
                cli([])
            except NotImplementedError:
                continue
            except ImportError:
                continue
            else:
                raise AssertionError(f"Module {modname}.execute_from_cli did not raise NotImplementedError or ImportError")
