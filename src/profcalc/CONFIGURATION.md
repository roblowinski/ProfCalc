# Configuration System

This project uses a hierarchical configuration system with clear separation of concerns.

## Configuration Files

### 1. Analysis Configuration (`src/profcalc/common/config.json`)

**Purpose:** Analysis parameters and defaults used during computation
**Scope:** Production code - actively used by analysis functions
**Contents:**

- `dx`: Grid spacing for volume calculations and profile analysis (default: 10.0 feet)

**Usage:** Loaded by `config_utils.get_dx()` function

### 2. Application Configuration (`src/profcalc/settings/config.json`)

**Purpose:** Project metadata and application-level settings
**Scope:** Placeholder for future expansion - not currently used
**Contents:**

- Project metadata (version, name, description)
- Default units
- Path configurations

**Usage:** Reserved for future application-level configuration

## Configuration Hierarchy

1. **Analysis Config** (highest priority for analysis parameters)
   - Used by: Volume calculations, profile analysis, grid operations
   - Override: Environment variables or function parameters

2. **Application Config** (lower priority, future use)
   - Used by: Application initialization, UI settings, paths
   - Override: Command line arguments, environment variables

## Adding New Configuration

- **Analysis parameters** → Add to `common/config.json`
- **Application settings** → Add to `settings/config.json`
- **Environment overrides** → Use environment variables
- **Runtime overrides** → Function parameters

## Future Considerations

When the application grows, consider:

- Environment-specific configs (dev/prod)
- User-specific overrides
- Configuration validation on startup
- Configuration migration utilities
