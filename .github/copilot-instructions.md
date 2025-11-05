# Copilot Instructions for Notebook Transformations

## General Rules
- **Always activate virtual environment first**: Use `source .venv/bin/activate` before running any Python commands, installing packages, or executing scripts to ensure proper environment isolation.
- **All documentation and notes must be written in the `notes/` folder**: Use the existing convention with prefixes (e.g., `codeanalysis.`, `featurerequest.`) followed by lowercase names with dashes (e.g., `featurerequest.middleware-diagrams.md`).
- **Never include actual credentials or API keys in documentation**: Always use placeholders like "your_api_key_here" or "your_secret_key_here" instead of real values to prevent accidental exposure.
- When a user requests to transform a Python script (.py) to a Jupyter notebook (.ipynb), follow these steps to ensure completeness and usability.

## Specific Steps for Transformation
1. **Create Notebook Structure**:
   - Start with a title cell (markdown) describing the notebook's purpose.
   - Add an install cell: Use `%pip install <dependencies>` to install required libraries. Include all dependencies from the script (e.g., `transformers`, `torch`, `pillow` if needed).
   - Convert script code to python cells.
   - Convert comments to markdown cells for explanations.

2. **Dependencies**:
   - Always include `%pip install` cell unless the user specifies otherwise.
   - Base dependencies on imports: e.g., `transformers` for pipelines, `torch` for backend, `pillow` for images.
   - Use `%pip` instead of `!pip` for better notebook compatibility.

3. **Formatting**:
   - Use markdown for titles, explanations, and notes.
   - Keep code cells clean and executable.
   - Add interpretations or results explanations if relevant.

4. **Validation**:
   - Ensure the notebook is runnable from top to bottom.
   - Include error handling or notes if dependencies might fail.

This ensures notebooks are self-contained and user-friendly, avoiding repeated setup issues.