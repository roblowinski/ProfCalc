
import numpy as np


# 1. Cross-Sectional Change Between Two Profiles
def cross_section_change(x, z1, z2):
    x, z1, z2 = map(np.array, (x, z1, z2))
    dz = z2 - z1
    delta_area = np.trapz(dz, x)
    return delta_area


# 2. Volume Above a Contour

# --- Robust BMAP-style area above contour ---
# Minimal, robust BMAP-matching implementation
def area_above_contour_bmap(x, z, contour_elev, dx=10.0, xon=None, xoff=None):
    x = np.asarray(x)
    z = np.asarray(z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]
    # Restrict to XOn/XOff if specified
    if xon is not None:
        xon = float(xon)
        mask = x >= xon
        x = x[mask]
        z = z[mask]
    if xoff is not None:
        xoff = float(xoff)
        mask = x <= xoff
        x = x[mask]
        z = z[mask]
    if len(x) < 2:
        return 0.0
    # Remove exact consecutive duplicate x
    xz = [(x[0], z[0])]
    for i in range(1, len(x)):
        if x[i] == x[i-1]:
            continue
        xz.append((x[i], z[i]))
    x, z = np.array([p[0] for p in xz]), np.array([p[1] for p in xz])
    # Find crossings and insert contour points
    def insert_crossings(x, z):
        out_x, out_z = [x[0]], [z[0]]
        for i in range(1, len(x)):
            out_x.append(x[i])
            out_z.append(z[i])
            if (z[i-1] - contour_elev) * (z[i] - contour_elev) < 0:
                frac = (contour_elev - z[i-1]) / (z[i] - z[i-1])
                x_cross = x[i-1] + frac * (x[i] - x[i-1])
                out_x.insert(-1, x_cross)
                out_z.insert(-1, contour_elev)
        return np.array(out_x), np.array(out_z)
    x, z = insert_crossings(x, z)
    # Integrate area above contour
    area = 0.0
    for i in range(len(x) - 1):
        x0, x1 = x[i], x[i+1]
        z0, z1 = z[i], z[i+1]
        h0 = z0 - contour_elev
        h1 = z1 - contour_elev
        h0_clip = max(h0, 0)
        h1_clip = max(h1, 0)
        seg_area = 0.5 * (h0_clip + h1_clip) * (x1 - x0)
        area += float(seg_area)
    return area

    # Find all crossings
    crossings = []
    for i in range(1, len(x)):
        if (z[i-1] - contour_elev) * (z[i] - z[i-1]) < 0:
            frac = (contour_elev - z[i-1]) / (z[i] - z[i-1])
            x_cross = x[i-1] + frac * (x[i] - x[i-1])
            crossings.append(x_cross)
        elif (z[i-1] - contour_elev) == 0:
            crossings.append(x[i-1])
        elif (z[i] - contour_elev) == 0:
            crossings.append(x[i])
    xon = x[0] if xon is None else xon
    xoff = x[-1] if xoff is None else xoff
    # If odd number of crossings, prepend xon as a virtual wall
    if len(crossings) % 2 == 1:
        crossings = [xon] + crossings
    # If even but no crossings, treat whole profile as above contour if all z > contour
    if not crossings and np.all(z > contour_elev):
        crossings = [xon, xoff]
    # Integrate above contour for each region
    total_area = 0.0
    for i in range(0, len(crossings), 2):
        x_start, x_end = crossings[i], crossings[i+1]
        mask = (x >= x_start) & (x <= x_end)
        if np.sum(mask) < 2:
            # Interpolate at boundaries if needed
            x_region = np.linspace(x_start, x_end, int(np.ceil((x_end-x_start)/dx))+1)
            z_region = np.interp(x_region, x, z)
        else:
            x_region = x[mask]
            z_region = z[mask]
        h = np.maximum(0.0, z_region - contour_elev)
        area = np.trapz(h, x_region)
    total_area += float(area)
    return total_area


# 3. Volume Between Two Elevations
def area_between_contours(x, z, low_elev, high_elev):
    x, z = np.array(x), np.array(z)

    # Clip elevations to limits
    z_clipped = np.clip(z, low_elev, high_elev)

    # Compute height within the band
    z_between = np.maximum(z_clipped - low_elev, 0.0) - np.maximum(
        z_clipped - high_elev, 0.0
    )

    # Integrate between contours
    area_between = np.trapz(z_between, x)
    return area_between


# 4. Handling Profiles of Different Lengths
def align_profiles(x1, z1, x2, z2, spacing):
    # Determine overlapping domain
    x_min = max(np.min(x1), np.min(x2))
    x_max = min(np.max(x1), np.max(x2))

    # Common station array
    x_common = np.arange(x_min, x_max + spacing, spacing)

    # Linear interpolation
    z1i = np.interp(x_common, x1, z1)
    z2i = np.interp(x_common, x2, z2)

    return x_common, z1i, z2i


# ---- Example Usage ----
if __name__ == "__main__":
    # Sample data for two profiles
    x = np.array([0, 10, 20, 30, 40])
    old_profile = np.array([6, 4, 2, 0, -2])
    new_profile = np.array([6.5, 5, 3, 1, -1])

    # Cross-sectional change (ΔA)
    dA = cross_section_change(x, old_profile, new_profile)

    # Volume above a contour (e.g., +2 ft)
    above = area_above_contour_bmap(x, new_profile, contour_elev=2)

    # Volume between two elevations (e.g., 0 to +6 ft)
    between = area_between_contours(x, new_profile, low_elev=0, high_elev=6)

    # Output results
    print(f"ΔCross-sectional area = {dA:.2f} ft²")
    print(f"Area above +2 ft = {above:.2f} ft²")
    print(f"Area between 0–6 ft = {between:.2f} ft²")
