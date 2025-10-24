# User Instructions and Context Summary

## Key Points from Recent Interactions

### 1. **Next Tools to Develop**
- The next tools will address workflows for **annual monitoring reports** and **construction activities**.
- These tools will be modular, combining or slightly modifying existing BMAP tools.
- Tools will focus solely on **number crunching** and mimic BMAP's output format:
  - **Tables of calculations**.
  - **Paired datasets** (e.g., profiles).

### 2. **Dataset Import/Export**
- Datasets will follow a specific format developed in the **profile database project**.
- The profile database project includes import/export scripts that will be integrated later.
- These scripts will also need to be tested.

### 3. **Output Comparisons**
- Output comparisons will be handled manually by the user.
- Tools will mimic BMAP's output format for easy validation.

### 4. **Common Folder**
- The `common` folder will house reusable functions for data handling, math, etc.
- Additional functions will be brainstormed by the user later and implemented as needed.

### 5. **Testing Plan**
- **Unit Tests**: Each tool will be tested individually.
- **Cradle-to-Grave Testing**: Full workflow testing will be done later to ensure seamless interaction between tools.

---

## Plan of Action

### 1. **Tool Development**
- Continue developing missing tools:
  - **Dean Equilibrium Profile**.
  - **Cross-Shore Sediment Transport**.
- Ensure tools are modular, computational, and follow the BMAP output format.

### 2. **Integration Preparation**
- Design tools to interface with the import/export scripts from the profile database project.
- Keep tools modular and ready for database integration.

### 3. **Common Folder Enhancements**
- Add reusable functions to the `common` folder as needed during tool development.
- Wait for the user's brainstormed list of additional functions to expand the `common` folder.

### 4. **Testing Framework**
- Write unit tests for each tool as they are developed.
- Prepare for cradle-to-grave testing once all tools are complete.

---

## Questions for Clarification

1. **Tool Development**:
   - Should I proceed with the **Dean Equilibrium Profile** tool next, or would you prefer another tool?

2. **Common Folder**:
   - Should I add any specific reusable functions to the `common` folder now, or wait for your brainstormed list?

3. **Testing**:
   - Should I start preparing unit tests for the tools already developed, or focus solely on new tool development for now?

---

## User Preferences for Tools
- Tools should focus on **number crunching** only, with no CLI or user interaction embedded.
- Tools will eventually link to the profile database but should also support file-based I/O for standalone use.
- Tools should be modular and reusable for future expansion.

---

## Reference
- Copilot instructions are located in `.github/instructions/copilot-instructions.md`.
