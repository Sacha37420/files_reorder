# My Tkinter File Organizer

This project is a Tkinter application designed to organize files in a user-defined structure. It utilizes Gemini AI for validation and adjustments, ensuring that the organization meets user preferences. The application scans a specified directory, categorizes files by their extensions, and organizes them into corresponding folders.

## Project Structure

```
my-tkinter-app
├── src
│   ├── organizer
│   │   └── file_organizer.py
│   ├── gui
│   │   └── app.py
│   ├── ai
│   │   └── gemini_validator.py
│   └── data
│       └── schema.json
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/my-tkinter-app.git
   ```
2. Navigate to the project directory:
   ```
   cd my-tkinter-app
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/gui/app.py
   ```
2. Input the directory you wish to organize and define your preferred file structure.
3. The application will utilize Gemini AI to validate your preferences and suggest adjustments.
4. Once confirmed, the files will be organized according to the specified schema.

## Features

- User-friendly GUI built with Tkinter.
- File organization based on user-defined structures.
- Integration with Gemini AI for validation and suggestions.
- Schema storage in JSON format for future reference.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.