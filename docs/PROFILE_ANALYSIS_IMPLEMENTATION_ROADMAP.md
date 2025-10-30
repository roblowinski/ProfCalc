# Profile Analysis Implementation Roadmap

This document summarizes the plan for implementing profile-based volume analyses in the ProfCalc program, based on recent workflow discussions and leveraging existing BMAP tools.

---

## Overview

There are two primary profile analysis workflows required for annual monitoring and reporting:

1. **Survey vs. Design Template (Beachfill) Analysis**
2. **Survey vs. Survey (Year-to-Year) Analysis**

Both workflows rely on the same core logic for volume calculation, with differences in the reference profile used. BMAP tools and supplemental data (e.g., Profile Origin Azimuth files) are integral to automating and streamlining these analyses.

---

## Stepwise Implementation Plan

### 1. Data Preparation

- **Input:** Surveyed profile files (BMAP, CSV, etc.), Design template profiles (if applicable), Profile Origin Azimuth file.
- **BMAP Tools:** Use BMAP parsers to extract profile data, stationing, and metadata.

### 2. Profile Pairing and Metadata Extraction

- **Action:**
  - For Survey vs. Design: Pair each surveyed profile with its corresponding design template.
  - For Survey vs. Survey: Pair each profile from one survey year with the same profile from another year.

- **BMAP Tools:** Use BMAP metadata and Profile Origin Azimuth file to:
  - Identify and order profiles (typically north to south)
  - Extract origin coordinates and azimuths for each profile

### 3. Interpolation to Common Stations

- **Action:** Interpolate all profiles in a pair to a common set of stations (chainages).

- **BMAP Tools:** Use or extend BMAP interpolation utilities to ensure both profiles in a pair have matching station points.

### 4. Plan-View Distance Calculation

- **Action:** For each station, calculate the true plan-view (map) distance between the two profiles using their origin coordinates and azimuths.

- **BMAP Tools:** Use BMAP coordinate utilities or add new functions to project station points and compute distances.

### 5. Cross-Sectional Area Calculation

- **Action:** At each station, compute the area between the two profiles (trapezoidal or similar method).

- **BMAP Tools:** Use or extend BMAP area calculation routines.

### 6. Wedge/Prism Volume Calculation

- **Action:** For each station, multiply the cross-sectional area by the plan-view distance to get the wedge/prism volume. Sum across all stations for the total volume between profiles.

- **BMAP Tools:** Implement or adapt BMAP volume calculation logic to use interpolated stations and plan-view distances.

### 7. Batch Processing and Automation

- **Action:** Automate the above steps for all profile pairs in the network, using the ordered list from the Profile Origin Azimuth file.

- **BMAP Tools:** Leverage BMAP batch processing capabilities or add new automation scripts.

### 8. Output and Reporting

- **Action:** Export results (volumes, areas, summary tables) to CSV or other report formats for inclusion in monitoring reports.

- **BMAP Tools:** Use BMAP export utilities or extend as needed for reporting.

---

## Relationship to BMAP Tools

- **Parsing & Metadata:** BMAP tools handle file parsing, metadata extraction, and initial data structuring.
- **Interpolation & Area:** BMAP routines can be used or extended for interpolation and area calculations.
- **Distance & Volume:** New or adapted BMAP functions will handle plan-view distance and wedge volume calculations.
- **Batch Automation:** BMAP’s scripting and batch features will be leveraged for network-wide processing.
- **Reporting:** BMAP export tools will be used for outputting results in required formats.

---

## Notes

- The Profile Origin Azimuth file is critical for automating profile pairing, ordering, and distance calculations.
- The CLI should provide clear, separate workflows for Survey vs. Design and Survey vs. Survey analyses.
- The same core logic applies to both workflows; only the reference profile source changes.
- All steps should be as automated as possible to minimize manual intervention and ensure repeatability.

---

_Last updated: 2025-10-29_
