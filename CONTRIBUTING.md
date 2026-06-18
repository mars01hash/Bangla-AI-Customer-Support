# Contributing to Bangla Customer Support Platform

Thank you for your interest in helping us improve the platform! To maintain code quality and ensure a professional developer environment, please adhere to these guidelines.

---

## Code Style Guidelines

- **Python (Backend)**: Follow PEP 8 guidelines. Indents must be 4 spaces. Ensure imports are sorted and clean.
- **Javascript/React (Frontend)**: Standard ES6+ formatting. Indents must be 2 spaces. 
- **Universal**: Use UTF-8 encoding. Ensure there are no trailing whitespaces and files end with a newline (configured automatically in [.editorconfig](file:///.editorconfig)).

---

## Submitting Pull Requests

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```
2. **Commit Changes**: Use clean, descriptive commit messages, referencing ticket IDs if applicable.
3. **Run Tests**: Ensure all unit and integration tests are passing successfully:
   ```bash
   python -m pytest tests/
   ```
4. **Push and Open PR**: Push to your branch and open a PR against the `main` branch. The GitHub Action CI pipeline will automatically lint and compile builds for verification.

---

## Ingesting FAQ / Guideline Datasets

When adding or expanding corporate data models:
- Upload CSV lists in the format: `Question, Answer, Category`
- Submit documents through the **Seed Knowledge Base** portal interface inside the Admin Dashboard.
