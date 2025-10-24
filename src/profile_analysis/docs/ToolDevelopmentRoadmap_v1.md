# 🧭 BMAP Clone & Expansion – Tool Development Roadmap

## Overview
This roadmap outlines the **development plan for the analysis tools** used to replicate and extend BMAP (Beach Morphology Analysis Package) functionality.
The focus here is strictly on **tool logic, calculations, and validation** — independent of the database, GUI, or CLI integrations.

The goal is to:
- Reproduce BMAP tools one-by-one with verified numerical agreement.
- Extend functionality to automate multi-profile and alongshore analyses.
- Build a modular, reusable toolkit forming the analytical core of the broader system.

---

## Phase 1 – Foundation: Core Framework

### 🎯 Objectives
- Establish consistent **data structures** (e.g., `Profile`, `VolumeResult`, etc.).
- Standardize **file input/output** using ASCII/CSV profile files for standalone testing.
- Implement and test **math utilities**:
  - Interpolation
  - Trapezoidal integration
  - Cross-shore clipping
  - Contour crossing

### 📁 Deliverables
- `/core/data_types.py` — defines shared dataclasses
- `/core/utils.py` — numerical helpers for all modules
- `/core/io_ascii.py` — reads simple profile files
- `tests/` — baseline validation scripts using known BMAP outputs

---

## Phase 2 – BMAP-Equivalent Tool Modules

Each module will be developed, verified against BMAP output, and documented individually.

### 2.1 Volume Analysis
**Purpose:** Compute cross-sectional area and volume above a reference elevation.

**Features:**
- Volume between user-specified limits (`x₀`, `x₁`)
- Optional volume above a contour (e.g., +2.5 ft NAVD88)
- Output total, above-reference, and below-reference volumes

**Deliverables:**
- `/modules/volume.py`
- Validation: compare to BMAP Volume and Volume Above Contour outputs

---

### 2.2 Profile Comparison
**Purpose:** Replicate BMAP’s Cut/Fill and Contour Change routines.

**Features:**
- Align profiles by common datum (z-align)
- Compute cut, fill, and net change volumes
- Calculate Δx for contours (shoreline, MHW, etc.)

**Deliverables:**
- `/modules/compare.py`
- Validation: compare against BMAP “Profile Comparison” reports

---

### 2.3 Alignment Tool
**Purpose:** Reproduce BMAP’s horizontal alignment behavior.

**Features:**
- Landward-most crossing alignment
- User-specified alignment elevation (e.g., MHW)
- Optional datum shift summary

**Deliverables:**
- `/modules/align.py`
- Validation: overlay plots showing matched alignment to BMAP outputs

---

### 2.4 Dean Equilibrium Profile
**Purpose:** Implement the equilibrium profile fitting (h = A·x^(2/3)).

**Features:**
- Fit A parameter (least squares)
- Generate equilibrium curve for comparison
- Compute fit error (RMSE)
- Optional plot overlay for QA

**Deliverables:**
- `/modules/equilibrium.py`
- Validation: A-value and curve fit agreement with BMAP

---

### 2.5 Bar Geometry
**Purpose:** Replicate BMAP’s bar/trough detection and volume tools.

**Features:**
- Identify bar crest/trough positions
- Compute bar height, depth, and volume
- Optionally integrate multiple bars per profile

**Deliverables:**
- `/modules/bars.py`
- Validation: check against BMAP bar analysis tables

---

### 2.6 (Optional) Cross-Shore Sediment Transport
**Purpose:** Implement BMAP’s sediment transport estimation using profile change rates.

**Features:**
- Integrate volume change over time
- Compute flux using sediment density assumptions
- Output net transport rate (yd³/ft/yr)

**Deliverables:**
- `/modules/transport.py`
- Validation: approximate agreement with BMAP Transport Rate results (if available)

---

## Phase 3 – Composite / “Black Box” Tools

These combine two or more core modules into higher-level automated analyses based on real workflows.

### 3.1 Alongshore Volume Tool
**Purpose:** Compute beach volume along a reach using average end area (AEA) method.

**Features:**
- Accept multiple profiles and spacing info
- Integrate volumes between adjacent profiles
- Output total beach volume and average change

**Deliverables:**
- `/modules/alongshore_volume.py`
- Validation: compare to Excel-calculated AEA results currently used in reporting

---

### 3.2 Annual Change Analyzer
**Purpose:** Automate yearly comparison and reporting of beach fill performance.

**Features:**
- Pull two survey years for all stations
- Compute volume and contour changes per profile
- Aggregate by re
