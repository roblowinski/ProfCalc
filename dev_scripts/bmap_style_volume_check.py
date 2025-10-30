import numpy as np


def bmap_style_volume_above_contour(x, z, contour, dx=10.0):
    x = np.asarray(x)
    z = np.asarray(z)
    idx = np.argsort(x)
    x, z = x[idx], z[idx]

    # Find all crossings
    crossings = []
    for i in range(1, len(x)):
        if (z[i-1] - contour) * (z[i] - z[i-1]) < 0:
            frac = (contour - z[i-1]) / (z[i] - z[i-1])
            x_cross = x[i-1] + frac * (x[i] - x[i-1])
            crossings.append(x_cross)
        elif (z[i-1] - contour) == 0:
            crossings.append(x[i-1])
        elif (z[i] - contour) == 0:
            crossings.append(x[i])
    xon = x[0]
    xoff = x[-1]
    # If odd number of crossings, prepend xon as a virtual wall
    if len(crossings) % 2 == 1:
        crossings = [xon] + crossings
    # If even but no crossings, treat whole profile as above contour if all z > contour
    if not crossings and np.all(z > contour):
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
        h = np.maximum(0.0, z_region - contour)
        area = np.trapz(h, x_region)
        total_area += area
    return total_area / 27.0  # cu yd/ft

# Example usage (replace with real data for a test):
if __name__ == "__main__":
    # Example profile: simple berm with two crossings
    x = np.array([0, 50, 100, 150, 200])
    z = np.array([2, 6, 2, 6, 2])
    contour = 4.0
    vol = bmap_style_volume_above_contour(x, z, contour)
    print(f"BMAP-style volume above contour: {vol:.3f} cu yd/ft")
