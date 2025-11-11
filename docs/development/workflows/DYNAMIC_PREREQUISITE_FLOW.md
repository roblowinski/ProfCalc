# Dynamic Prerequisite Handling Flow for ProfCalc CLI

**Goal:**
Allow users to select any menu item at any time. If a selected action requires a prerequisite (e.g., data loaded, config set), the system will:
- Detect the missing prerequisite.
- Inform the user what’s needed and ask for confirmation to proceed to the prerequisite step.
- If the user agrees, guide them through the required step(s), then return to their original action.
- If the user declines, return them to the previous menu without taking further action.

## Key Concepts
- **No Hard Prerequisites in Menus:** Users are never forced to manually navigate to prerequisite steps before accessing a tool or action.
- **Context Checks:** Each tool or menu action checks for required context (e.g., data loaded, settings configured) before running.
- **User Confirmation:** If something is missing, the system:
  1. Informs the user what’s needed.
  2. Asks if they want to proceed to the prerequisite step.
  3. If yes, launches the relevant menu or prompt, then returns to the original action.
  4. If no, returns to the previous menu.
- **Reusable Pattern:** This logic is implemented in a reusable way, so all tools and menus can use it without duplicating code.

## Example Flow
1. User selects “Volume Calculations” from a workflow menu.
2. System checks: Is data loaded?
   - If yes: proceed with Volume Calculations.
   - If no: inform the user, ask for confirmation to load/select data.
     - If user agrees: prompt to load/select data, then return to Volume Calculations.
     - If user declines: return to previous menu.

## Benefits
- Maximum flexibility and user-friendliness.
- No unnecessary blocking or manual navigation.
- User is always in control of workflow.
- Consistent, guided experience for all tools and workflows.
