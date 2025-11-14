# Copilot Instructions for Notebook Transformations

## General Rules
- **Always activate virtual environment first**: Use `source .venv/bin/activate` before running any Python commands, installing packages, or executing scripts to ensure proper environment isolation.
- **All documentation and notes must be written in the `notes/` folder**: Use the existing convention with prefixes (e.g., `codeanalysis.`, `featurerequest.`) followed by lowercase names with dashes (e.g., `featurerequest.middleware-diagrams.md`).
- **Never include actual credentials or API keys in documentation**: Always use placeholders like "your_api_key_here" or "your_secret_key_here" instead of real values to prevent accidental exposure.
- When a user requests to transform a Python script (.py) to a Jupyter notebook (.ipynb), follow these steps to ensure completeness and usability.

## LLM Setup & Configuration
- **LLM Client**: Use `ChatOpenAI` from `langchain_openai` for all LLM calls (NOT `litellm.completion()`)
  - Reason: `litellm.completion()` has issues with Azure model name parsing for models like `gpt-5-mini`
  - `ChatOpenAI` properly handles Azure model names and base_url configuration
- **API Keys**: Credentials come from environment variables (use LiteLLM naming convention):
  - `LITELLM_MODEL`: Model name (e.g., `gpt-5-mini`, `gpt-4`)
  - `LITELLM_VIRTUAL_KEY`: API key for authentication
  - `LITELLM_API`: API base URL (e.g., `https://proxyllm.id`)
- **Implementation Pattern**:
  ```python
  from langchain_openai import ChatOpenAI
  from pydantic import SecretStr
  
  model = ChatOpenAI(
      api_key=SecretStr(os.getenv('LITELLM_VIRTUAL_KEY')),
      model=os.getenv('LITELLM_MODEL', 'gpt-4'),
      base_url=os.getenv('LITELLM_API'),
      temperature=1.0,  # For reasoning models
  )
  
  response = model.invoke([{"role": "user", "content": prompt}])
  result = response.content  # String content
  ```

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