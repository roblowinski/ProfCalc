# Tool Development Roadmap

## Phase I: BMAP Tool Replication
This phase replicates the core tools of the USACE Beach Morphology Analysis Package (BMAP), aimed at providing coastal engineers with accurate and standardized analysis tools.

### Completed Tools
- **Dean Equilibrium Profile**: Generates the Dean equilibrium profile for a given beach.
- **Modified Equilibrium Profile (MEP)**: Estimates the modified equilibrium profile based on a grain size or A-parameter.
- **Transport Rate**: Computes the cross-shore sand transport rate from two profiles.
- **Least Squares Regression**: Performs a least-squares regression on profile data to estimate beach slope (A-parameter).
- **Align Profiles**: Aligns two profiles based on a reference elevation.
- **Compare Profiles**: Compares two profiles and computes volume and contour change.
- **Slope Profile**: Computes the slope of a beach profile.
- **Translate Profile**: Translates (shifts) a beach profile horizontally and vertically.
- **Bar Properties**: Computes geometric properties of submerged beach bars.
- **Volume Calculation**: Computes the volume of material between two profiles.

### Tools Yet to be Developed
- **Beach Fill Template Tool**: Currently not planned for implementation.
  
---

## Phase II: Monitoring Tools
These tools focus on routine monitoring and analysis of beach profile changes over time. They are used for creating annual reports, long-term trend analyses, and other monitoring activities.

### Planned Tools
- **Volume Change Trends**: Computes changes in volume over time across multiple profiles.
- **Profile Evolution**: Tracks profile change over multiple years.
- **Shoreline Change Analysis**: Analyzes changes in the shoreline location over time.

---

## Phase III: Construction Tools
These tools will aid in beachfill construction projects, including progress tracking, design comparisons, and post-construction analysis.

### Planned Tools
- **Fill Progress Tracker**: Tracks the progress of beachfill construction and calculates volume added over time.
- **Template Comparison**: Compares constructed profile with design template.
- **Section Compare Tool**: Compares profile sections across different construction phases.

---

## Phase IV: Integrated Workflows
This phase will involve creating workflows that combine multiple tools for seamless, comprehensive analyses.

### Planned Workflows
- **Annual Monitoring Workflow**: A workflow combining profile comparison, volume change, and shoreline change tools for the annual report generation.
- **Beachfill Performance Evaluation**: Combines volume tracking, profile comparisons, and fill tracking tools to evaluate the success of a beachfill project.
