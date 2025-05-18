import re
import os
import sys
import argparse
from pathlib import Path

def midpoint_percentage(min_range, max_range):
    """Calculate the midpoint percentage of a range, rounded to nearest 0.5"""
    midpoint = (float(min_range) + float(max_range)) / 2
    # Round to nearest 0.5
    return round(midpoint * 2) / 2

def extract_results_from_report(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Create a dictionary to store results with subcategories and assessment status
    results = {
        "Final Product & Technical Functionality (25%)": {
            "covered": "Partially",
            "assessment_type": "Performance analysis provided, embedded projects require manual review",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Fully functional embedded projects (15%)": {"score": "", "status": "Requires manual review"},
                "Overall site interactivity and performance (10%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Design & Responsiveness (15%)": {
            "covered": "Partially",
            "assessment_type": "Responsive Design and Flexbox/Grid assessment provided. Color scheme and typography require manual review.",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Responsive design (mobile-first) (7%)": {"score": "", "status": "Complete assessment"},
                "Effective use of Flexbox/Grid (4%)": {"score": "", "status": "Complete assessment"},
                "Cohesive color scheme and typography (4%)": {"score": "", "status": "Requires manual review"}
            }
        },
        "Accessibility & Semantic HTML (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Compliance with WCAG 2.1 AA standards (5%)": {"score": "", "status": "Complete assessment"},
                "Proper semantic tags and ARIA attributes (3%)": {"score": "", "status": "Complete assessment"},
                "Accessible navigation and content (2%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "AI Integration & Critical Interaction (20%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Depth and relevance of AI interactions (5%)": {"score": "", "status": "Complete assessment"},
                "Prompt engineering evolution (5%)": {"score": "", "status": "Complete assessment"},
                "Critical evaluation of AI-generated output (5%)": {"score": "", "status": "Complete assessment"},
                "Implementation improvements beyond AI suggestions (5%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Development Process (10%)": {
            "covered": "Partially",
            "assessment_type": "Only Code organisation assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Problem-solving approaches (5%)": {"score": "", "status": "No assessment provided"},
                "Code organisation and documentation (5%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Version Control (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Commit frequency and distribution (3%)": {"score": "", "status": "Complete assessment"},
                "Quality of commit messages (4%)": {"score": "", "status": "Complete assessment"},
                "Repository organisation (3%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Deployment (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Correct deployment using GitHub and Netlify (10%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Optional Bonus (up to 5%)": {
            "covered": "No",
            "assessment_type": "No assessment provided",
            "score": "", # Section score will be left blank as per request
            "subcategories": {
                "Quality and depth of code review and improvement roadmap": {"score": "", "status": "No assessment provided"}
            }
        }
    }

    # Extract Site Interactivity and Performance score
    site_performance_match = re.search(r"Site Interactivity and Performance.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)\s*\(([\d.]+)%\)", content, re.DOTALL)
    if site_performance_match:
        performance = site_performance_match.group(1)
        min_range = site_performance_match.group(2)
        max_range = site_performance_match.group(3)
        score = site_performance_match.group(4)
        total = site_performance_match.group(5)
        percent = site_performance_match.group(6)

        # Calculate midpoint percentage for the performance level
        if score and total:
            # If explicit score is provided, use it
            try:
                numeric_score = float(score)
                results["Final Product & Technical Functionality (25%)"]["subcategories"]["Overall site interactivity and performance (10%)"]["score"] = f"{numeric_score}"
            except ValueError:
                # Fallback to midpoint calculation
                midpoint = midpoint_percentage(min_range, max_range)
                numeric_score = round((midpoint / 100) * 10 * 2) / 2  # 10% criteria, rounded to nearest 0.5
                results["Final Product & Technical Functionality (25%)"]["subcategories"]["Overall site interactivity and performance (10%)"]["score"] = f"{numeric_score}"

        # Section total is not needed as per new requirements
        # results["Final Product & Technical Functionality (25%)"]["score"] = f"{section_total}/25"


    # Extract Responsive Design score
    responsive_design_match = re.search(r"### Responsive Design \(Mobile-First\).*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\n\*\*Score:\*\*\s*([\d.]+)/([\d.]+)\s*points\s*\(([\d.]+)%\)", content, re.DOTALL)
    if responsive_design_match:
        performance = responsive_design_match.group(1)
        min_range = responsive_design_match.group(2)
        max_range = responsive_design_match.group(3)
        score = responsive_design_match.group(4)
        total = responsive_design_match.group(5)
        percent = responsive_design_match.group(6)

        # Use the provided score if available, otherwise calculate from midpoint
        if score:
            try:
                numeric_score = float(score)
                results["Design & Responsiveness (15%)"]["subcategories"]["Responsive design (mobile-first) (7%)"]["score"] = f"{numeric_score}"
            except ValueError:
                # Fallback to midpoint calculation
                midpoint = midpoint_percentage(min_range, max_range)
                numeric_score = round((midpoint / 100) * 7 * 2) / 2  # 7% criteria, rounded to nearest 0.5
                results["Design & Responsiveness (15%)"]["subcategories"]["Responsive design (mobile-first) (7%)"]["score"] = f"{numeric_score}"

    # Extract Flexbox/Grid usage from CSS features
    flexbox_grid_match = re.search(r"CSS Responsiveness Features:.*?Flexbox Features:\s*(\d+).*?Grid Features:\s*(\d+)", content, re.DOTALL)
    if flexbox_grid_match:
        flexbox_count = int(flexbox_grid_match.group(1))
        grid_count = int(flexbox_grid_match.group(2))

        # Determine performance level based on feature count
        total_layout_features = flexbox_count + grid_count
        if total_layout_features >= 10:
            min_range = "65"
            max_range = "74"
        elif total_layout_features >= 5:
            min_range = "50"
            max_range = "64"
        else:
            min_range = "0"
            max_range = "49"

        # Calculate the midpoint score
        midpoint = midpoint_percentage(min_range, max_range)
        numeric_score = round((midpoint / 100) * 4 * 2) / 2  # 4% criteria, rounded to nearest 0.5
        results["Design & Responsiveness (15%)"]["subcategories"]["Effective use of Flexbox/Grid (4%)"]["score"] = f"{numeric_score}"

    # Extract Overall Design & Responsiveness score
    total_design_match = re.search(r"### Total Design & Responsiveness Score.*?\n\*\*Score:\*\*\s*([\d.]+)/([\d.]+)\s*points\s*\(([\d.]+)%\)", content, re.DOTALL)
    if total_design_match:
        score = total_design_match.group(1)
        total = total_design_match.group(2)
        percent = total_design_match.group(3)

        # Section total is not needed as per new requirements
        # if score:
        #     results["Design & Responsiveness (15%)"]["score"] = f"{score}/15"


    # Extract Accessibility & Semantic HTML scores
    accessibility_match = re.search(r"Average Accessibility Score:\s*([\d.]+)/([\d.]+)", content)
    if accessibility_match:
        score = accessibility_match.group(1)
        total = accessibility_match.group(2)

        # Section total is not needed as per new requirements
        # try:
        #     # Convert score to percentage then to points out of 10
        #     score_float = float(score)
        #     total_float = float(total)
        #     percentage = (score_float / total_float) * 100
        #     points_out_of_10 = round((percentage / 100) * 10 * 2) / 2  # 10% total, rounded to nearest 0.5
        #     results["Accessibility & Semantic HTML (10%)"]["score"] = f"{points_out_of_10}"
        # except ValueError:
        #     # Keep the original score format if conversion fails
        #     results["Accessibility & Semantic HTML (10%)"]["score"] = f"{score}/{total}"


    # Extract WCAG compliance score
    wcag_match = re.search(r"WCAG 2\.1 AA Compliance Score:\s*(\d+)/(\d+)", content)
    if wcag_match:
        score = wcag_match.group(1)
        total = wcag_match.group(2)

        # Look for the WCAG performance level section specifically
        wcag_perf_match = re.search(r"### WCAG 2\.1 AA Compliance.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\n\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL) # Added Points capture
        if wcag_perf_match:
            score_points = wcag_perf_match.group(4) # Capture points
            results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"] = f"{score_points}/5"
        else: # Fallback to midpoint calculation if points not explicitly found
            wcag_perf_match = re.search(r"### WCAG 2\.1 AA Compliance.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
            if wcag_perf_match:
                min_range = wcag_perf_match.group(2)
                max_range = wcag_perf_match.group(3)

                # Calculate actual score out of 5 (midpoint of range)
                midpoint = midpoint_percentage(min_range, max_range)
                numeric_score = round((midpoint / 100) * 5 * 2) / 2  # 5% criteria, rounded to nearest 0.5
                results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"] = f"{numeric_score}"

    # Extract semantic tags score
    semantic_match = re.search(r"### Proper Semantic Tags and ARIA Attributes.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL) # Added Points capture
    if semantic_match:
        score_points = semantic_match.group(4) # Capture points
        results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Proper semantic tags and ARIA attributes (3%)"]["score"] = f"{score_points}/3"
    else: # Fallback to midpoint calculation if points not explicitly found
        semantic_match = re.search(r"### Proper Semantic Tags and ARIA Attributes.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
        if semantic_match:
            min_range = semantic_match.group(2)
            max_range = semantic_match.group(3)

            # Calculate actual score out of 3 (midpoint of range)
            midpoint = midpoint_percentage(min_range, max_range)
            numeric_score = round((midpoint / 100) * 3 * 2) / 2  # 3% criteria, rounded to nearest 0.5
            results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Proper semantic tags and ARIA attributes (3%)"]["score"] = f"{numeric_score}"

    # Extract navigation accessibility score
    nav_match = re.search(r"### Accessible Navigation and Content.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL) # Added Points capture
    if nav_match:
        score_points = nav_match.group(4) # Capture points
        results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Accessible navigation and content (2%)"]["score"] = f"{score_points}/2"
    else: # Fallback to midpoint calculation if points not explicitly found
        nav_match = re.search(r"### Accessible Navigation and Content.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
        if nav_match:
            min_range = nav_match.group(2)
            max_range = nav_match.group(3)

            # Calculate actual score out of 2 (midpoint of range)
            midpoint = midpoint_percentage(min_range, max_range)
            numeric_score = round((midpoint / 100) * 2 * 2) / 2  # 2% criteria, rounded to nearest 0.5
            results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Accessible navigation and content (2%)"]["score"] = f"{numeric_score}"

    # Section total is not needed as per new requirements
    # if all([wcag_score, semantic_score, nav_score]):
    #     try:
    #         total_accessibility = float(wcag_score) + float(semantic_score) + float(nav_score)
    #         results["Accessibility & Semantic HTML (10%)"]["score"] = f"{total_accessibility}/10"
    #     except ValueError:
    #         pass  # Keep the previously set score if conversion fails
    # elif results["Accessibility & Semantic HTML (10%)"]["score"]:
    #      # If no subscores but an overall score exists, format it
    #      current_score = results["Accessibility & Semantic HTML (10%)"]["score"]
    #      if "/" not in current_score:
    #          results["Accessibility & Semantic HTML (10%)"]["score"] = f"{current_score}/10"


    # Extract AI Integration scores
    ai_scores_match = re.search(r"\*\*Average\*\*\s*\|\s*-\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|", content)
    if ai_scores_match:
        ai_interaction_score = ai_scores_match.group(1)
        prompt_engineering_score = ai_scores_match.group(3)
        critical_evaluation_score = ai_scores_match.group(5)
        implementation_score = ai_scores_match.group(7)
        total_score = ai_scores_match.group(9)

        # Use the actual numeric scores directly for subcategories
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Depth and relevance of AI interactions (5%)"]["score"] = f"{ai_interaction_score}/5"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Prompt engineering evolution (5%)"]["score"] = f"{prompt_engineering_score}/5"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Critical evaluation of AI-generated output (5%)"]["score"] = f"{critical_evaluation_score}/5"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Implementation improvements beyond AI suggestions (5%)"]["score"] = f"{implementation_score}/5"
        # Section total is not needed as per new requirements
        # results["AI Integration & Critical Interaction (20%)"]["score"] = f"{total_score}/20"


    # Extract Code Organisation score
    code_quality_match = re.search(r"\*\*Assessment:\*\*\s*([\d.]+)/([\d.]+)\s*points\s*\(([\d.]+)%\)", content)
    if code_quality_match:
        score = code_quality_match.group(1)
        total = code_quality_match.group(2)

        # Use the provided numeric score directly for the subcategory
        results["Development Process (10%)"]["subcategories"]["Code organisation and documentation (5%)"]["score"] = f"{score}/5"
        # Section total is not needed as per new requirements
        # results["Development Process (10%)"]["score"] = f"{score}/10"

    # Extract Code Quality Validation score (redundant with above if format is consistent, keeping for robustness)
    validation_match = re.search(r"\*\*Code Organisation and Documentation.*\n\*\*Score:\*\*\s*([\d.]+)/([\d.]+)\s*\((\w+)\s*\((\d+)-(\d+)%\)\)", content)
    if validation_match:
        score = validation_match.group(1)
        total = validation_match.group(2)

        # If this match is found, it likely provides the definitive score for the subcategory
        results["Development Process (10%)"]["subcategories"]["Code organisation and documentation (5%)"]["score"] = f"{score}/5"
        # Section total is not needed as per new requirements
        # results["Development Process (10%)"]["score"] = f"{score}/10"


    # Extract Version Control scores
    version_control_overall_match = re.search(r"\*\*Overall Version Control\*\*\s*\|\s*\*\*([\d.]+)/([\d.]+)\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|", content)
    if version_control_overall_match:
        score = version_control_overall_match.group(1)
        # Section total is not needed as per new requirements
        # results["Version Control (10%)"]["score"] = f"{score}/10"

    # Extract commit frequency score
    commit_freq_match = re.search(r"### Commit Frequency and Distribution.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if commit_freq_match:
        score = commit_freq_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Commit frequency and distribution (3%)"]["score"] = f"{score}/3"

    # Extract commit messages quality score
    commit_msg_match = re.search(r"### Quality of Commit Messages.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if commit_msg_match:
        score = commit_msg_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Quality of commit messages (4%)"]["score"] = f"{score}/4"

    # Extract repository organisation score
    repo_org_match = re.search(r"### Repository Organisation.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if repo_org_match:
        score = repo_org_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Repository organisation (3%)"]["score"] = f"{score}/3"

    # Section total is not needed as per new requirements
    # commit_freq_score = results["Version Control (10%)"]["subcategories"]["Commit frequency and distribution (3%)"]["score"]
    # commit_msg_score = results["Version Control (10%)"]["subcategories"]["Quality of commit messages (4%)"]["score"]
    # repo_org_score = results["Version Control (10%)"]["subcategories"]["Repository organisation (3%)"]["score"]
    # if all([commit_freq_score, commit_msg_score, repo_org_score]):
    #     try:
    #         # Extract numeric value before the '/' for summation
    #         total_vc = float(commit_freq_score.split('/')[0]) + float(commit_msg_score.split('/')[0]) + float(repo_org_score.split('/')[0])
    #         results["Version Control (10%)"]["score"] = f"{total_vc}/10"
    #     except (ValueError, IndexError):
    #         pass


    # Extract Deployment score
    deployment_match = re.search(r"### Correct deployment using GitHub and Netlify.*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if deployment_match:
        score = deployment_match.group(1)
        # Section total is not needed as per new requirements
        # results["Deployment (10%)"]["score"] = f"{score}/10"
        results["Deployment (10%)"]["subcategories"]["Correct deployment using GitHub and Netlify (10%)"]["score"] = f"{score}/10"

    # Extract Optional Bonus score
    optional_bonus_match = re.search(r"## Optional Bonus.*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if optional_bonus_match:
        score = optional_bonus_match.group(1)
        # Section total is not needed as per new requirements
        # results["Optional Bonus (up to 5%)"]["score"] = f"{score}/5"
        # Optional bonus only has one subcategory listed in the initial structure
        for subcat in results["Optional Bonus (up to 5%)"]["subcategories"]:
            results["Optional Bonus (up to 5%)"]["subcategories"][subcat]["score"] = f"{score}/5"


    return results


# Removed calculate_total_score function as the summary section is removed

def create_markdown_table(results, student_id): # Simplified argument is no longer needed
    table = f"# Assessment Results for {student_id}\n\n"

    # Version with all subcategories included
    table += "| Rubric Section | Score |\n"
    table += "|----------------|-------|\n"

    for section, data in results.items():
        # Add section row - Score column is intentionally blank
        table += f"| **{section}** | |\n"

        # Add all subcategory rows
        for subcat, subdata in data['subcategories'].items():
            # Display score if available, otherwise blank. Strip trailing whitespace from score.
            score_display = subdata['score'].strip() if subdata['score'] else ""
            table += f"| - {subcat} | {score_display} |\n"

    # Removed the summary section

    return table

def create_ascii_table(results, student_id):
    """Create an ASCII table with fixed-width columns for better alignment"""

    # Define column widths
    section_width = 45
    score_width = 15

    # Create header
    header = f"Assessment Results for {student_id}\n"
    header += "=" * (section_width + score_width + 3) + "\n\n"

    # Create table structure
    table = f"{'Rubric Section':{section_width}} | {'Score':{score_width}}\n"
    table += "-" * section_width + "-+-" + "-" * score_width + "\n"

    # Add rows
    for section, data in results.items():
        # Format section name to remove the percentage for cleaner display
        section_name = re.sub(r"\s*\(\d+%\)", "", section)
        # Add section row - Score column is intentionally blank, padded to width
        table += f"{section_name:{section_width}} | {'':{score_width}}\n".rstrip() + "\n" # rstrip to remove potential trailing space

        # Add all subcategory rows
        for subcat, subdata in data['subcategories'].items():
            # Format subcategory name to remove the percentage
            subcat_name = re.sub(r"\s*\(\d+%\)", "", subcat)
            # Indent subcategories for better readability
            score_display = subdata['score'].strip() if subdata['score'] else ""
            table += f"  - {subcat_name:{section_width-4}} | {score_display:{score_width}}\n".rstrip() + "\n" # rstrip and pad score

    # Removed the summary section

    return header + table


def process_student(student_id, base_dir, simplified=False, ascii_format=False):
    file_path = Path(f"{base_dir}/{student_id}/final_assessment/{student_id}_final_assessment_report.md")

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False

    results = extract_results_from_report(file_path)

    if ascii_format:
        table_content = create_ascii_table(results, student_id)
    else:
        table_content = create_markdown_table(results, student_id)

    # Always use 'results.txt' as output file name
    output_file = Path(f"{base_dir}/{student_id}/results.txt")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(table_content)

    print(f"Results table created for student {student_id} at {output_file}")
    return True

def process_all_students(base_dir, simplified=False, ascii_format=False):
    success_count = 0
    failure_count = 0

    if not Path(base_dir).exists():
        print(f"Error: Base directory not found: {base_dir}")
        return

    # Get all student directories (assuming directories with numeric names are student IDs)
    student_dirs = [d for d in Path(base_dir).iterdir() if d.is_dir() and d.name.isdigit()]

    for student_dir in student_dirs:
        student_id = student_dir.name
        # Pass simplified=False as the simplified/detailed output logic is removed
        if process_student(student_id, base_dir, simplified=False, ascii_format=ascii_format):
            success_count += 1
        else:
            failure_count += 1

    print(f"\nProcessing complete: {success_count} successful, {failure_count} failed")

def main():
    parser = argparse.ArgumentParser(description='Extract assessment results for students.')
    parser.add_argument('--base-dir', type=str, default='master_assessment_reports',
                        help='Base directory containing student folders (default: master_assessment_reports)')
    # Simplified argument is kept only for filename suffixing now
    parser.add_argument('--simplified', '--simple', action='store_true',
                        help='(Deprecated functionality - now controls output filename suffix) Generate a simplified table.')
    parser.add_argument('--ascii', action='store_true',
                        help='Generate an ASCII-formatted table with fixed-width columns for better alignment')

    # Create a mutually exclusive group for student_id or --all
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Process all students')
    group.add_argument('student_id', nargs='?', type=str, help='Student ID to process')

    args = parser.parse_args()

    # The simplified flag now only affects the output filename suffix
    # The table content format is now consistently the "minimal" version
    if args.all:
        process_all_students(args.base_dir, simplified=False, ascii_format=args.ascii)
    else:
        process_student(args.student_id, args.base_dir, simplified=False, ascii_format=args.ascii)

if __name__ == "__main__" :
    main()

