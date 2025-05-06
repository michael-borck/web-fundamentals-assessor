# Web Fundamentals Assessment Suite

## Overview

This repository contains a collection of Python scripts designed to automate and assist in the assessment of student web development projects, specifically tailored for the "Portfolio Fusion" assignment (or similar web fundamentals courses). The toolkit evaluates various aspects of web development, including accessibility, code quality, responsive design, Git usage, AI interaction, deployment, and performance.

These tools aim to provide objective, consistent, and detailed feedback, aligning with common web development best practices and the provided course rubric, thereby streamlining the grading process for lecturers.

## Features

The suite includes the following assessment scripts and utilities:

* **`accessibility_checker.py`**: Analyses HTML files for common accessibility issues based on semantic HTML, ARIA attributes, and other basic checks.
* **`batch_scrape_conversations.py`**: A utility to scrape multiple AI conversations from a list of URLs (e.g., ChatGPT share links) and save them as individual files. Uses `scrape_chat.py` internally.
* **`code_quality_analyser.py`**: Evaluates HTML, CSS, and JavaScript files for code organisation, best practices, and potential issues.
* **`conversation_analyser.py`**: Assesses transcripts of student interactions with AI tools, focusing on prompt engineering, critical evaluation, and depth of engagement.
* **`deployment_analyser.py`**: Checks GitHub repository setup for CI/CD workflows (e.g., GitHub Actions) and analyses Netlify deployment status, SSL, and basic SEO.
* **`extract_urls.py`**: A utility to find and extract all URLs from a given text file or all text files within a specified folder. Useful for identifying AI conversation share links embedded in student submission documents (e.g., README files, Word documents saved as text).
* **`git_analyser.py`**: Examines a Git repository's history, analysing commit frequency, message quality, and repository organisation.
* **`performance_analyser.py`**: Uses Lighthouse (via CLI or npx) to test the performance, accessibility, best practices, and SEO of HTML files.
* **`responsive_analyser.py`**: Analyses CSS and HTML for responsive design features and compares desktop vs. mobile screenshots to assess layout adaptation.
* **`scrape_chat.py`**: A utility script using Selenium to scrape a single conversation from a ChatGPT share link (or similar web-based chat interface) and save it as text or JSON. This is primarily used by `batch_scrape_conversations.py`.
* **`screenshot.py`**: Captures screenshots of web pages at different viewport sizes (desktop, mobile, tablet) using Selenium. It can process local HTML files or crawl a live URL.
* **`validate_web.py`**: Validates HTML and CSS files using the W3C validation services.

## Prerequisites

Before using these tools, ensure you have the following installed:

* **Python 3.8+** and `pip`.
* **Git**: For `git_analyser.py`.
* **Node.js and npm/npx**: Required by `performance_analyser.py` for Lighthouse.
* **Google Chrome or Chromium**: Required by `screenshot.py`, `scrape_chat.py`, `batch_scrape_conversations.py`, and `performance_analyser.py`. Ensure it's in your system's PATH.
* **Web Drivers**:
    * **ChromeDriver**: If using Chrome. Ensure it's compatible with your Chrome version and in your system's PATH. (Refer to `INSTALL.md` for details).

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd WebFundamentalsAssessor  # Or your chosen repository name
    ```

2.  **Create and Activate a Virtual Environment:**
    (Refer to `INSTALL.md` for detailed OS-specific instructions if needed).
    * Using standard `venv`:
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # On Windows: .venv\Scripts\activate
        ```

3.  **Install Python Dependencies:**
    A `requirements.txt` file should be generated and included in this repository. This file should include `selenium`, `requests`, `nltk`, `beautifulsoup4`, `matplotlib`, `pandas`, `numpy`, `cssutils`, `esprima`, `PyYAML`, `chardet`, `validators`, and other necessary packages.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Lighthouse (Optional but Recommended):**
    While `performance_analyser.py` can use `npx`, a global Lighthouse installation is often more reliable:
    ```bash
    npm install -g lighthouse
    ```

5.  **NLTK Data:**
    `conversation_analyser.py` requires NLTK data (`punkt`, `vader_lexicon`, `punkt_tab`). It attempts to download these automatically. Ensure an internet connection on the first run.

6.  **GitHub API Token (Optional):**
    For `deployment_analyser.py`, set a `GITHUB_TOKEN` environment variable to increase API rate limits.

For more detailed setup instructions, especially regarding WebDrivers and OS-specific nuances, please refer to **`INSTALL.md`**.

## Folder Structure

A recommended folder structure for organising student work and assessment outputs:

```
WebFundamentalsAssessor/
├── .gitignore
├── README.md
├── INSTALL.md
├── MARKING_WORKFLOW.md
├── requirements.txt
│
├── scripts/
│   ├── accessibility_checker.py
│   ├── batch_scrape_conversations.py
│   ├── code_quality_analyser.py
│   ├── conversation_analyser.py
│   ├── deployment_analyser.py
│   ├── extract_urls.py
│   ├── git_analyser.py
│   ├── performance_analyser.py
│   ├── responsive_analyser.py
│   ├── scrape_chat.py
│   ├── screenshot.py
│   └── validate_web.py
│
├── student_projects/
│   ├── student_A_portfolio/
│   └── ...
│
├── student_submissions_misc/ # For student READMEs, URL lists etc.
│   ├── student_A_readme.md
│   └── ...
│
├── master_assessment_reports/ # Main output for main_assessor.py (if used)
│   ├── student_A/
│   │   ├── ai_conversations_input/ # Populated by manual copy + batch_scrape
│   │   ├── accessibility_reports/
│   │   ├── code_quality_reports/
│   │   ├── conversation_analysis_reports/
│   │   └── ... (other tool reports)
│   │   └── final_assessment/
│   │       └── student_A_final_assessment_report.md
│   └── student_B/
│       └── ...
└── ...
```

## Usage

Each script can be run individually from the command line. For a comprehensive assessment, a `main_assessor.py` script (if implemented and configured) can orchestrate these tools.

Refer to each script's help for specific arguments: `python scripts/<script_name>.py -h`

**Workflow for AI Conversations:**

1.  **Extract URLs (Optional):** If students provide AI conversation links within documents (e.g., their project's README), use `extract_urls.py`:
    ```bash
    python scripts/extract_urls.py path/to/student_submission_document.md --output temp_chat_urls.txt
    # or for a folder
    python scripts/extract_urls.py path/to/student_submission_folder/ --output temp_chat_urls.txt
    ```
2.  **Batch Scrape Conversations:** Use the output from `extract_urls.py` (or a manually created file of URLs) with `batch_scrape_conversations.py` to download the chat logs:
    ```bash
    python scripts/batch_scrape_conversations.py temp_chat_urls.txt path/to/student_specific/ai_conversations_input_folder/
    ```
    This `ai_conversations_input_folder/` will then be used by `conversation_analyser.py` (often orchestrated by `main_assessor.py`).

**Other Example Individual Script Usages:**

* **Accessibility:**
    ```bash
    python scripts/accessibility_checker.py path/to/student_project_folder/ --output-dir path/to/accessibility_reports/
    ```
* **Git Analysis:**
    ```bash
    python scripts/git_analyser.py path/to/cloned_student_git_repo/ --output path/to/git_reports/
    ```

### Using `main_assessor.py` (Orchestration Script - if implemented)

If a `main_assessor.py` script is implemented (as discussed or provided separately), it would typically take arguments like student ID, paths to the website folder, Git repo URL, Netlify URL, and the prepared AI conversations folder. An example invocation might look like:

```bash
python main_assessor.py \
    --student_id "student_A" \
    --website_folder "student_projects/student_A_portfolio/" \
    --manual_conversations_folder "path/to/student_A_manual_chats/" \
    --chat_scrape_file "student_submissions_misc/student_A_chat_urls.txt" \
    --git_repo_url "[https://github.com/studentA/portfolio](https://github.com/studentA/portfolio)" \
    --netlify_url "[https://studentA-portfolio.netlify.app](https://studentA-portfolio.netlify.app)" \
    --output_base_dir "master_assessment_reports"
```
(This assumes `main_assessor.py` is configured to use the other scripts from the `scripts/` directory and handles the workflow of preparing AI conversations using `batch_scrape_conversations.py` internally if `chat_scrape_file` is provided.)

### Output

Individual scripts generate reports (Markdown, CSV, JSON, images) in their specified output directories. An orchestrating script like `main_assessor.py` aims to create a consolidated report in the student's main output folder.

## Key Dependencies and Setup Notes

* **`extract_urls.py`**: Requires `chardet` (for detecting file encodings) and `validators` (for URL validation).
* **`batch_scrape_conversations.py`**: Relies on `scrape_chat.py` and its dependencies (Selenium, WebDriver).
* **Other dependencies:** `selenium`, `requests`, `nltk`, `beautifulsoup4`, `matplotlib`, `pandas`, `numpy`, `cssutils`, `esprima`, `PyYAML`. Ensure all are installed via `requirements.txt`.

For detailed setup, especially for WebDrivers, refer to `INSTALL.md`.

## Troubleshooting

* **"Command not found"**: Check installation and PATH for Python, pip, git, node, npm, lighthouse.
* **`ModuleNotFoundError`**: Ensure virtual environment is active and `requirements.txt` installed.
* **Selenium/WebDriver Issues**: Match ChromeDriver to Chrome version; ensure it's in PATH.
* **NLTK `LookupError`**: Run relevant script with internet access for first-time data download.

## License

MIT License
