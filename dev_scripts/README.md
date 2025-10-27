# Development Scripts Directory

This directory contains experimental and prototype code that extends or enhances the production codebase in `src/`.

## Purpose

The scripts in this directory serve as:

1. **Prototypes** - Experimental implementations of new features
2. **Enhanced Versions** - Improved versions of production code with additional capabilities
3. **Reference Implementations** - Alternative approaches for comparison
4. **Development Tools** - Utilities for testing and development

## Important Notes

### Production vs Development Code

- **Production code** lives in `src/profcalc/` - this is the actively maintained, tested, and deployed codebase
- **Development scripts** in this directory are experimental and may not be fully tested or maintained

### File Status

| File | Status | Description |
|------|--------|-------------|
| `error_handler_enhanced.py` | Enhanced Prototype | Extended version of `src/profcalc/common/error_handler.py` with additional validation utilities |
| `validation_enhanced.py` | Enhanced Prototype | Extended validation system with additional patterns |
| `cli_prototype.py` | Prototype | Experimental CLI interface (see Issue #11) |
| `demo_coordinate_transforms.py` | Reference | Demonstration of coordinate transformation algorithms |

### Usage Guidelines

- **Do not use** dev_scripts in production deployments
- **Reference only** - use these files for inspiration or as starting points for new features
- **Merge to production** - enhancements should be properly tested and merged into `src/` before production use
- **Keep updated** - periodically review and either merge or remove outdated prototypes

## Maintenance

- Review this directory quarterly
- Remove obsolete prototypes
- Merge successful enhancements to production
- Update this README when files are added/removed

## Related Issues

- Issue #7: Code duplication between dev_scripts and src
- Issue #11: Platform-specific code in cli_prototype.py
