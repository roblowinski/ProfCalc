"""
Interactive menu system for Profile Calculator.
"""


def launch_menu() -> None:
    """Launch the interactive menu system."""
    print("\n" + "=" * 80)
    print("PROFILE CALCULATOR SYSTEM")
    print("=" * 40)
    print("\nFor now, please use the quick tools via command-line flags:")
    print("\n  profcalc -b <files> -o <output>    # Find common bounds")
    print("  profcalc -c <input> --to <format> -o <output>  # Convert format")
    print("  profcalc -i <file> -o <output>     # File inventory")
    print("  profcalc -a <xyz> --baselines <file> -o <output>  # Assign XYZ")
    print("  profcalc -f <input> -o <output>    # Fix BMAP point counts")
    print("\nRun 'profcalc -h' for more details.\n")

