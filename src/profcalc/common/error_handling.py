"""Compatibility shim: re-export everything from ``error_handler``.

The package previously exposed helpers from a module named
``profcalc.common.error_handling``. The consolidated implementation now
lives in ``profcalc.common.error_handler``. Importing this shim keeps
backwards compatibility for tests and third-party code that still
imports the old module name.

This intentionally performs a broad re-export; the shim is small and
exists only to ease the migration. When the codebase is fully migrated
this file can be removed.
"""

from . import error_handler as _error_handler

# Re-export public names from the consolidated implementation. We copy the
# attributes into this module's globals so that `from profcalc.common.error_handling
# import check_array_lengths` continues to work.
_public = getattr(_error_handler, "__all__", None)
if _public is None:
    # If the implementation didn't define __all__, export all non-private names.
    _public = [n for n in dir(_error_handler) if not n.startswith("_")]

for _name in _public:
    try:
        globals()[_name] = getattr(_error_handler, _name)
    except AttributeError:
        # Skip names that aren't actually present.
        pass

__all__ = list(_public)

# Provide a small compatibility helper when the consolidated implementation
# does not include older validation helpers such as `check_array_lengths`.
if "check_array_lengths" not in globals():
    from typing import List, Optional

    def check_array_lengths(
        *arrays, names: Optional[List[str]] = None
    ) -> None:
        """Ensure all provided arrays have the same length.

        This is a lightweight backport of the historical helper used by many
        modules and tests. It raises the consolidated module's
        ValidationError when available, otherwise BeachProfileError.
        """
        if len(arrays) < 2:
            return

        first_length = len(arrays[0])
        first_name = names[0] if names and len(names) > 0 else "array_0"

        for i, array in enumerate(arrays[1:], 1):
            if len(array) != first_length:
                array_name = (
                    names[i] if names and len(names) > i else f"array_{i}"
                )
                _exc = getattr(_error_handler, "ValidationError", None)
                if _exc is None:
                    _exc = getattr(_error_handler, "BeachProfileError")
                raise _exc(
                    f"Array length mismatch: {first_name} has {first_length} elements, "
                    f"{array_name} has {len(array)} elements"
                )

    globals()["check_array_lengths"] = check_array_lengths
    __all__.append("check_array_lengths")
