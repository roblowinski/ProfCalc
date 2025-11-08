from profcalc.common.csv_io import _load_profile_origin_azimuths

p = "src/profcalc/data/required_inputs/ProfileOriginAzimuths.csv"
df = _load_profile_origin_azimuths(p)
print(df.head())
print(df.dtypes)
