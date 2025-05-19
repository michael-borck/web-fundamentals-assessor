# Marking Workflow: Web Fundamentals Assessment Suite

This document outlines the complete workflow for assessing student web development projects using the Web Fundamentals Assessment Suite.

## Overview

The assessment process consists of three main stages:
1. **Preprocessing** - Organizing student submissions and preparing for analysis
2. **Assessment** - Running automated scripts to evaluate different aspects of student work
3. **Reporting** - Generating and reviewing assessment reports

## Prerequisites

Before starting, ensure you have:
- Completed all installation steps in [INSTALL.md](INSTALL.md)
- Access to student submissions (typically downloaded from an LMS like Blackboard)
- Basic understanding of the rubric criteria in `docs/simplified_rubric.md`

## Stage 1: Preprocessing

### Step 1.1: Organize Student Submissions

1. Create a student folder structure:
   ```
   submissions/
   ├── submissions.csv
   └── [student_id]/
       ├── [repository_files]/
       └── conversations/
   ```

2. For each student submission:
   - Create a folder with the student's ID as its name
   - Extract the student's repository files into this folder
   - Create a `conversations` subfolder for AI conversation documents

3. Create or update `submissions.csv` with the format:
   ```
   student,github,netlify
   student_id1,https://github.com/student1/repo.git,https://student1-site.netlify.app
   ```

### Step 1.2: Extract AI Conversations

The system will extract text from various document formats:

1. For each student, the preprocessing stage will:
   - Scan all document files (PDF, DOCX, TXT, MD) in the student's folder
   - Extract text from PDF and DOCX files
   - Copy existing text/markdown files
   - Place all extracted content in the `conversations` subfolder

2. This is handled automatically by the pipeline via:
   ```bash
   python scripts/gather_conversations.py "[student_dir]/" "[student_dir]/conversations"
   ```

## Stage 2: Assessment

### Step 2.1: Process All Submissions

The main assessment process is orchestrated through:

```bash
python scripts/process_assessments.py submissions/submissions.csv --submissions-folder submissions --manual-folder-name conversations
```

This script:
1. Reads the CSV file with student information
2. For each student:
   - Identifies their repository and conversations folder
   - Runs `main_assessor.py` with appropriate parameters

### Step 2.2: Main Assessment Process

For each student, `main_assessor.py` orchestrates these analysis steps:

1. **Setup**:
   - Creates assessment output directories
   - Prepares AI conversations for analysis
   - Clones the student's Git repository (if URL provided)

2. **Screenshots**:
   - Captures desktop and mobile screenshots of the website

3. **Analysis Tools**:
   - **Accessibility Analysis**: Evaluates semantic HTML usage and WCAG compliance
   - **Code Quality Analysis**: Checks code organization and best practices
   - **Conversation Analysis**: Evaluates AI interaction quality
   - **Deployment Analysis**: Verifies GitHub and Netlify setup
   - **Git Analysis**: Examines commit history and repository organization
   - **Performance Analysis**: Tests website performance metrics
   - **Responsive Analysis**: Checks mobile-first design implementation
   - **Validation**: Verifies HTML/CSS validity

4. **Report Generation**:
   - Aggregates individual tool reports into a final assessment
   - Organizes by rubric criteria
   - Creates a comprehensive Markdown report

## Stage 3: Reporting

### Step 3.1: Extract Results

After assessment, extract standardized results tables:

```bash
python scripts/extract_results.py --all --simplified --ascii --base-dir master_assessment_reports
```

This creates a `results.txt` file in each student's assessment folder, containing scores for each rubric criterion.

### Step 3.2: Adding Total Scores (Optional)

Optionally, calculate and add total scores to assessment reports:

```bash
python scripts/add_total_score.py master_assessment_reports/
```

Or using the shell script:

```bash
./scripts/add_total_score.sh
```

### Step 3.3: Manual Review

Instructors should review the generated reports:

1. Navigate to `master_assessment_reports/[student_id]/`
2. Review `final_assessment/[student_id]_final_assessment_report.md`
3. Examine the `results.txt` file with extracted scores
4. Verify assessment accuracy and add manual scores for criteria not covered by automation
5. Add additional feedback where needed

### Step 3.4: Generate Final Feedback (Optional)

Optionally, use an LLM to generate summary feedback:

```bash
python scripts/get_feedback.py master_assessment_reports/[student_id]/
```

Or for all students:

```bash
./scripts/run_feedback.sh
```

### Step 3.5: Compress Reports (Optional)

To create compressed archives of all assessment reports:

```bash
./scripts/compress_assessment_reports.sh
```

## Complete Pipeline

For convenience, the entire process can be executed with:

```bash
./run_pipeline.sh
```

This script:
1. Runs the conversation extraction process for all students
2. Processes all submissions using the CSV file
3. Optionally extracts results in a standardized format

## Processing Individual Students

To process a single student outside the main pipeline:

```bash
python scripts/main_assessor.py \
  --student_id "[student_id]" \
  --website_folder "submissions/[student_id]/[website_folder]" \
  --manual_conversations_folder "submissions/[student_id]/conversations" \
  --git_repo_url "https://github.com/[username]/[repo].git" \
  --netlify_url "https://[site].netlify.app" \
  --output_base_dir "master_assessment_reports"
```

## Troubleshooting

If issues occur during assessment:

1. Check the `assessment_log.txt` file in the student's output directory
2. Verify that all prerequisites are installed correctly
3. Ensure student submission formats are consistent
4. For script-specific errors, run individual scripts with `-h` to see available options

## Notes for Handling Edge Cases

- **Missing GitHub/Netlify URLs**: If a student does not provide deployment links, use "none" in the CSV file
- **Multiple Repository Folders**: If a student has multiple folders, specify the main one manually
- **Large Files**: Some PDF/DOCX files may take longer to process; increase timeouts if needed
- **Character Encoding Issues**: Use `--encoding` parameter with extraction scripts if text appears corrupted

## Conclusion

This workflow provides a systematic approach to assessing web development assignments, combining automated analysis with instructor review. The goal is to provide consistent, objective feedback while reducing the manual assessment workload.

For technical details on individual scripts, refer to the comments in the script files themselves or run them with the `-h` flag to see available options.