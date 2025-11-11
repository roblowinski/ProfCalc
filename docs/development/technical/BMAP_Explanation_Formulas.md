
# BMAP Cross-Sectional Volume Computation Methodology

This document explains the methods used by **Beach Morphology Analysis Package (BMAP)** for computing cross-sectional and volumetric changes between beach profiles. It provides the formulas used for computing:

- Cross-sectional change between two profiles
- Volume above a contour
- Volume between two contours
- How BMAP handles different profile lengths and multiple crossings of a contour

---

## ⚙️ 1. Cross-Sectional Change Between Two Profiles

### Formula for Cross-Sectional Change

For two profiles (Profile 1 and Profile 2) with stations (x) and elevations (z), the **cross-sectional change** is computed as:
\[\Delta A = \sum_i
rac{(\Delta z_i + \Delta z_{i+1})}{2} \cdot (x_{i+1} - x_i)\]
where:

- \(\Delta z_i = z_{2,i} - z_{1,i}\) is the elevation difference at each station.
- \(x_i\) is the station location along the profile.

The **area difference** between the profiles is computed using the trapezoidal rule, summing the area between each pair of consecutive stations.

To compute **volume** from the area change, multiply the result by the alongshore spacing (Δy):
\[\ V = A_{\Delta} \cdot \Delta y\]

### Notes on Cross-Sectional Change

- Profiles are interpolated to a common station grid.
- If the profiles are of different lengths, only the **overlapping region** is used.
- If the profiles cross multiple times, the **signed areas** (positive for accretion, negative for erosion) are summed algebraically.

---

## 🧩 2. Volume Above a Contour

### Formula for Volume Above a Contour

The volume above a contour elevation is computed by clipping all elevations below the contour
to zero:
\[\ A_{ ext{above}} = \sum_i
rac{(z'_i + z'_{i+1})}{2} \cdot (x_{i+1} - x_i)\]
where:
\[\ z'_i = \max(z_i - z_{ ext{contour}}, 0)\]
This calculates the **cross-sectional area** above the contour, using the trapezoidal rule.

To compute the **volume**, multiply the cross-sectional area by the alongshore spacing (Δy):
\[\ V_{ ext{above}} = A_{ ext{above}} \cdot \Delta y\]

### Notes on Volume Above a Contour

- If the profile crosses the contour multiple times, BMAP calculates the area for each enclosed region and sums them.
- If a portion of the profile is below the contour, it contributes **zero** to the volume.

---

## 🧮 3. Volume Between Two Elevations

### Formula for Aligning Profiles

For computing the volume between two elevation limits:
\[\ A_{ ext{between}} = \sum_i
rac{(h_i + h_{i+1})}{2} \cdot (x_{i+1} - x_i)\]
where:
\[\ h_i = \max(z_i - z_{ ext{low}}, 0) - \max(z_i - z_{ ext{high}}, 0)\]
This computes the **cross-sectional area** between the two contours.

To compute the **volume**, multiply the cross-sectional area by the alongshore spacing (Δy):
\[\ V_{ ext{between}} = A_{ ext{between}} \cdot \Delta y\]

### Notes on Profile Alignment

- This method works even if the profile crosses the two contours multiple times, clipping and summing the areas between the bounds.

---

## 📏 4. Handling Profiles of Different Lengths

### Formula

To align two profiles with different lengths to a common grid, **linear interpolation** is used. The profile with the shorter length determines the overlap.

### Additional Notes

- Profiles are resampled to the same station spacing using linear interpolation.
- The **overlapping region** defines the limits for the analysis.

---

## 🧾 5. Multiple Crossings of the Contour

### Notes

- If the profile crosses the contour multiple times, each enclosed region is treated as a separate polygon above the contour.
- Each positive enclosed area is summed algebraically to compute the total **volume above the contour**.
- The volume for each **zonal region** (between two contours) is computed separately, and the results are aggregated.

---

## 🧮 Summary of Formulas

| Computation Type                    | Formula                                                                 | Description                              |
|--------------------------------------|-------------------------------------------------------------------------|------------------------------------------|
| **Cross-sectional change**           | \(\Delta A = \sum_i \frac{(\Delta z_i + \Delta z_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area change between profiles    |
| **Volume change**                    | \(V = A_{\Delta} \cdot \Delta y\)                                      | Computes volume between profiles         |
| **Area above contour**              | \(A_{ ext{above}} = \sum_i \frac{(z'_i + z'_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area above a specified contour  |
| rac{(z'_i + z'_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area above a specified contour  | Missing formula description              |
| **Area above contour**              | \(\frac{(z'_i + z'_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area above a specified contour  |
| **Area between contours**           | \(A_{ ext{between}} = \sum_i \frac{(h_i + h_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area between two contours       |
| rac{(h_i + h_{i+1})}{2} (x_{i+1} - x_i)\) | Computes area between two contours       | Missing formula description              |
| **Volume between contours**         | \(V_{ ext{between}} = A_{ ext{between}} \cdot \Delta y\)             | Computes volume between two contours     |

---

## End of Explanation
