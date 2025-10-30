"""
Interactive menu system for Profile Calculator.
"""


def conversion_submenu():
    """Display and handle the Conversion submenu under Quick Tools option 2."""
    while True:
        print("\n--- File Conversion Options ---")
        print("1. BMAP Free Format to XYZ/9-Col")
        print("2. BMAP Free Format to Shapefile")
        print("3. XYZ/9-Col to BMAP Free Format")
        print("4. XYZ/9-Col to Shapefile")
        print("5. Point Shapefile to BMAP Free Format")
        print("6. Point Shapefile to XYZ/9-Col")
        print("7. Return to Previous Menu")
        choice = input("Select a conversion: ").strip()

        if choice == "1":
            # BMAP to CSV conversion
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_bmap_to_csv,
                )

                execute_bmap_to_csv()
            except ImportError:
                print("❌ BMAP to CSV conversion not available.")
        elif choice == "2":
            # BMAP to Shapefile with origin azimuth
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_bmap_to_shapefile,
                )

                execute_bmap_to_shapefile()
            except ImportError:
                print("❌ BMAP to Shapefile conversion not available.")
        elif choice == "3":
            # CSV to BMAP conversion
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_csv_to_bmap,
                )

                execute_csv_to_bmap()
            except ImportError:
                print("❌ CSV to BMAP conversion not available.")
        elif choice == "4":
            # CSV to Shapefile conversion
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_csv_to_shapefile,
                )

                execute_csv_to_shapefile()
            except ImportError:
                print("❌ CSV to Shapefile conversion not available.")
        elif choice == "5":
            # Point Shapefile to BMAP conversion
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_shapefile_to_bmap,
                )

                execute_shapefile_to_bmap()
            except ImportError:
                print("❌ Shapefile to BMAP conversion not available.")
        elif choice == "6":
            # Point Shapefile to XYZ conversion
            try:
                from profcalc.cli.quick_tools.convert import (
                    execute_shapefile_to_xyz,
                )

                execute_shapefile_to_xyz()
            except ImportError:
                print("❌ Shapefile to XYZ conversion not available.")
        elif choice == "7":
            break
        else:
            print("Invalid selection. Please try again.")


def quick_tools_menu():
    """Display and handle the Quick Tools submenu."""
    while True:
        print("\n--- Quick Tools ---")
        print(
            "1. Find Common X Bounds Within a Group of Profiles in a BMap Free Format File"
        )
        print("2. Convert File Format & Create Shapefiles (i.e., 3D to 2D)")
        print("3. Get an Inventory of Profiles from a BMap Free Format File")
        print("4. Assign Profile Names to XYZ/CSV Files Missing Profile IDs")
        print("5. Back to Main Menu")
        choice = input("Select a quick tool: ").strip()

        if choice == "1":
            # Import and call bounds tool interactively
            try:
                from profcalc.cli.quick_tools.bounds import execute_from_menu

                execute_from_menu()
            except ImportError:
                print("❌ Bounds tool not available.")
        elif choice == "2":
            # Call the conversion submenu
            conversion_submenu()
        elif choice == "3":
            # Import and call inventory tool interactively
            try:
                from profcalc.cli.quick_tools.inventory import (
                    execute_from_menu,
                )

                execute_from_menu()
            except ImportError:
                print("❌ Inventory tool not available.")
        elif choice == "4":
            # Import and call assign tool interactively
            try:
                from profcalc.cli.quick_tools.assign import execute_from_menu

                execute_from_menu()
            except ImportError:
                print("❌ Assign tool not available.")
        elif choice == "5":
            break
        else:
            print("Invalid selection. Please try again.")


def main_menu():
    """Display and handle the main menu."""
    while True:
        print("\n=== ProfCalc Main Menu ===")
        print("1. File Conversion Tools")
        print("2. Profile Analysis Tools")
        print("3. Batch Processing")
        print("4. Configuration & Settings")
        print("5. Quick Tools")  # New option
        print("6. Help & Documentation")
        print("7. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            print("File Conversion Tools - Coming Soon!")
            # Placeholder for future implementation
        elif choice == "2":
            print("Profile Analysis Tools - Coming Soon!")
            # Placeholder for future implementation
        elif choice == "3":
            print("Batch Processing - Coming Soon!")
            # Placeholder for future implementation
        elif choice == "4":
            print("Configuration & Settings - Coming Soon!")
            # Placeholder for future implementation
        elif choice == "5":
            quick_tools_menu()  # Call the new submenu
        elif choice == "6":
            print("Help & Documentation - Coming Soon!")
            # Placeholder for future implementation
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Please try again.")


def launch_menu() -> None:
    """Launch the interactive menu system."""
    main_menu()

