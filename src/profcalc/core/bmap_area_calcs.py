import numpy as np

# 1. Cross-Sectional Change Between Two Profiles
def cross_section_change(x, z1, z2):
    x, z1, z2 = map(np.array, (x, z1, z2))
    dz = z2 - z1
    delta_area = np.trapz(dz, x)
    return delta_area

# 2. Volume Above a Contour
def area_above_contour_bmap(x, z, contour_elev, xon=None, xoff=None):
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
                out_x.append(x_cross)
                out_z.append(contour_elev)
        return np.array(out_x), np.array(out_z)
    x, z = insert_crossings(x, z)
    z = np.maximum(z, contour_elev)
    return np.trapz(z - contour_elev, x)