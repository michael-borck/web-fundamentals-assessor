# Folder Structure Documentation

This document outlines the folder structure used in the Web Fundamentals Assessment Suite, explaining the purpose and contents of each directory.

## Top-Level Structure

```
web-fundamentals-assessor/
├── docs/                       # Documentation files
├── master_assessment_reports/  # Output of assessment process
├── scripts/                    # Assessment scripts
├── submissions/                # Student submission files
├── INSTALL.md                  # Installation instructions
├── LICENSE.md                  # License information
├── MARKING_WORKFLOW.md         # Marking procedure documentation
├── README.md                   # Project overview
├── requirements.txt            # Python dependencies
└── run_pipeline.sh             # Main pipeline script
```

## Documentation Files

```
docs/
├── blackboard_rubric.md        # Detailed assessment rubric
├── FOLDER_STRUCTURE.md         # This file
├── prompt.txt                  # LLM prompts for feedback
├── SCRIPT_DOCUMENTATION.md     # Documentation for each script
└── simplified_rubric.md        # Simplified version of the rubric
```

## Submission Structure

Each student submission is organized as follows:

```
submissions/
├── submissions.csv             # CSV with student IDs and URLs
└── [student_id]/               # Individual student submissions
    ├── [repository_files]/     # Website files extracted from submission
    │   ├── index.html
    │   ├── css/
    │   ├── js/
    │   ├── assets/
    │   └── ...
    └── conversations/          # AI conversation files
        ├── conversation1.txt
        ├── conversation2.txt
        └── ...
```

Where:
- `student_id` is a unique identifier for each student
- `submissions.csv` contains three columns: student, github, netlify
- `repository_files` contains the student's website project files
- `conversations` contains extracted AI conversation text

## Assessment Reports Structure

The output of the assessment process is organized as follows:

```
master_assessment_reports/
└── [student_id]/                       # Individual student assessment
    ├── accessibility_reports/          # Accessibility analysis
    │   ├── accessibility_summary.md
    │   └── accessibility_details.json
    ├── ai_conversations_input/         # Processed conversation files
    │   ├── conversation1.txt
    │   └── ...
    ├── code_quality_reports/           # Code quality analysis
    │   ├── code_quality_detailed.md
    │   └── code_quality_rubric.md
    ├── conversation_analysis_reports/  # AI interaction analysis
    │   ├── conversation_metrics.json
    │   └── summary_report.md
    ├── deployment_reports/             # Deployment analysis
    │   └── deployment_analysis.md
    ├── final_assessment/               # Final assessment report
    │   └── [student_id]_final_assessment_report.md
    ├── git_reports/                    # Git repository analysis
    │   └── git_analysis_summary.md
    ├── performance_reports/            # Lighthouse performance analysis
    │   ├── lighthouse_report.json
    │   └── performance_report.md
    ├── responsive_reports/             # Responsive design analysis
    │   └── responsive_analysis.md
    ├── screenshots/                    # Website screenshots
    │   ├── desktop/
    │   │   └── index.png
    │   └── mobile/
    │       └── index.png
    ├── validation_reports/             # HTML/CSS validation
    │   ├── validation_detailed_report.md
    │   ├── validation_summary.md
    │   └── validation_rubric.md
    ├── assessment_log.txt              # Log of assessment process
    └── results.txt                     # Extracted assessment results
```

## Scripts Structure

The assessment scripts are organized by function:

```
scripts/
├── preprocessing/             # Data preparation scripts
│   ├── gather_conversations.py
│   ├── extract_urls.py
│   ├── extract_chatgpt_links.py
│   ├── batch_scrape_conversations.py
│   ├── gather_files.py
│   └── gather_files.sh
├── analysis/                  # Core analysis scripts
│   ├── accessibility_checker.py
│   ├── code_quality_analyser.py
│   ├── conversation_analyser.py
│   ├── deployment_analyser.py
│   ├── git_analyser.py
│   ├── performance_analyser.py
│   ├── responsive_analyser.py
│   ├── screenshot.py
│   └── validate_web.py
├── reporting/                 # Report generation scripts
│   ├── extract_results.py
│   ├── add_total_score.py
│   ├── add_total_score.sh
│   ├── get_feedback.py
│   └── complete_summary_report.py
├── utilities/                 # Helper scripts
│   ├── list_repos.py
│   └── enhanced_frequency_analysis.py
├── main_assessor.py           # Main assessment coordinator
└── process_assessments.py     # Batch assessment processor
```

Note: In the actual repository, scripts might not be organized in subdirectories as shown above, but are logically grouped here for clarity.

## Data Flow

The assessment process follows this data flow:

1. **Input**: Student submissions in `submissions/[student_id]/`
2. **Preprocessing**: Convert documents to text in `submissions/[student_id]/conversations/`
3. **Assessment**: Run analyses on website files and conversations
4. **Output**: Generate reports in `master_assessment_reports/[student_id]/`
5. **Results Extraction**: Create standardized results in `master_assessment_reports/[student_id]/results.txt`

## Recommended Organization for New Files

When adding new files to the project:

- **New scripts**: Add to the `scripts/` directory with a descriptive name
- **Documentation**: Add to the `docs/` directory
- **Configuration**: Add to the project root or a new `config/` directory
- **Templates**: Create a `templates/` directory for report templates

## Notes on File Naming

- Use snake_case for Python scripts and directories
- Use TitleCase.md for documentation files
- Prefix scripts with their function (e.g., `extract_`, `analyse_`, `generate_`)
- Suffix reports with their format (e.g., `_report.md`, `_summary.json`)