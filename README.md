# Web Fundamentals Assessment Suite

## Overview

This repository contains a collection of Python scripts designed to automate and assist in the assessment of student web development projects. The toolkit evaluates various aspects of web development, including accessibility, code quality, responsive design, Git usage, AI interaction, deployment, and performance.

These tools aim to provide objective, consistent, and detailed feedback, aligning with common web development best practices and the provided course rubric, thereby streamlining the grading process for instructors.

## Quick Start

For a complete end-to-end workflow, run:

```bash
./run_pipeline.sh
```

This script will process student submissions, extract AI conversations, run assessments, and generate reports. See [MARKING_WORKFLOW.md](MARKING_WORKFLOW.md) for step-by-step instructions.

## Assessment Pipeline

The assessment process follows these main steps:

1. **Preprocessing**:
   - Extract text from student submissions (PDF, DOCX, MD, TXT)
   - Gather AI conversations from different sources
   - Identify GitHub repositories and Netlify deployments

2. **Assessment**:
   - Run various analysis scripts for different assessment criteria 
   - Generate detailed reports for each aspect

3. **Reporting**:
   - Collate individual reports into final assessment documents
   - Extract final scores in a standardized format
   - Generate feedback summaries

## Features

The suite includes the following assessment scripts and utilities:

* **`accessibility_checker.py`**: Analyzes HTML files for common accessibility issues based on semantic HTML, ARIA attributes, and other basic checks.
* **`batch_scrape_conversations.py`**: A utility to scrape multiple AI conversations from a list of URLs (e.g., ChatGPT share links) and save them as individual files.
* **`code_quality_analyser.py`**: Evaluates HTML, CSS, and JavaScript files for code organization, best practices, and potential issues.
* **`conversation_analyser.py`**: Assesses transcripts of student interactions with AI tools, focusing on prompt engineering, critical evaluation, and depth of engagement.
* **`deployment_analyser.py`**: Checks GitHub repository setup for CI/CD workflows and analyzes Netlify deployment status, SSL, and basic SEO.
* **`extract_links.py`**, **`extract_urls.py`**, **`extract_chatgpt_links.py`**: Utilities to find and extract various types of URLs from student submission documents.
* **`git_analyser.py`**: Examines a Git repository's history, analyzing commit frequency, message quality, and repository organization.
* **`main_assessor.py`**: Orchestrates the entire assessment process for a single student.
* **`performance_analyser.py`**: Uses Lighthouse to test the performance, accessibility, best practices, and SEO of HTML files.
* **`process_assessments.py`**: Processes the assessment for all students listed in a CSV file.
* **`responsive_analyser.py`**: Analyzes CSS and HTML for responsive design features and compares desktop vs. mobile screenshots to assess layout adaptation.
* **`screenshot.py`**: Captures screenshots of web pages at different viewport sizes using Selenium.
* **`validate_web.py`**: Validates HTML and CSS files using the W3C validation services.

## Prerequisites

Before using these tools, ensure you have the following installed:

* **Python 3.8+** and `pip`
* **Git**: For `git_analyser.py`
* **Node.js and npm/npx**: Required by `performance_analyser.py` for Lighthouse
* **Google Chrome or Chromium**: Required by `screenshot.py`, `scrape_chat.py`, and `performance_analyser.py`
* **Web Drivers**: ChromeDriver compatible with your Chrome version

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Directory Structure

```
web-fundamentals-assessor/
├── INSTALL.md                 # Detailed installation instructions
├── LICENSE.md                 # License information
├── MARKING_WORKFLOW.md        # Step-by-step marking procedure
├── README.md                  # This file
├── docs/                      # Documentation files
│   ├── blackboard_rubric.md   # Detailed marking rubric
│   ├── prompt.txt             # LLM prompts for feedback
│   └── simplified_rubric.md   # Simplified rubric version
├── master_assessment_reports/ # Output directory for all student assessments
├── requirements.txt           # Python dependencies
├── run_pipeline.sh            # Main pipeline execution script
├── scripts/                   # All assessment scripts
│   ├── accessibility_checker.py
│   ├── add_total_score.py
│   ├── add_total_score.sh
│   └── ... (and other scripts)
└── submissions/               # Directory containing student submissions
    ├── submissions.csv        # CSV with student IDs and URLs 
    └── [student_id]/          # Individual student submission folders
```

## Setup and Usage

### Basic Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-fundamentals-assessor.git
   cd web-fundamentals-assessor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Organize student submissions in the `submissions/` directory

4. Create a CSV file at `submissions/submissions.csv` with the following format:
   ```
   student,github,netlify
   student_id1,https://github.com/student1/repo.git,https://student1-site.netlify.app
   student_id2,https://github.com/student2/repo.git,https://student2-site.netlify.app
   ```

### Running the Assessment Pipeline

Execute the main pipeline:
```bash
./run_pipeline.sh
```

This will:
1. Process all student folders in `submissions/`
2. Extract AI conversations from documents
3. Run all assessment scripts
4. Generate reports in `master_assessment_reports/`

### Running Individual Scripts

Each script can be run independently. For example:

```bash
# Run accessibility check on a specific student project
python scripts/accessibility_checker.py submissions/student_id/website_folder --output-dir output/student_id/accessibility_reports

# Extract URLs from a specific document
python scripts/extract_urls.py submissions/student_id/document.pdf --output links.txt

# Analyze Git repository
python scripts/git_analyser.py /path/to/git/repo --output output/student_id/git_reports
```

For more detailed instructions on each stage of the assessment workflow, refer to [MARKING_WORKFLOW.md](MARKING_WORKFLOW.md).

## Customization

You can customize the assessment process by:

1. Modifying the rubric in `docs/simplified_rubric.md` or `docs/blackboard_rubric.md`
2. Adjusting threshold values in individual assessment scripts
3. Adding new assessment scripts and integrating them into `main_assessor.py`

## License

MIT License