# Coastal Profile Analysis - Documentation Index

**Last Updated:** October 26, 2025

## Quick Start

- [README](../../../README.md) - Project overview and installation
- [FEATURES.md](FEATURES.md) - Current implemented features

## User Guides

### File Conversion
- [CONVERSION_GUIDE.md](CONVERSION_GUIDE.md) - Complete guide to format conversion
  - Supported formats (BMAP, CSV, XYZ, Shapefile)
  - Column order customization
  - Edge cases and validation
  - Troubleshooting

### Shapefile Export
- [SHAPEFILE_EXPORT.md](SHAPEFILE_EXPORT.md) - GIS shapefile export feature
  - Point and line shapefiles
  - 3D geometry support
  - Coordinate reference systems
  - Integration with ArcGIS/QGIS

## Technical Reference

- [DateFunctions.md](DateFunctions.md) - Date parsing and formatting utilities
- [VALIDATION_IMPLEMENTATION_SUMMARY.md](VALIDATION_IMPLEMENTATION_SUMMARY.md) - Recent validation fixes

## Development & Planning

- [FUTURE_DEVELOPMENT.md](FUTURE_DEVELOPMENT.md) - Planned features and enhancements
  - Modular analysis tools
  - Validation strategy
  - Future workflows

## File Organization

```
docs/
├── INDEX.md                              # This file - documentation navigation
├── FEATURES.md                           # Current implemented features
├── CONVERSION_GUIDE.md                   # File conversion documentation
├── SHAPEFILE_EXPORT.md                   # Shapefile export feature
├── VALIDATION_IMPLEMENTATION_SUMMARY.md  # Validation fixes summary
├── DateFunctions.md                      # Date handling reference
└── FUTURE_DEVELOPMENT.md                 # Planning and future work
```

## Getting Help

- Check the relevant guide above for your use case
- Run `profcalc -h` for command-line help
- See test files in `src/profcalc/tests/` for examples
