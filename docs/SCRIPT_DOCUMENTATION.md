# Script Documentation

This document provides an overview of each script in the Web Fundamentals Assessment Suite, explaining its purpose, usage, and parameters.

## Core Assessment Scripts

### `main_assessor.py`

**Purpose**: Orchestrates the entire assessment process for a single student.

**Usage**:
```bash
python main_assessor.py --student_id "student_id" --website_folder "/path/to/student/website" \
  --manual_conversations_folder "/path/to/conversations" --git_repo_url "https://github.com/user/repo" \
  --netlify_url "https://site.netlify.app" --output_base_dir "master_assessment_reports"
```

**Key Parameters**:
- `--student_id`: Identifier for the student
- `--website_folder`: Path to student's website files
- `--manual_conversations_folder`: Path to AI conversation files
- `--git_repo_url`: GitHub repository URL
- `--netlify_url`: Netlify deployment URL
- `--output_base_dir`: Base directory for assessment outputs
- `--rubric_file`: Path to rubric file (default: blackboard_rubric.md)

### `process_assessments.py`

**Purpose**: Batch processes assessments for all students listed in a CSV file.

**Usage**:
```bash
python process_assessments.py submissions.csv --submissions-folder submissions --manual-folder-name conversations
```

**Key Parameters**:
- `csv_file`: Path to CSV file with student information
- `--main-script`: Path to main_assessor.py
- `--manual-folder-name`: Name of conversations subfolder
- `--submissions-folder`: Path to submissions root directory
- `--dry-run`: Print commands without executing

## Preprocessing Scripts

### `gather_conversations.py`

**Purpose**: Extracts text from student submission documents (PDF, DOCX, MD, TXT).

**Usage**:
```bash
python gather_conversations.py input_dir output_dir
```

**Key Parameters**:
- `input_dir`: Root folder to scan
- `output_dir`: Folder to save extracted texts

### `extract_urls.py`

**Purpose**: Extracts URLs from text files.

**Usage**:
```bash
python extract_urls.py input_path --output output.txt
```

**Key Parameters**:
- `input_path`: Path to file or directory to scan
- `--output`: Output file for extracted URLs

### `extract_chatgpt_links.py`

**Purpose**: Specifically extracts ChatGPT conversation links.

**Usage**:
```bash
python extract_chatgpt_links.py input_file --output links.txt
```

**Key Parameters**:
- `input_file`: Input text file
- `--output`: Output file for links

### `batch_scrape_conversations.py`

**Purpose**: Scrapes AI conversation content from URLs.

**Usage**:
```bash
python batch_scrape_conversations.py urls.txt output_dir
```

**Key Parameters**:
- `urls_file`: File containing URLs (one per line)
- `output_dir`: Directory to save scraped conversations

## Analysis Scripts

### `accessibility_checker.py`

**Purpose**: Analyzes HTML for accessibility compliance.

**Usage**:
```bash
python accessibility_checker.py website_folder --output-dir reports
```

**Key Parameters**:
- `website_folder`: Path to website files
- `--output-dir`: Directory for reports
- `--format`: Output format (markdown, json, both)

### `code_quality_analyser.py`

**Purpose**: Evaluates code organization and best practices.

**Usage**:
```bash
python code_quality_analyser.py website_folder --output reports
```

**Key Parameters**:
- `website_folder`: Path to website files
- `--output`: Directory for reports

### `conversation_analyser.py`

**Purpose**: Assesses AI interaction quality.

**Usage**:
```bash
python conversation_analyser.py conversations_dir --output_dir reports
```

**Key Parameters**:
- `conversations_dir`: Directory with conversation files
- `--output_dir`: Directory for reports

### `deployment_analyser.py`

**Purpose**: Checks GitHub and Netlify deployment.

**Usage**:
```bash
python deployment_analyser.py github_url netlify_url --output reports
```

**Key Parameters**:
- `github_url`: GitHub repository URL
- `netlify_url`: Netlify deployment URL
- `--output`: Directory for reports

### `git_analyser.py`

**Purpose**: Analyzes Git repository history.

**Usage**:
```bash
python git_analyser.py repo_path --output reports
```

**Key Parameters**:
- `repo_path`: Path to Git repository
- `--output`: Directory for reports

### `performance_analyser.py`

**Purpose**: Runs Lighthouse performance tests.

**Usage**:
```bash
python performance_analyser.py --url https://site.netlify.app --output reports
```

**Key Parameters**:
- `--url`: Website URL to test
- `--output`: Directory for reports
- `--chrome-path`: Path to Chrome executable

### `responsive_analyser.py`

**Purpose**: Evaluates responsive design implementation.

**Usage**:
```bash
python responsive_analyser.py website_folder --screenshots screenshots --output reports
```

**Key Parameters**:
- `website_folder`: Path to website files
- `--screenshots`: Directory with website screenshots
- `--output`: Directory for reports
- `--format`: Output format (markdown, json, both)

### `screenshot.py`

**Purpose**: Captures website screenshots at different viewport sizes.

**Usage**:
```bash
python screenshot.py --directory website_folder --output screenshots
```

**Key Parameters**:
- `--directory`: Website directory
- `--output`: Directory for screenshots
- `--url`: URL to capture (instead of local files)

### `validate_web.py`

**Purpose**: Validates HTML and CSS files.

**Usage**:
```bash
python validate_web.py website_folder --output validation.md --summary summary.md --rubric rubric.md
```

**Key Parameters**:
- `website_folder`: Path to website files
- `--output`: Path for detailed report
- `--summary`: Path for summary report
- `--rubric`: Path for rubric-aligned report

## Post-processing Scripts

### `extract_results.py`

**Purpose**: Extracts assessment results into standardized tables.

**Usage**:
```bash
python extract_results.py --all --simplified --ascii --base-dir master_assessment_reports
```

**Key Parameters**:
- `--all`: Process all students
- `student_id`: Process specific student
- `--simplified`: Generate simplified table
- `--ascii`: Use ASCII formatting
- `--base-dir`: Base directory with assessment reports

### `add_total_score.py`

**Purpose**: Calculates and adds total scores to result files.

**Usage**:
```bash
python add_total_score.py master_assessment_reports/
```

**Key Parameters**:
- `reports_base_dir`: Base directory with assessment reports

### `get_feedback.py`

**Purpose**: Generates summary feedback using LLM.

**Usage**:
```bash
python get_feedback.py assessment_dir
```

**Key Parameters**:
- `assessment_dir`: Student assessment directory

### `compress_assessment_reports.sh`

**Purpose**: Creates ZIP archives of assessment reports.

**Usage**:
```bash
./compress_assessment_reports.sh
```

## Utility Scripts

### `list_repos.py`

**Purpose**: Lists all repositories from submissions.csv.

**Usage**:
```bash
python list_repos.py submissions.csv
```

**Key Parameters**:
- `csv_file`: Path to CSV file

### `enhanced_frequency_analysis.py`

**Purpose**: Analyzes codebase for patterns and feature usage.

**Usage**:
```bash
python enhanced_frequency_analysis.py website_folder
```

**Key Parameters**:
- `website_folder`: Path to website files

## Pipeline Script

### `run_pipeline.sh`

**Purpose**: Runs the complete assessment pipeline.

**Usage**:
```bash
./run_pipeline.sh
```

**Configuration variables** (edit in script):
- `SUBMISSIONS_DIR`: Directory of student submissions
- `CONVERSATIONS_OUTDIR`: Output directory for conversations
- `CSV_FILE`: CSV file with student information
- `MAIN_SCRIPT`: Path to main_assessor.py
- `MANUAL_FOLDER_NAME`: Name of conversations folder
- `RESULTS_BASE_DIR`: Base directory for assessment reports