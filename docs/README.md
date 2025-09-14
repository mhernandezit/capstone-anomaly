# Documentation

This directory contains all documentation for the BGP Failure Detection capstone project.

## 📁 Structure

```
docs/
├── research/           # Research foundation and references
│   ├── references.md   # Academic literature (APA format)
│   └── proposals/      # Project proposals and planning
├── design/            # System architecture and design
│   ├── bgp_anomaly_uml.py           # Structural UML (system flow)
│   ├── bgp_anomaly_uml.gv.png       # System architecture diagram
│   ├── bgp_action_specification.py  # Action specification UML
│   ├── bgp_action_specification.gv.png # Behavioral model & use cases
│   ├── bgp_usecase_details.gv.png   # Detailed scenario flows
│   └── README.md                    # Design documentation guide
├── development/       # Development documentation
│   ├── program_alignment.md  # Course outcome mapping
│   ├── thesis.md            # Thesis statement
│   ├── evaulation_plan.md   # Testing and evaluation plan
│   └── proposal.md          # Project proposal
├── papers/            # PDF copies of referenced papers
├── presentations/     # Slides and presentation materials
└── README.md         # This file
```

## 📚 Quick Access

### Essential Documents
- **[References](research/references.md)** - Core academic literature
- **[System Architecture](design/bgp_anomaly_uml.gv.png)** - Structural flow diagram
- **[Behavioral Model](design/bgp_action_specification.gv.png)** - Use cases & actions
- **[Design Guide](design/README.md)** - Complete design documentation
- **[Project Proposal](development/proposal.md)** - Problem statement and approach
- **[Program Alignment](development/program_alignment.md)** - Course outcome mapping

### For Advisors/Review
- **Research Foundation:** [references.md](research/references.md) - 9 peer-reviewed sources
- **Technical Design:** [design/](design/) - UML diagrams and architecture
- **Academic Integration:** [program_alignment.md](development/program_alignment.md) - Maps to IS curriculum

## 📖 Documentation Standards

- **Academic References:** APA 7th edition format
- **Technical Diagrams:** PlantUML/Graphviz source + rendered images
- **Markdown:** GitHub-flavored markdown for all text documents
- **File Naming:** Snake_case for technical files, kebab-case for documents

## 🔄 Maintenance

- Update references.md when adding new literature
- Regenerate UML diagrams when system architecture changes
- Weekly updates to development docs during active sprints
- Archive old versions in git rather than keeping multiple files
