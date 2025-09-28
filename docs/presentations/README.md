# Final Project Presentation

This directory contains the LaTeX source files for the IS 499 Final Project presentation.

## Files

- `final_project_draft.tex` - Main LaTeX document for the final project presentation
- `build.sh` - Build script for Unix/Linux/macOS systems
- `build.bat` - Build script for Windows systems
- `README.md` - This file

## Building the Document

### Prerequisites

You need a LaTeX distribution installed on your system:

- **Windows**: MiKTeX or TeX Live
- **macOS**: MacTeX or TeX Live
- **Linux**: TeX Live

### Building on Windows

```cmd
cd docs/presentations
build.bat
```

### Building on Unix/Linux/macOS

```bash
cd docs/presentations
chmod +x build.sh
./build.sh
```

### Manual Building

If the build scripts don't work, you can build manually:

```bash
pdflatex final_project_draft.tex
bibtex final_project_draft
pdflatex final_project_draft.tex
pdflatex final_project_draft.tex
```

## Document Structure

The presentation follows the IS 499 Final Project template requirements:

1. **Cover Page** - Document title, college name, student name, date
2. **Table of Contents** - Automatic generation from sections
3. **Introduction** - Project overview and motivation
4. **Topic Description** - System architecture and research foundation
5. **Problem Description** - Current challenges and impact
6. **Solution Discussion** - Technical approach and implementation
7. **Analysis** - Current status, preliminary results, evaluation framework
8. **References** - Bibliography using APA style

## Status Indicators

The document includes status indicators for sections that need additional data:

- 🔄 **In Progress** - Currently being worked on
- ✅ **Completed** - Finished components
- **\textcolor{red}{[NEEDS MORE DATA]}** - Requires additional data collection
- **\textcolor{red}{[IN PROGRESS]}** - Currently being developed

## Bibliography

The document references the same bibliography file as the project proposal:
`../project_proposal/references.bib`

## Notes

- This is a first draft with placeholders for sections requiring additional data
- The document structure follows the professor's template exactly
- LaTeX formatting matches the existing proposal style
- Status indicators clearly mark what needs more work
