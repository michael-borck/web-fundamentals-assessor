#!/usr/bin/env python3
import csv
import subprocess
import os
import argparse

def extract_repo_folder(github_url: str) -> str:
    """
    Given a Git URL (SSH or HTTPS), strip off .git (if present),
    pull out the repo name, and append '-main'.
    E.g. 'git@github.com:user/repo.git' → 'repo-main'
    """
    url = github_url[:-4] if github_url.endswith('.git') else github_url
    sep = max(url.rfind('/'), url.rfind(':'))
    repo = url[sep+1:]
    return f"{repo}-main"

def build_and_run(row, args):
    student = row['student'].strip()
    github = row['github'].strip()
    netlify = row['netlify'].strip()

    cmd = ['python', args.main_script,
           '--student_id', student]

    # Determine website folder
    if github.lower() != 'none':
        # Use GitHub repo folder when URL is provided
        repo_folder = extract_repo_folder(github)
        website_folder = os.path.join(student, repo_folder)
    else:
        # No GitHub URL: list directories under student/ and exclude manual conversations folder
        all_dirs = [d for d in os.listdir(student)
                    if os.path.isdir(os.path.join(student, d))]
        exclude = args.manual_folder_name
        candidates = [d for d in all_dirs if d != exclude]
        if len(candidates) == 1:
            website_folder = os.path.join(student, candidates[0])
        else:
            raise ValueError(
                f"Could not determine website folder for student {student}. Found: {candidates}"
            )
    cmd += ['--website_folder', website_folder]

    # Manual conversations folder (e.g., 'conversations' or 'ai-conversations')
    manual_folder = os.path.join(student, args.manual_folder_name)
    cmd += ['--manual_conversations_folder', manual_folder]

    # Include Git and Netlify URLs if available
    if github.lower() != 'none':
        cmd += ['--git_repo_url', github]
    if netlify.lower() != 'none':
        cmd += ['--netlify_url', netlify]

    print("Running:", ' '.join(cmd))
    if not args.dry_run:
        subprocess.run(cmd, check=True)
    else:
        print("Dry run: command not executed.")


def main():
    parser = argparse.ArgumentParser(
        description="Batch-run main_assessor.py for each row in a CSV"
    )
    parser.add_argument('csv_file', help="Path to input CSV")
    parser.add_argument('--main-script',
                        default='main_assessor.py',
                        help="Path to the main_assessor.py script")
    parser.add_argument('--manual-folder-name',
                        default='ai-conversations',
                        help="Name of the manual conversations subfolder")
    parser.add_argument('--dry-run',
                        action='store_true',
                        help="If set, print commands without executing them")
    args = parser.parse_args()

    with open(args.csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                build_and_run(row, args)
            except Exception as e:
                print(f"Error processing student {row.get('student')}: {e}")

if __name__ == '__main__':
    main()


