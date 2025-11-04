# ProfCalc Data Architecture Philosophy: Separation of Analysis and Database Access

**Last updated:** October 29, 2025

## Philosophy
- ProfCalc CLI is dedicated to local data analysis, transformation, and reporting.
- All database access, querying, and data retrieval are handled by a separate utility or the database CLI itself.
- ProfCalc CLI does not contain any code for direct database connections, queries, or authentication.
- Users export data from the database using the dedicated tool, then load it into ProfCalc for analysis.
- All work in ProfCalc is performed on local copies of data, ensuring safety, reproducibility, and flexibility.

## Benefits
- **Simplicity:** ProfCalc codebase remains focused, clean, and easy to maintain.
- **Security:** No risk of accidental database changes or exposure of credentials.
- **Reliability:** Analysis is always performed on a known, static dataset.
- **Extensibility:** Database and analysis tools can evolve independently.
- **Transparency:** Users always know which tool is responsible for which part of the workflow.

## Workflow Example
1. User queries and exports data from the database using the DB CLI or a dedicated "pipe" utility.
2. User loads the exported data into ProfCalc CLI for analysis, transformation, and reporting.
3. If needed, user can save/export results from ProfCalc for further use or sharing.
4. (Optional, future) If write-back to the database is needed, it is handled by the DB CLI or pipe utility, not ProfCalc.

## Future-Proofing
- If integration is ever needed, a dedicated interface/adapter can be built as a separate module or service, keeping ProfCalc decoupled from DB logic.
- This approach supports both standalone and enterprise workflows.

---

*This document serves as a reference for design decisions and future contributors. For more, see MENU_SYSTEM_LAYOUT.md and DYNAMIC_PREREQUISITE_FLOW.md.*
