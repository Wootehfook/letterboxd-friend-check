# Contributing to Letterboxd Friend Check

Thank you for considering contributing to the Letterboxd Friend Check application! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. A clear, descriptive title
2. A detailed description of the bug and how to reproduce it
3. Your operating system and Python version
4. Screenshots if applicable

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:

1. A clear, descriptive title
2. A detailed description of the feature
3. Any relevant examples or mockups
4. Explanation of how this feature would benefit users

### Code Contributions

To contribute code:

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes, following coding standards
4. Add tests for your changes
5. Run existing tests to ensure nothing breaks
6. Submit a pull request

## Development Environment

1. Clone the repository
2. Install development dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up VS Code with the recommended extensions (see .vscode/extensions.json)
4. Copy .env.example to .env and fill in required values

## Coding Standards

This project follows:

1. PEP 8 style guide for Python
2. Google docstring format for documentation
3. Type hints where appropriate

## Testing

Please run tests before submitting pull requests:

```
pytest
```

## Commit Messages

Write clear, concise commit messages:

1. Use the present tense ("Add feature" not "Added feature")
2. Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
3. Limit the first line to 72 characters or less
4. Reference issues and pull requests liberally after the first line

## Pull Requests

1. Update the README.md with details of changes if applicable
2. Update the version number following [Semantic Versioning](https://semver.org/)
3. The PR will be merged once approved by maintainers

## License

By contributing, you agree that your contributions will be licensed under the project's GNU GPL v3 license.

## Questions?

Feel free to create an issue labeled "question" for any questions about contributing.
