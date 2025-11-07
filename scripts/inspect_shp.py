import fiona

p='bounds_both_20251107_142742_xon_xoff.shp'
with fiona.open(p) as src:
    print('SCHEMA:', src.schema)
    print('CRS:', src.crs)
    for i,f in enumerate(src):
        print('FEATURE', i, f['properties'])
        if i>3:
            break
