# =============================================================================
# Error Handling Compatibility Shim Module
# =============================================================================
#
# FILE: src/profcalc/common/error_handling.py
#
# PURPOSE:
# This module provides backwards compatibility for code that imports from
# the old error_handling module name. It serves as a shim that re-exports
# all functionality from the consolidated error_handler module, ensuring
# existing code continues to work during the migration period.
#
# WHAT IT'S FOR:
# - Maintaining backwards compatibility during module consolidation
# - Re-exporting all public functions from error_handler module
# - Providing legacy validation helpers that may be missing
# - Ensuring smooth transition for tests and third-party code
# - Allowing gradual migration away from old import paths
#
# WORKFLOW POSITION:
# This module exists temporarily during the refactoring process. It allows
# the codebase to evolve while maintaining compatibility. Once all imports
# have been updated to use the new error_handler module, this shim can be
# removed entirely.
#
# LIMITATIONS:
# - This is a temporary compatibility layer, not permanent code
# - Broad re-exports may hide import issues
# - Legacy validation helpers are minimal implementations
# - Should be removed once migration is complete
#
# ASSUMPTIONS:
# - The error_handler module contains all the needed functionality
# - __all__ is properly defined in the consolidated module
# - Legacy code uses standard import patterns
# - Migration will eventually eliminate the need for this shim
#
# =============================================================================

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

    def check_array_lengths(*arrays, names: Optional[List[str]] = None) -> None:
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
                array_name = names[i] if names and len(names) > i else f"array_{i}"
                _exc = getattr(_error_handler, "ValidationError", None)
                if _exc is None:
                    _exc = getattr(_error_handler, "BeachProfileError")
                raise _exc(
                    f"Array length mismatch: {first_name} has {first_length} elements, "
                    f"{array_name} has {len(array)} elements"
                )

    globals()["check_array_lengths"] = check_array_lengths
    __all__.append("check_array_lengths")
