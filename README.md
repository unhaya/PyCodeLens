# 🔍 PyCodeLens: LLM-Ready Python Code Analyzer

[![GitHub Stars](https://img.shields.io/github/stars/unhaya/pycodelens?style=social)](https://github.com/unhaya/pycodelens)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)

> **When LLMs face complex codebases, PyCodeLens becomes their eyes.**

PyCodeLens is a powerful Python code analysis tool designed specifically to help developers work with Large Language Models (LLMs) on complex codebases. Stop overwhelming your LLM with thousands of lines of code - feed it structured insights instead.


## 🌟 Why PyCodeLens?

Ever tried asking Claude or GPT to understand a large codebase? Painful, right?

**Problem:** LLMs have token limits and struggle with large, multi-file codebases
**Solution:** PyCodeLens extracts the crucial structural information your LLM needs

## 🚀 Key Features

- 🔄 **Smart Codebase Summaries**: Transforms complex Python codebases into LLM-friendly JSON
- 🧩 **Class & Method Analysis**: Extracts all classes, methods, and their relationships
- 📊 **Dependency Mapping**: Visualizes call graphs and module dependencies
- 🌲 **Directory Structure**: Delivers clean, navigable file trees
- 🖥️ **UI Interface**: Intuitive GUI for exploring and exporting analysis
- 📋 **Clipboard Integration**: Copy results directly for immediate use with LLMs
- 🔌 **Extensible Architecture**: Ready for adding more languages and analysis types

## 💡 Perfect For

- **LLM Developers**: Feed structured code insights to Claude, GPT, etc.
- **Open Source Contributors**: Quickly understand new projects
- **Code Reviewers**: Get high-level views of project structure
- **Python Learners**: Visualize how real-world Python projects work

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/unhaya/pycodelens.git

# Navigate to the project directory
cd pycodelens

# Install dependencies
pip install -r requirements.txt

# Run the application
python "main.py"
```

## 📋 Quick Usage

1. Launch PyCodeLens
2. Import a Python file or directory
3. View the analysis results in the structured tabs
4. Copy the JSON output to clipboard
5. Paste directly to your favorite LLM with your coding questions
6. Use right-click and Ctrl+click in the directory tree for additional options

## 🖱️ Advanced Interface Tips

### Directory Tree Navigation
- **Right-click**: Opens a context menu with options to:
  - Open file in Explorer/Finder
  - Open file with default application
- **Ctrl+click**: Excludes the selected file or directory from analysis
  - Excluded items appear grayed out
  - Re-click to include them again in the analysis

These features help you quickly navigate through the codebase and customize which parts should be included in the analysis.

## 🖼️ Screenshots

<img src="screenshot/pycodelens_screenshot.png" alt="スクリーンショット" width="600" />
<img src="screenshot/pycodelens_screenshot.png" alt="スクリーンショット" width="600" />

## 🏗️ Project Structure

```
PyCodeLens/
├── main.py			# Core analysis functionality
└── simple_json_converter.py	# JSON conversion utilities
```

### Main Components

- **ConfigManager**: Handles application settings and previous sessions
- **CodeAnalyzer**: Base class for code analysis
- **AstroidAnalyzer**: Deep semantic analysis with Astroid
- **DirectoryTreeView**: UI for navigating project files
- **SyntaxHighlighter**: Code visualization helper
- **CodeAnalyzerApp**: Main application UI

## 🚀 Roadmap

- [ ] Support for additional programming languages (JavaScript, Java, C++)
- [ ] Export results in multiple formats (PDF, HTML, Markdown)
- [ ] Plugins for direct LLM API integration
- [ ] Web version for browser-based analysis
- [ ] Performance optimizations for very large codebases
- [ ] Full test coverage and CI/CD pipeline

## 👥 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Here's how you can contribute:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## 💌 Contact

[@haasiy](https://x.com/haassiy) - haasiy@gmail.com

[https://github.com/unhaya/pycodelens/](https://github.com/unhaya/pycodelens/)

---

<p align="center">
  <b>Made with ❤️ for the LLM development community</b><br>
  <i>Give your LLMs the gift of code understanding</i>
</p>
