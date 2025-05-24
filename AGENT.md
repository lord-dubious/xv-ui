# AGENT.md - Guidelines for AI Agents

## Build and Test Commands
- Run all tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_specific.py`
- Run with specific function: `python -m pytest tests/test_file.py::test_function`
- Run the application: `python webui.py`

## Code Style Guidelines
- **Formatting**: Using Ruff for code formatting and linting
- **Type Checking**: Basic type checking via VSCode settings
- **Imports**: Use absolute imports from `src.` directories
- **Type Annotations**: Use Python type hints on function parameters and return values
- **Docstrings**: Functions should have docstrings with descriptions and parameter documentation
- **Error Handling**: Use try-except blocks with specific exceptions and logging
- **Naming**: 
  - snake_case for variables and functions
  - PascalCase for classes
  - ALL_CAPS for constants
- **Async**: Project uses asyncio for async operations