# Elevation Band Support: Future Enhancement

## Motivation

Currently, area and volume calculations are performed for two elevation bands:

- Above closure depth (entire active profile)
- Above MHW (subaerial beach)

To support more advanced reporting, ecological, or regulatory needs, the system should allow users to define and analyze arbitrary elevation bands (e.g., dune crest to MHW, MHW to MLW, etc.).

## Proposed Feature

- Allow user to specify any number of elevation bands (e.g., as a list of breakpoints or named bands).
- For each band, calculate:
  - Cross-sectional area within the band
  - Volume between profiles within the band
  - (Optionally) summary statistics for each band
- Output results in tables and shapefiles, with band attributes.

## Example Bands

- Dune crest to MHW
- MHW to MLW
- MLW to closure depth
- Custom regulatory or ecological bands

## Implementation Notes

- Update CLI and backend to accept a list of elevation bands.
- Refactor area/volume calculation routines to loop over bands.
- Ensure output tables and shapefiles include band information.
- Maintain backward compatibility with current two-band workflow.

## Status

- Not yet implemented (as of 2025-10-29)
- To be prioritized after core workflow validation

---

_Last updated: 2025-10-29_
