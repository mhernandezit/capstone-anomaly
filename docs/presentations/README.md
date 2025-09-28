# Final Project Presentation

This directory contains the LaTeX source files for the final project presentation.

## Files

- `final_project_draft.tex` - Main LaTeX document for the final project presentation
- `system_architecture.png` - System architecture UML diagram
- `action_specification.png` - Action specification UML diagram  
- `usecase_details.png` - Use case details UML diagram
- `README.md` - This file

## Building the Document

### Prerequisites

You need a LaTeX distribution installed on your system:

- **Windows**: MiKTeX or TeX Live
- **macOS**: MacTeX or TeX Live
- **Linux**: TeX Live

### Building on Windows (PowerShell)

```powershell
cd docs/presentations
$env:PATH += ";C:\texlive\2025\bin\windows"
pdflatex final_project_draft.tex
```

### Building on Unix/Linux/macOS

```bash
cd docs/presentations
pdflatex final_project_draft.tex
```

### Manual Building

The document uses a manual bibliography (no BibTeX required):

```bash
pdflatex final_project_draft.tex
```

## Document Structure

The presentation follows the required final project template structure:

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

- **In Progress** - Currently being worked on
- **Completed** - Finished components
- **\textcolor{red}{[NEEDS MORE DATA]}** - Requires additional data collection
- **\textcolor{red}{[IN PROGRESS]}** - Currently being developed

## Bibliography

The document includes a manual bibliography with APA-style citations and hyperlinks to research papers.

## Notes

- This is the final presentation document following the required template structure
- LaTeX formatting uses academic language aligned with Mohammed et al. NOC framework
- UML diagrams are integrated for system architecture and use case visualization
- Document focuses on multi-modal network anomaly detection and correlation analysis
