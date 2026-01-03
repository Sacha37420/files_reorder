# Copilot Instructions for My Tkinter File Organizer

Welcome to the My Tkinter File Organizer project! This document provides essential guidelines for AI coding agents to contribute effectively to this codebase.

## Project Overview

This project is a Tkinter-based application designed to organize files in a user-defined structure. It integrates Gemini AI for validating user preferences and suggesting adjustments. The application categorizes files by their extensions and organizes them into folders based on a schema defined by the user.

### Key Components

- **GUI**: Located in `src/gui/`, this module contains the Tkinter-based graphical interface (`app.py`, `chat_panel.py`, etc.).
- **File Organizer**: The core logic for organizing files resides in `src/organizer/file_organizer.py`.
- **AI Integration**: The Gemini AI validation logic is implemented in `src/ai/gemini_validator.py`.
- **API**: Any external API interactions are handled in `src/api/gemini.py`.
- **Tests**: Unit tests are located in the `tests/` directory.

## Development Guidelines

### Code Structure

- Follow the existing modular structure. Each subdirectory in `src/` corresponds to a specific functionality.
- Use descriptive function and variable names to maintain readability.
- Ensure that all new features integrate seamlessly with the existing GUI and AI validation logic.

### Testing

- Add unit tests for any new functionality in the `tests/` directory.
- Use `pytest` as the testing framework.
- Run tests before submitting changes:
  ```bash
  pytest tests/
  ```

### Dependencies

- All dependencies are listed in `requirements.txt`. Install them using:
  ```bash
  pip install -r requirements.txt
  ```

### Running the Application

- Start the application by running:
  ```bash
  python src/gui/app.py
  ```
- Input the directory to organize and define the file structure.

## Guidelines for Managing Dependencies

When adding new imports to the project, ensure the following:

1. **Check if the library is already listed in `requirements.txt`**:
   - Open the `requirements.txt` file located at the root of the project.
   - Verify if the library is already included.

2. **Add Missing Libraries**:
   - If the library is not listed, append it to `requirements.txt`.
   - Use the following format: `<library-name>==<version>` (if a specific version is required).

3. **Test the Installation**:
   - Run the following command to ensure the updated `requirements.txt` works correctly:
     ```bash
     pip install -r requirements.txt
     ```

4. **Document Changes**:
   - Mention the new dependency in the pull request description or commit message.

By following these steps, the project will maintain a consistent and functional dependency management process.

## Project-Specific Conventions

- **File Organization**: Use `file_organizer.py` as the entry point for organizing files. Ensure compatibility with the JSON schema stored in `src/data/schema.json`.
- **AI Validation**: Any changes to the AI logic should maintain compatibility with `gemini_validator.py`.
- **Cross-Component Communication**: Use clear function interfaces for communication between the GUI, organizer, and AI modules.

## Examples

### Adding a New File Type
To add support for a new file type:
1. Update the categorization logic in `file_organizer.py`.
2. Modify the schema in `src/data/schema.json`.
3. Test the changes using `pytest`.

### Modifying the GUI
To add a new GUI feature:
1. Implement the feature in `src/gui/app.py`.
2. Ensure it interacts correctly with the organizer and AI modules.
3. Test the GUI manually by running the application.

## Contribution Workflow

1. Fork the repository and create a new branch for your feature or bug fix.
2. Make your changes, ensuring they adhere to the guidelines above.
3. Run tests and verify that everything works as expected.
4. Submit a pull request with a clear description of your changes.

Thank you for contributing to My Tkinter File Organizer!