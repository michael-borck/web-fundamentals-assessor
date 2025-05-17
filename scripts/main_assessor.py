import os
import argparse
import subprocess
import shutil
import re
import glob
from datetime import datetime

# --- Configuration ---
SCRIPTS_DIR = "scripts"  # Assuming your scripts are in a 'scripts' subdirectory

REPORT_MAPPING = {
    "Overall Site Interactivity and Performance": ("performance_analyser.py", "performance_report.md"),
    "Responsive Design (Mobile-First)": ("responsive_analyser.py", "responsive_analysis.md"),
    "Effective Use of Flexbox/Grid": ("responsive_analyser.py", "responsive_analysis.md"),
    "Accessibility & Semantic HTML (WCAG, Semantic Tags, ARIA, Navigation)": ("accessibility_checker.py", "accessibility_summary.md"),
    "AI Integration & Critical Interaction": ("conversation_analyser.py", "summary_report.md"),
    "Code Organisation and Documentation (Code Quality)": ("code_quality_analyser.py", "code_quality_rubric.md"),
    "Code Quality (Validation)": ("validate_web.py", "validation_rubric.md"),
    "Version Control (Commit Frequency, Messages, Repository Organisation)": ("git_analyser.py", "git_analysis_summary.md"),
    "Deployment (GitHub and Netlify)": ("deployment_analyser.py", "deployment_analysis.md"),
}

RUBRIC_SECTIONS_ORDER = [
    "Final Product & Technical Functionality",
    "Design & Responsiveness",
    "Accessibility & Semantic HTML",
    "AI Integration & Critical Interaction",
    "Development Process",
    "Version Control",
    "Deployment",
]

TOOL_TO_RUBRIC_CATEGORY = {
    "performance_analyser.py": "Final Product & Technical Functionality",
    "responsive_analyser.py": "Design & Responsiveness",
    "accessibility_checker.py": "Accessibility & Semantic HTML",
    "conversation_analyser.py": "AI Integration & Critical Interaction",
    "code_quality_analyser.py": "Development Process",
    "validate_web.py": "Development Process",
    "git_analyser.py": "Version Control",
    "deployment_analyser.py": "Deployment",
}


def setup_directories(output_base_dir, student_id):
    """Creates the necessary directory structure for the student's assessment."""
    student_main_output_dir = os.path.join(output_base_dir, student_id)
    os.makedirs(student_main_output_dir, exist_ok=True)

    dirs_to_create = {
        "accessibility_reports": os.path.join(student_main_output_dir, "accessibility_reports"),
        "code_quality_reports": os.path.join(student_main_output_dir, "code_quality_reports"),
        "conversation_input_dir": os.path.join(student_main_output_dir, "ai_conversations_input"), # Consolidated input
        "conversation_analysis_reports": os.path.join(student_main_output_dir, "conversation_analysis_reports"), # Output of analyser
        "deployment_reports": os.path.join(student_main_output_dir, "deployment_reports"),
        "git_reports": os.path.join(student_main_output_dir, "git_reports"),
        "performance_reports": os.path.join(student_main_output_dir, "performance_reports"),
        "responsive_reports": os.path.join(student_main_output_dir, "responsive_reports"),
        "screenshot_output": os.path.join(student_main_output_dir, "screenshots"),
        "validation_reports": os.path.join(student_main_output_dir, "validation_reports"),
        # "scraped_chats_output" is now handled by conversation_input_dir
        "temp_git_repo": os.path.join(student_main_output_dir, "temp_git_repo"),
        "final_report_dir": os.path.join(student_main_output_dir, "final_assessment")
    }

    for dir_path in dirs_to_create.values():
        os.makedirs(dir_path, exist_ok=True)

    print(f"Output directories created under: {student_main_output_dir}")
    return student_main_output_dir, dirs_to_create

def run_script(command_parts, tool_name, student_main_output_dir, log_file_path):
    """Runs a script using subprocess and logs its output."""
    print(f"\n--- Running {tool_name} ---")
    # Ensure the first element (python interpreter) is correctly identified
    # This check might be overly cautious depending on your environment setup
    # and how scripts are intended to be run. If scripts are directly executable,
    # 'python' might not be needed. Assuming they need 'python' for safety.
    if command_parts and command_parts[0].lower() not in ['python', 'python3'] and not os.path.basename(command_parts[0]).lower().startswith('python'):
        # Check if the script itself is the first argument and exists
        if len(command_parts) > 0 and os.path.isfile(os.path.join(SCRIPTS_DIR, command_parts[0])):
             command_parts.insert(0, 'python') # Prepend python if script path is first

    print(f"Command: {' '.join(command_parts)}")

    with open(log_file_path, 'a', encoding='utf-8') as log_f:
        log_f.write(f"\n--- Running {tool_name} ---\n")
        log_f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        log_f.write(f"Command: {' '.join(command_parts)}\n")
        try:
            # Use shell=True cautiously, only if necessary for command execution
            # Generally, prefer shell=False for security and portability
            # Assuming simple commands that don't require shell=True
            process = subprocess.run(command_parts, cwd=os.getcwd(), capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')

            log_f.write("Stdout:\n")
            log_f.write(process.stdout + "\n")
            log_f.write("Stderr:\n")
            log_f.write(process.stderr + "\n")

            if process.returncode == 0:
                print(f"{tool_name} completed successfully.")
                log_f.write(f"{tool_name} completed successfully.\n")
                return True
            else:
                print(f"Error running {tool_name}. Return code: {process.returncode}")
                # Print a snippet of stderr to console, but write full to log
                print(f"Stderr (snippet):\n{process.stderr[:500]}...") # Print first 500 chars of stderr
                log_f.write(f"Error running {tool_name}. Return code: {process.returncode}\n")
                log_f.write(f"Full Stderr:\n{process.stderr}\n")
                return False
        except FileNotFoundError:
            error_msg = f"Error: The script for {tool_name} (e.g., '{command_parts[1] if len(command_parts) > 1 else command_parts[0]}') or the Python interpreter was not found. Ensure SCRIPTS_DIR is correct and scripts are present, and Python is in PATH."
            print(error_msg)
            log_f.write(error_msg + "\n")
            return False
        except Exception as e:
            error_msg = f"An unexpected error occurred while running {tool_name}: {e}"
            print(error_msg)
            log_f.write(error_msg + "\n")
            return False

def prepare_ai_conversations_with_walk(manual_conversations_folder_path, chat_scrape_file_path, target_input_dir, log_file_path, headless_scraping=True):
    """
    Preparses the AI conversation input directory by:
    1. Copying manually provided files, including traversing subdirectories.
    2. Running batch_scrape_conversations.py if a URL file is provided.
    """
    os.makedirs(target_input_dir, exist_ok=True)
    print(f"\n--- Preparing AI Conversations in {target_input_dir} ---")

    # 1. Copy manually provided conversation files (now with directory traversal)
    if manual_conversations_folder_path and os.path.isdir(manual_conversations_folder_path):
        print(f"Copying manually provided conversations from: {manual_conversations_folder_path} (including subdirectories)")
        copied_count = 0
        skipped_count = 0
        # Use os.walk to traverse the directory tree
        for root, _, files in os.walk(manual_conversations_folder_path):
            for item in files:
                source_item_path = os.path.join(root, item)
                # Check if it's a file (os.walk only yields files here, but good practice)
                # and has a supported extension
                if os.path.isfile(source_item_path) and item.lower().endswith(('.txt', '.md')):
                    # Construct the destination path, maintaining subdirectory structure if desired,
                    # but for this use case, we'll copy all to the single target_input_dir
                    destination_item_path = os.path.join(target_input_dir, item)

                    # Optional: Add logic to handle potential filename conflicts
                    # If multiple files with the same name exist in different subdirectories,
                    # this current code will overwrite. A more robust solution might rename
                    # the file or place it in a subdirectory within target_input_dir.
                    # For this example, we'll keep the simple overwrite behavior.

                    try:
                        shutil.copy2(source_item_path, destination_item_path)
                        print(f"Copied {source_item_path} to {destination_item_path}")
                        copied_count += 1
                    except Exception as e:
                        copy_error_msg = f"Error copying {source_item_path} to {destination_item_path}: {e}"
                        print(copy_error_msg)
                        with open(log_file_path, 'a', encoding='utf-8') as log_f:
                            log_f.write(copy_error_msg + "\n")
                else:
                    skipped_count += 1
                    # print(f"Skipping {source_item_path}: not a supported file type") # Can be noisy

        print(f"Finished copying manual conversations. {copied_count} files copied, {skipped_count} files skipped.")
    else:
        print("No valid manual conversations folder provided or folder does not exist. Skipping manual copy.")

    # 2. Run batch scraping if URL file is provided (This part remains the same)
    if chat_scrape_file_path and os.path.exists(chat_scrape_file_path):
        print(f"Batch scraping AI Conversations using URL file: {chat_scrape_file_path}")

        batch_scrape_script_path = os.path.join("scripts", 'batch_scrape_conversations.py') # Assuming SCRIPTS_DIR is defined or use relative path
        if not os.path.exists(batch_scrape_script_path):
            missing_script_msg = f"Error: batch_scrape_conversations.py not found in scripts directory. Skipping scraping."
            print(missing_script_msg)
            with open(log_file_path, 'a', encoding='utf-8') as log_f:
                log_f.write(missing_script_msg + "\n")
        else:
            cmd = ['python', os.path.abspath(batch_scrape_script_path),
                   os.path.abspath(chat_scrape_file_path),
                   os.path.abspath(target_input_dir)]
            if not headless_scraping:
                cmd.append('--no-headless')

            # Determine where to run the script from (usually the directory of the script itself)
            # Or just use os.getcwd() if scripts are expected to handle paths correctly
            script_cwd = os.path.dirname(batch_scrape_script_path) if os.path.exists(batch_scrape_script_path) else os.getcwd()

            # Assuming run_script is defined elsewhere and handles subprocess execution and logging
            # Replace this with your actual run_script call or implementation
            print(f"Simulating run_script call for batch_scrape_conversations.py with command: {' '.join(cmd)}")
            # Example of how you might call run_script if it were provided:
            # if run_script(cmd, "batch_scrape_conversations.py", script_cwd, log_file_path):
            #     print("Batch AI conversation scraping process completed or attempted.")
            #     failed_log = os.path.join(target_input_dir, "failed_scrapes.log")
            #     if os.path.exists(failed_log):
            #         try:
            #             with open(failed_log, 'r', encoding='utf-8') as f_err:
            #                 failed_urls = f_err.read().strip()
            #             if failed_urls:
            #                 warning_msg = f"Warning: Some URLs failed to scrape. See {failed_log}"
            #                 print(warning_msg)
            #                 with open(log_file_path, 'a', encoding='utf-8') as main_log:
            #                     main_log.write(warning_msg + "\nFailed URLs:\n" + failed_urls + "\n")
            #         except Exception as e:
            #             print(f"Warning: Could not read failed scrapes log {failed_log}: {e}")
            # else:
            #     critical_msg = "CRITICAL: Batch AI conversation scraping script failed to execute."
            #     print(critical_msg)
            #     with open(log_file_path, 'a', encoding='utf-8') as main_log:
            #         main_log.write(critical_msg + "\n")

    else:
        print("No chat scrape file provided or file does not exist. Skipping batch scraping.")

    print("AI Conversation preparation finished.")

def clone_git_repository(repo_url, clone_target_dir, log_file_path):
    """Clones the specified Git repository."""
    # Check if the directory exists and looks like a cloned repo
    if os.path.exists(os.path.join(clone_target_dir, '.git')):
        print(f"Git repository folder {clone_target_dir} already exists and contains a .git directory. Assuming cloned. Skipping clone.")
        # Optional: Could add logic here to pull latest changes if desired
        return True
    elif os.path.exists(clone_target_dir) and os.listdir(clone_target_dir):
         print(f"Warning: Git repository folder {clone_target_dir} exists but does not seem to be a valid repository (no .git). Attempting to clean and re-clone.")
         try:
             shutil.rmtree(clone_target_dir)
             os.makedirs(clone_target_dir, exist_ok=True)
         except Exception as e:
             error_msg = f"Error cleaning existing git directory {clone_target_dir}: {e}"
             print(error_msg)
             with open(log_file_path, 'a', encoding='utf-8') as log_f:
                log_f.write(error_msg + "\n")
             return False # Cannot proceed if cleanup fails

    elif not os.path.exists(os.path.dirname(clone_target_dir)):
        os.makedirs(os.path.dirname(clone_target_dir), exist_ok=True)

    print(f"\n--- Cloning Git Repository: {repo_url} into {clone_target_dir} ---")
    cmd = ['git', 'clone', repo_url, clone_target_dir]
    # Run from the parent directory of the clone target
    return run_script(cmd, "Git Clone", os.path.dirname(clone_target_dir), log_file_path)


def aggregate_final_report(student_id, student_main_output_dir, dirs_config, final_report_path, rubric_file_path):
    """Aggregates individual reports into a final Markdown document based on the rubric."""
    print("\n--- Aggregating Final Report ---")

    rubric_content = ""
    if rubric_file_path and os.path.exists(rubric_file_path):
        try:
            with open(rubric_file_path, 'r', encoding='utf-8') as f_rubric:
                rubric_content = f_rubric.read()
            print(f"Read rubric content from {rubric_file_path}")
        except Exception as e:
            print(f"Warning: Could not read rubric file {rubric_file_path}: {e}")

    generated_reports_data = {}

    for section_name, (tool_script, report_pattern) in REPORT_MAPPING.items():
        # Determine the key for dirs_config based on the tool script name
        # This needs to be robust to how keys were defined in setup_directories
        # Map script name to its corresponding output directory key
        tool_output_dir_key = None
        if tool_script == "conversation_analyser.py":
            tool_output_dir_key = "conversation_analysis_reports"
        elif tool_script == "accessibility_checker.py":
            tool_output_dir_key = "accessibility_reports"
        elif tool_script == "code_quality_analyser.py":
            tool_output_dir_key = "code_quality_reports"
        elif tool_script == "deployment_analyser.py":
            tool_output_dir_key = "deployment_reports"
        elif tool_script == "git_analyser.py":
            tool_output_dir_key = "git_reports"
        elif tool_script == "performance_analyser.py":
            tool_output_dir_key = "performance_reports"
        elif tool_script == "responsive_analyser.py":
            tool_output_dir_key = "responsive_reports"
        elif tool_script == "validate_web.py":
            tool_output_dir_key = "validation_reports"
        # Add mappings for any other tools

        if tool_output_dir_key and tool_output_dir_key in dirs_config:
             tool_report_dir_path = dirs_config[tool_output_dir_key]
        else:
            print(f"Warning: Output directory mapping not found for tool '{tool_script}' or directory not in dirs_config. Skipping report for '{section_name}'.")
            continue

        # Ensure the directory exists before searching for reports
        if not os.path.isdir(tool_report_dir_path):
            print(f"Warning: Report directory '{tool_report_dir_path}' for tool '{tool_script}' does not exist. Skipping report for '{section_name}'.")
            continue


        # Construct the glob pattern using the determined directory path
        full_report_pattern = os.path.join(tool_report_dir_path, report_pattern)
        report_files_found = glob.glob(full_report_pattern)

        if report_files_found:
            # Assuming the first matched file is the primary report, adjust if needed
            report_file_to_read = report_files_found[0]
            if os.path.exists(report_file_to_read):
                print(f"Reading report for '{section_name}' from: {report_file_to_read}")
                try:
                    with open(report_file_to_read, 'r', encoding='utf-8') as f_report:
                        report_content = f_report.read()
                        generating_tool_key = tool_script
                        if generating_tool_key not in generated_reports_data:
                            generated_reports_data[generating_tool_key] = []
                        # Prepend a clear marker for which tool and section this content is for
                        generated_reports_data[generating_tool_key].append(f"## Contribution from `{tool_script}` for Rubric Area: '{section_name}'\n\n{report_content}\n\n---\n")
                except Exception as e:
                    print(f"Warning: Could not read report file {report_file_to_read}: {e}")
            else:
                # This case should ideally not happen if glob found it, but as a safety check
                print(f"Warning: Report file {report_file_to_read} (matched by pattern) not found for tool {tool_script}.")
        else:
            print(f"Warning: No report file matching pattern '{report_pattern}' found in {tool_report_dir_path} for tool {tool_script} (section: '{section_name}').")

    # Write the final aggregated report
    try:
        with open(final_report_path, 'w', encoding='utf-8') as f_final:
            f_final.write(f"# Final Assessment Report for {student_id}\n")
            f_final.write(f"Generated on: {datetime.now().isoformat()}\n\n")
            f_final.write("This report aggregates findings from various automated assessment tools.\n")
            f_final.write("Please review the individual tool reports for more detailed information.\n\n")
            f_final.write("---\n")

            if rubric_content:
                f_final.write("\n## Original Rubric Overview (for reference)\n\n")
                f_final.write("```markdown\n") # Using markdown block for better rendering if rubric is md
                f_final.write(rubric_content)
                f_final.write("\n```\n\n---\n\n")

            f_final.write("\n## Aggregated Assessment Results by Primary Rubric Category\n\n")

            for rubric_cat in RUBRIC_SECTIONS_ORDER:
                f_final.write(f"# {rubric_cat}\n\n")
                found_content_for_category = False
                # Iterate through generated reports and add content if it maps to the current rubric category
                for tool_name, reports_content_list in generated_reports_data.items():
                    if TOOL_TO_RUBRIC_CATEGORY.get(tool_name) == rubric_cat:
                        for report_text in reports_content_list:
                            f_final.write(report_text)
                        found_content_for_category = True

                if not found_content_for_category:
                    # Add placeholder messages for sections not covered by automated reports or where reports were missing
                    if rubric_cat == "Final Product & Technical Functionality":
                         f_final.write("*(Partially covered by Performance Analysis. Functionality of embedded projects and overall technical execution typically require manual review.)*\n\n")
                    elif rubric_cat == "Design & Responsiveness":
                         f_final.write("*(Responsive Design and Flexbox/Grid usage are covered by `responsive_analyser.py`. Cohesive color scheme, typography, and visual appeal typically require manual review.)*\n\n")
                    elif rubric_cat == "Accessibility & Semantic HTML":
                         f_final.write("*(Covered by `accessibility_checker.py`.)*\n\n") # Explicitly state if fully covered
                    elif rubric_cat == "AI Integration & Critical Interaction":
                        f_final.write("*(Covered by `conversation_analyser.py`.)*\n\n")
                    elif rubric_cat == "Development Process":
                         f_final.write("*(Code Organisation/Documentation and Validation are covered by `code_quality_analyser.py` and `validate_web.py`. Problem-solving approaches and development workflow may require insights from Git history, AI conversations, and manual review.)*\n\n")
                    elif rubric_cat == "Version Control":
                        f_final.write("*(Covered by `git_analyser.py`.)*\n\n")
                    elif rubric_cat == "Deployment":
                         f_final.write("*(Covered by `deployment_analyser.py`.)*\n\n")
                    else:
                        f_final.write("*(No automated reports directly mapped to this primary rubric section found. Manual review may be required.)*\n\n")
                f_final.write("---\n\n")

        print(f"Final aggregated report saved to: {final_report_path}")

    except IOError as e:
        print(f"Error writing final aggregated report to {final_report_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while aggregating reports: {e}")


def main():
    parser = argparse.ArgumentParser(description="Main Assessor for Web Fundamentals Projects.")
    parser.add_argument("--student_id", required=True, help="Unique identifier for the student (e.g., student_name or student_number).")
    parser.add_argument("--website_folder", required=True, help="Path to the student's unzipped website project folder (for local file analysis where applicable).")
    parser.add_argument("--manual_conversations_folder", help="Path to the folder containing student's manually saved AI conversation logs (optional).")
    parser.add_argument("--git_repo_url", help="URL of the student's GitHub repository.")
    parser.add_argument("--netlify_url", help="URL of the student's live Netlify deployment.")
    parser.add_argument("--chat_scrape_file", help="Optional: Path to a text file containing URLs of AI conversations to scrape (one URL per line).")
    parser.add_argument("--output_base_dir", default="master_assessment_reports", help="Base directory to store all assessment outputs.")
    parser.add_argument("--rubric_file", default="blackboard_rubric.md", help="Path to the master rubric file for reference in the final report.")
    parser.add_argument("--chrome_path", help="Optional: Path to Chrome/Chromium executable for Lighthouse/Selenium if not found automatically.")
    parser.add_argument("--no_headless_scraping", action="store_false", dest="headless_scraping", help="Run AI conversation scraping in non-headless (visible browser) mode.")
    parser.set_defaults(headless_scraping=True)

    args = parser.parse_args()

    student_main_output_dir, dirs_config = setup_directories(args.output_base_dir, args.student_id)
    log_file_path = os.path.join(student_main_output_dir, "assessment_log.txt")

    # Ensure the log file is created or cleared at the start of a new run
    with open(log_file_path, 'w', encoding='utf-8') as log_f:
        log_f.write(f"Assessment started for {args.student_id} at {datetime.now().isoformat()}\n")
        log_f.write(f"Arguments: {vars(args)}\n")
        log_f.write("-" * 20 + "\n") # Separator


    # --- Prepare AI Conversations (Copy manual + Scrape if specified) ---
    conversation_input_dir = dirs_config["conversation_input_dir"]
    # Pass args.headless_scraping to the function
    prepare_ai_conversations(args.manual_conversations_folder, args.chat_scrape_file, conversation_input_dir, log_file_path, args.headless_scraping)

    # --- Clone Git Repository ---
    git_repo_local_path = dirs_config["temp_git_repo"]
    # Pass log_file_path to clone_git_repository
    if not clone_git_repository(args.git_repo_url, git_repo_local_path, log_file_path):
        print(f"CRITICAL: Failed to clone Git repository: {args.git_repo_url}. Git-dependent analyses will be affected.")
        # Log this critical failure
        with open(log_file_path, 'a', encoding='utf-8') as log_f:
            log_f.write(f"CRITICAL: Failed to clone Git repository: {args.git_repo_url}. Git-dependent analyses will be affected.\n")


    # --- Run Screenshot tool ---
    screenshot_cmd = ['python', os.path.join(SCRIPTS_DIR, 'screenshot.py'),
                      '--directory', os.path.abspath(args.website_folder),
                      '--output', os.path.abspath(dirs_config["screenshot_output"])]
    # Add chrome_path if available and if screenshot.py supports a --chrome-path arg
    # (Assuming screenshot.py uses Selenium which might find Chrome automatically or need a driver)
    # Check screenshot.py's arguments if you want to pass --chrome-path here.
    # For now, keeping it simple as per original code.
    # if args.chrome_path:
    #     screenshot_cmd.extend(['--chrome-path', args.chrome_path]) # Example if supported

    # Run from the base output directory
    run_script(screenshot_cmd, "screenshot.py", student_main_output_dir, log_file_path)


    # --- Run All Assessment Scripts ---
    website_folder_abs = os.path.abspath(args.website_folder)
    netlify_url = args.netlify_url # Get Netlify URL from args - Defined here!

    # Accessibility Checker
    acc_cmd = ['python', os.path.join(SCRIPTS_DIR, 'accessibility_checker.py'),
               website_folder_abs, # Assuming accessibility_checker can work on local files
               '--output-dir', os.path.abspath(dirs_config["accessibility_reports"]),
               '--format', 'both']
    run_script(acc_cmd, "accessibility_checker.py", student_main_output_dir, log_file_path)

    # Code Quality Analyser
    cq_cmd = ['python', os.path.join(SCRIPTS_DIR, 'code_quality_analyser.py'),
              website_folder_abs, # Assuming code_quality_analyser works on local files
              '--output', os.path.abspath(dirs_config["code_quality_reports"])]
    run_script(cq_cmd, "code_quality_analyser.py", student_main_output_dir, log_file_path)

    # Conversation Analyser
    # conversation_input_dir is already prepared by prepare_ai_conversations
    conv_cmd = ['python', os.path.join(SCRIPTS_DIR, 'conversation_analyser.py'),
                os.path.abspath(conversation_input_dir), # Use the prepared input directory
                '--output_dir', os.path.abspath(dirs_config["conversation_analysis_reports"])]
    run_script(conv_cmd, "conversation_analyser.py", student_main_output_dir, log_file_path)

    # Deployment Analyser
    dep_cmd = ['python', os.path.join(SCRIPTS_DIR, 'deployment_analyser.py'),
               args.git_repo_url, args.netlify_url, # Uses both repo URL and Netlify URL
               '--output', os.path.abspath(dirs_config["deployment_reports"])]
    run_script(dep_cmd, "deployment_analyser.py", student_main_output_dir, log_file_path)

    # Git Analyser - Only run if git clone was successful
    # Check for the .git directory as a robust indicator of a successful clone
    if os.path.exists(os.path.join(git_repo_local_path, '.git')):
        git_cmd = ['python', os.path.join(SCRIPTS_DIR, 'git_analyser.py'),
                   os.path.abspath(git_repo_local_path), # Path to the cloned repository
                   '--output', os.path.abspath(dirs_config["git_reports"])]
        run_script(git_cmd, "git_analyser.py", student_main_output_dir, log_file_path)
    else:
        print("Skipping Git analysis as repository was not cloned successfully or path is invalid.")
        # Log the skip
        with open(log_file_path, 'a', encoding='utf-8') as log_f:
            log_f.write("Skipping Git analysis as repository was not cloned successfully or path is invalid.\n")


    # Performance Analyser - Using the Netlify URL
    perf_cmd = ['python', os.path.join(SCRIPTS_DIR, 'performance_analyser.py'),
                '--url', netlify_url, # Use the --url argument with the Netlify URL
                '--output', os.path.abspath(dirs_config["performance_reports"])]
    # Add chrome-path if provided in the main script arguments
    if args.chrome_path:
        perf_cmd.extend(['--chrome-path', args.chrome_path])
    # Note: --parallel and --use-ci are generally not applicable or ignored by performance_analyser.py when testing a single URL
    run_script(perf_cmd, "performance_analyser.py", student_main_output_dir, log_file_path)


    # Responsive Analyser
    resp_cmd = ['python', os.path.join(SCRIPTS_DIR, 'responsive_analyser.py'),
                website_folder_abs, # Assuming responsive_analyser works on local files + screenshots
                '--screenshots', os.path.abspath(dirs_config["screenshot_output"]),
                '--output', os.path.abspath(dirs_config["responsive_reports"]),
                '--format', 'both']
    run_script(resp_cmd, "responsive_analyser.py", student_main_output_dir, log_file_path)

    # Validation Analyser
    val_cmd = ['python', os.path.join(SCRIPTS_DIR, 'validate_web.py'),
               website_folder_abs, # Assuming validate_web works on local files
               '--output', os.path.join(dirs_config["validation_reports"], 'validation_detailed_report.md'),
               '--summary', os.path.join(dirs_config["validation_reports"], 'validation_summary.md'),
               '--rubric', os.path.join(dirs_config["validation_reports"], 'validation_rubric.md')]
    run_script(val_cmd, "validate_web.py", student_main_output_dir, log_file_path)

    # --- Aggregate Final Report ---
    final_report_file_path = os.path.join(dirs_config["final_report_dir"], f"{args.student_id}_final_assessment_report.md")
    # Pass log_file_path to aggregate_final_report for better logging within that function
    aggregate_final_report(args.student_id, student_main_output_dir, dirs_config, final_report_file_path, args.rubric_file)

    # --- Cleanup (Optional) ---
    try:
        # Ensure git_repo_local_path is defined before attempting to remove
        if 'git_repo_local_path' in locals() and os.path.exists(git_repo_local_path):
            print(f"\n--- Cleaning up temporary Git repository: {git_repo_local_path} ---")
            # Use shutil.rmtree with ignore_errors and onerror for more robust cleanup
            def onerror(func, path, exc_info):
                """Error handler for shutil.rmtree."""
                import traceback
                print(f"Error removing {path}: {exc_info}")
                with open(log_file_path, 'a', encoding='utf-8') as log_f:
                     log_f.write(f"Error removing {path} during cleanup: {exc_info}\n")
                     log_f.write(traceback.format_exc() + "\n")

            shutil.rmtree(git_repo_local_path, ignore_errors=False, onerror=onerror)
            print("Temporary Git repository removed.")
    except Exception as e:
        cleanup_error_msg = f"Error during cleanup of Git repo: {e}"
        print(cleanup_error_msg)
        with open(log_file_path, 'a', encoding='utf-8') as log_f:
            log_f.write(cleanup_error_msg + "\n")

    print(f"\n--- Assessment for {args.student_id} complete. ---")
    print(f"All outputs and logs are in: {student_main_output_dir}")
    print(f"Final aggregated report: {final_report_file_path}")
    print(f"Detailed log: {log_file_path}")

if __name__ == "__main__":
    main()
