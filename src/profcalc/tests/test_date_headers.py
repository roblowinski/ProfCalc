# Quick test to verify Profile date handling
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np

from profcalc.common.bmap_io import Profile, write_bmap_profiles

# Test 1: Profile with explicit date
profiles_with_date = [
    Profile(
        name="OC117",
        date="15AUG2020",
        description="Pre-storm survey",
        x=np.array([10.0, 20.0, 30.0]),
        z=np.array([5.0, 4.5, 4.0]),
    )
]

write_bmap_profiles(
    profiles_with_date, "src/profcalc/data/temp/test_profile_with_date.dat"
)
print(
    "✅ Created test_profile_with_date.dat - should show: OC117 15AUG2020 Pre-storm survey"
)

# Test 2: Profile without date, but with source filename containing date
profiles_no_date = [
    Profile(
        name="TEST001",
        date=None,
        description="Test profile",
        x=np.array([100.0, 150.0]),
        z=np.array([8.5, 7.2]),
    )
]

write_bmap_profiles(
    profiles_no_date,
    "src/profcalc/data/temp/test_no_date.dat",
    source_filename="survey_2024-10-26.xyz",
)
print(
    "✅ Created test_no_date.dat - should show: TEST001 26OCT2024 Test profile"
)

# Test 3: Profile without date, source filename has no date
profiles_filename_only = [
    Profile(
        name="BEACH01",
        date=None,
        description=None,
        x=np.array([50.0, 100.0]),
        z=np.array([6.0, 5.5]),
    )
]

write_bmap_profiles(
    profiles_filename_only,
    "src/profcalc/data/temp/test_filename_only.dat",
    source_filename="coastal_data.xyz",
)
print(
    "✅ Created test_filename_only.dat - should show: BEACH01 from_coastal_data"
)

print("\n📋 Verification:")
for fname in [
    "test_profile_with_date.dat",
    "test_no_date.dat",
    "test_filename_only.dat",
]:
    path = Path(f"src/profcalc/data/temp/{fname}")
    if path.exists():
        first_line = path.read_text().split("\n")[0]
        print(f"  {fname}: {first_line}")
