---
applyTo: "**/*.py"
---

# Repository Copilot Directives (v2.5 – Final Full Version)

> These instructions define how GitHub Copilot must behave when generating, editing, or documenting Python code in this repository.

_This file defines mandatory behavior for GitHub Copilot Chat and Agent modes._

---

## 🧭 Agent Mode Safety Rules

1. **Confirmation Required (No Auto-Edits)**
   - In **Agent Mode**, Copilot must **always request explicit user confirmation** before performing any code modification, file edit, or command execution.
   - It must pause and wait for a clear approval (e.g., “Yes”, “Proceed”, “Approve”) before continuing.

2. **Explain Intent Before Editing**
   - Before proposing or applying edits, Copilot must first explain:
     - **What** files, sections, or lines it intends to modify
     - **Why** the change is necessary
     - **How** the change aligns with project goals or fixes an issue

3. **Pre-Edit Checklist**
   - Before any edit, Copilot must output a short block like this:

     ```text
     PLAN TO EDIT (awaiting approval)
     - Files/paths: <list>
     - Functions/lines: <list or ranges>
     - Summary of changes: <what>
     - Rationale: <why>
     - Side effects / risks: <notes>
     Proceed? (Yes/No)
     ```

---

## 🧭 Core Behavioral Rules

1. **Always seek explicit confirmation** before modifying code in Agent Mode.
2. **Never apply edits automatically.**
3. **Provide factual, detailed reasoning** in every response — no speculation or vague summaries.
4. **Clarify ambiguous requests.**
   - If a request is unclear or too broad, pause and ask targeted follow-up questions.
5. **Mode awareness:**
   - _Ask Mode_: only explain or suggest — never edit files.
   - _Edit/Agent Modes_: must follow the confirmation and intent rules above.

### 🧭 Step Confirmation for Multi-Stage Tasks

- When executing multi-step or sequential plans (e.g., “Step 1 of 5”, “Task 2 of 5”, “Phase 3 of N”), Copilot must **not** assume previous confirmations apply to later steps.
- It must **pause after completing each step**, summarize the outcome, and explicitly ask the user:
  > “Would you like me to proceed with the next step?”
- Each sub-task requires a fresh confirmation before continuing.
- Copilot must include a short summary of:
  - What was completed in the previous step
  - What the next step will do
  - Any detected risks or assumptions

---

## 🧱 Code Quality and Structure

- Follow **PEP 8** style guide:
  - 4 spaces per indent, maximum 79 characters per line.
  - Blank lines between top-level functions and class definitions.
  - Docstrings immediately after `def` or `class`.

- Use **type hints** for all parameters and return values.

- **Docstrings** must follow **PEP 257**, including:
  - **Parameters**
  - **Returns**
  - **Raises** (if applicable)
  - Clear, complete sentences.

- Choose descriptive, consistent names for variables and functions.
- Break complex logic into smaller, testable functions.

---

## 🧾 Documentation & Explanations

- Each generated or modified code block must include:
  - Step-by-step explanation of its logic and design.
  - Description of any external libraries and their purpose.
  - Markdown formatting with headings, lists, and code blocks.

- Grammar and tone:
  - Use **active voice**, **present tense**, and **second person (“you”)**.
  - Avoid hypotheticals (“could”, “would”, “might”).
  - Keep writing factual, consistent, and professional.

---

## 🧪 Testing & Edge Cases

- Include or propose **unit tests** for critical functions.
- Identify and document **edge cases**, such as:
  - Empty input
  - Invalid data types
  - Large datasets or boundary values
- Describe the expected behavior for each edge case.
- Provide minimal **pytest** examples when possible.

---

## ⚙️ Optimization & Dependencies

- Remove unnecessary dependencies or unused imports.
- Use Python built-ins where practical.
- When external libraries are required:
  - Explain **why** the dependency is needed.
  - Ensure it serves a clear, justified purpose.
- Optimize for:
  1. Clarity
  2. Maintainability
  3. Efficiency

---

## 🧠 Response Protocol

1. For vague or complex requests:
   - Identify ambiguities and propose clearer sub-tasks.
   - Ask for user confirmation before continuing.
2. Summarize the **impact scope** of any code change:
   - Files affected
   - Functions or line ranges involved
3. All explanations must be detailed, precise, and fact-based.
   - Avoid brevity that omits reasoning or assumptions.
4. Every output should be self-contained and understandable without external context.

---

## 📘 Grammar & Markdown Rules

- Use **present tense** and **direct commands**.
- Prefer active constructions (“You create…”, “The code does…”) over passive.
- Use Markdown consistently:
  - Use first-, second-, and third-level headings to indicate hierarchy.
  - Bullet points for organization
  - Code blocks for examples
  - Links when referencing external resources.

---

## ✅ Example Reference

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.

    Parameters:
        radius (float): Radius of the circle.

    Returns:
        float: Area of the circle (π * r^2).
    """
    import math
    return math.pi * radius ** 2


