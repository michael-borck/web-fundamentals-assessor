# Installation Guide: Web Fundamentals Assessment Suite

This guide provides detailed instructions for setting up the Web Fundamentals Assessment Suite on your local machine.

## 1. System Prerequisites

Before you begin, ensure your system meets the following prerequisites:

### All Operating Systems:

* **Git:** Required for cloning the repository.
    * **Download:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
    * **Verify Installation:** Open a terminal or command prompt and type `git --version`.
* **Node.js and npm:** Required for `performance_analyser.py` (Lighthouse) and potentially other tools. npm is included with Node.js.
    * **Download (LTS version recommended):** [https://nodejs.org/](https://nodejs.org/)
    * **Verify Installation:** Type `node --version` and `npm --version` in your terminal.
* **Google Chrome or Chromium Browser:** Required by scripts that use Selenium for browser automation (`screenshot.py`, `scrape_chat.py`) and by Lighthouse for performance analysis.
    * **Download Google Chrome:** [https://www.google.com/chrome/](https://www.google.com/chrome/)
    * Ensure it's installed in the default location or accessible via your system's PATH.

### Windows:

* **Python (Recommended: Anaconda Distribution):**
    * **Anaconda (includes Python & Conda):** Provides a robust environment with many scientific packages. Download the Anaconda Individual Edition from [https://www.anaconda.com/products/individual](https://www.anaconda.com/products/individual). (Python 3.8+ is recommended).
    * During installation, it's generally recommended to **not** add Anaconda to your PATH environment variable if the installer advises against it, and instead use Anaconda Navigator or Anaconda Prompt to manage environments and launch tools.
    * **Verify Installation (from Anaconda Prompt):** Type `python --version` and `conda --version`.
* **Alternative (Standard Python):**
    * If not using Anaconda, download Python from [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/). (Python 3.8+ is recommended).
    * **Important:** During installation, ensure you check the box that says **"Add Python to PATH"**.
    * **Verify Installation (from Command Prompt/PowerShell):** Type `python --version` and `pip --version`.

### macOS:

* **Python 3:** macOS usually comes with Python 2.x. You need Python 3.
    * **Recommended:** Install via Homebrew: `brew install python`
    * Or download from [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/). (Python 3.8+ is recommended).
    * **Verify Installation:** Type `python3 --version` and `pip3 --version`.
* **Homebrew (for easier installation of some tools):** [https://brew.sh/](https://brew.sh/)

### Linux:

* **Python 3 & pip3:** Most Linux distributions come with Python 3. If not, install it using your distribution's package manager.
    * Example (Debian/Ubuntu): `sudo apt update && sudo apt install python3 python3-pip python3-venv git`
    * Example (Fedora): `sudo dnf install python3 python3-pip git`
    * **Verify Installation:** Type `python3 --version` and `pip3 --version`.

## 2. Clone the Repository

1.  Open your terminal, Git Bash (Windows), or Anaconda Prompt (Windows).
2.  Navigate to the directory where you want to store the project.
3.  Clone the repository:
    ```bash
    git clone <your-repository-url>
    ```
    (Replace `<your-repository-url>` with the actual URL of the repository).
4.  Change into the cloned directory:
    ```bash
    cd WebFundamentalsAssessor  # Or your chosen repository name
    ```

## 3. Set Up a Python Virtual Environment

A virtual environment isolates project dependencies. This is highly recommended.

### For Anaconda Users (Windows, macOS, Linux):

1.  Open Anaconda Prompt (Windows) or your terminal (macOS/Linux).
2.  Navigate to the project directory (e.g., `WebFundamentalsAssessor`).
3.  Create a new conda environment (e.g., named `webassess_env` with Python 3.9):
    ```bash
    conda create --name webassess_env python=3.9
    ```
    (You can choose a different Python version like 3.8, 3.10, or 3.11 if preferred).
4.  Activate the environment:
    ```bash
    conda activate webassess_env
    ```
    You should see `(webassess_env)` at the beginning of your prompt.

### For Standard Python Users (Windows, macOS, Linux):

1.  Open your terminal or Command Prompt.
2.  Navigate to the project directory (e.g., `WebFundamentalsAssessor`).
3.  Create a virtual environment (e.g., named `.venv`):
    * macOS/Linux:
        ```bash
        python3 -m venv .venv
        ```
    * Windows:
        ```bash
        python -m venv .venv
        ```
4.  Activate the environment:
    * macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    * Windows (Command Prompt):
        ```bash
        .venv\Scripts\activate.bat
        ```
    * Windows (PowerShell):
        ```bash
        .venv\Scripts\Activate.ps1
        ```
        (If script execution is disabled in PowerShell, you might need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first).
    You should see `(.venv)` or your environment name at the beginning of your prompt.

## 4. Install Python Dependencies

Once your virtual environment is activated, install the required Python libraries:

```bash
pip install -r requirements.txt
```
This command reads the `requirements.txt` file (which should be present in the repository) and installs all listed packages (e.g., `selenium`, `requests`, `nltk`, `beautifulsoup4`, etc.).

## 5. Install WebDriver for Selenium

Scripts like `screenshot.py` and `scrape_chat.py` use Selenium to control a web browser. You need to install the correct WebDriver for Google Chrome.

1.  **Check your Google Chrome Version:**
    * Open Chrome, go to `chrome://settings/help`. Note down the version number (e.g., 124.x.x.x).

2.  **Download ChromeDriver:**
    * Go to the official ChromeDriver download page: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) or [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/) (for newer versions).
    * **Crucial:** Download the ChromeDriver version that **matches your Google Chrome browser version**.

3.  **Place ChromeDriver:**
    * Extract the `chromedriver` (or `chromedriver.exe` on Windows) executable from the downloaded zip file.
    * **Recommended:** Place it in a directory that is part of your system's PATH environment variable.
        * **macOS/Linux:** A common location is `/usr/local/bin/`.
        * **Windows:** You can create a folder (e.g., `C:\WebDrivers`) and add this folder to your system's PATH.
    * **Alternative (Simpler for some):** Place the `chromedriver` executable directly in the `scripts/` directory of this project. Some scripts might be configured to look there.

## 6. Install Lighthouse (for Performance Analysis)

The `performance_analyser.py` script uses Lighthouse.

1.  Ensure Node.js and npm are installed (see Prerequisites).
2.  Open your terminal or command prompt (it doesn't need to be the Python virtual environment for this global npm package).
3.  Install Lighthouse globally:
    ```bash
    npm install -g lighthouse
    ```
    If you encounter permission issues on macOS/Linux, you might need `sudo npm install -g lighthouse`.
    The script can also attempt to use `npx lighthouse` if a global installation isn't found, but a global install is generally more reliable.

## 7. NLTK Data Download

The `conversation_analyser.py` script uses the Natural Language Toolkit (NLTK). It requires specific data packages.

* The script will attempt to download the necessary NLTK data (`punkt`, `vader_lexicon`, `punkt_tab`) automatically when it's first run.
* Ensure you have an **internet connection** during the first execution of `conversation_analyser.py`.
* If automatic download fails, you can try downloading them manually in a Python interpreter:
    ```python
    import nltk
    nltk.download('punkt')
    nltk.download('vader_lexicon')
    nltk.download('punkt_tab')
    ```

## 8. Optional: GitHub API Token

For scripts like `deployment_analyser.py` that interact with the GitHub API, providing an API token can prevent rate-limiting issues, especially if you're analysing many repositories.

1.  Generate a Personal Access Token (PAT) on GitHub:
    * Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic).
    * Generate a new token. Give it a descriptive name and select the necessary scopes (e.g., `repo` for accessing repository contents).
2.  Set the token as an environment variable named `GITHUB_TOKEN`:
    * **macOS/Linux (temporary for current session):**
        ```bash
        export GITHUB_TOKEN="your_github_pat_here"
        ```
    * **Windows Command Prompt (temporary for current session):**
        ```bash
        set GITHUB_TOKEN="your_github_pat_here"
        ```
    * **Windows PowerShell (temporary for current session):**
        ```bash
        $env:GITHUB_TOKEN="your_github_pat_here"
        ```
    For a more permanent setup, add this to your shell's profile file (e.g., `.bashrc`, `.zshrc`, or System Environment Variables on Windows).

## 9. Verification

After completing all steps:

1.  Ensure your Python virtual environment is **activated**.
2.  Navigate to the `scripts/` directory.
3.  Try running one of the scripts with its help flag to see if it executes without import errors:
    ```bash
    python accessibility_checker.py -h
    ```
    If this shows the help message for the script, your Python environment and basic dependencies are likely set up correctly.

## 10. Troubleshooting

* **`command not found: python` / `pip` / `git` / `node` / `npm` / `lighthouse`:**
    * The tool is not installed or not in your system's PATH. Revisit the prerequisite installation steps.
    * For Python commands, ensure your virtual environment is activated.
* **`ModuleNotFoundError: No module named 'selenium'` (or other Python library):**
    * Your Python virtual environment might not be activated, or `pip install -r requirements.txt` was not run successfully within the activated environment.
* **Selenium: `WebDriverException` or "chromedriver executable needs to be in PATH":**
    * ChromeDriver is not found or is incompatible. Double-check your Chrome browser version and the downloaded ChromeDriver version. Ensure `chromedriver` is in your PATH or the script's directory.
* **NLTK `LookupError`:**
    * The required NLTK data packages are missing. Ensure an internet connection and try running `conversation_analyser.py` again, or manually download as described in step 7.
* **Permission Errors (npm install -g, file operations):**
    * On macOS/Linux, you might need to use `sudo` for global npm installs.
    * Ensure you have write permissions for the directories where scripts save reports.

## 11. Support

If you encounter issues not covered here, please refer to the main `README.md` or contact [Your Name/Department Contact] for assistance.
