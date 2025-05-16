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
            "score": "",
            "subcategories": {
                "Fully functional embedded projects (15%)": {"score": "", "status": "Requires manual review"},
                "Overall site interactivity and performance (10%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Design & Responsiveness (15%)": {
            "covered": "Partially",
            "assessment_type": "Responsive Design and Flexbox/Grid assessment provided. Color scheme and typography require manual review.",
            "score": "",
            "subcategories": {
                "Responsive design (mobile-first) (7%)": {"score": "", "status": "Complete assessment"},
                "Effective use of Flexbox/Grid (4%)": {"score": "", "status": "Complete assessment"},
                "Cohesive color scheme and typography (4%)": {"score": "", "status": "Requires manual review"}
            }
        },
        "Accessibility & Semantic HTML (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "",
            "subcategories": {
                "Compliance with WCAG 2.1 AA standards (5%)": {"score": "", "status": "Complete assessment"},
                "Proper semantic tags and ARIA attributes (3%)": {"score": "", "status": "Complete assessment"},
                "Accessible navigation and content (2%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "AI Integration & Critical Interaction (20%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "",
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
            "score": "",
            "subcategories": {
                "Problem-solving approaches (5%)": {"score": "", "status": "No assessment provided"},
                "Code organisation and documentation (5%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Version Control (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "",
            "subcategories": {
                "Commit frequency and distribution (3%)": {"score": "", "status": "Complete assessment"},
                "Quality of commit messages (4%)": {"score": "", "status": "Complete assessment"},
                "Repository organisation (3%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Deployment (10%)": {
            "covered": "Yes",
            "assessment_type": "Complete assessment provided",
            "score": "",
            "subcategories": {
                "Correct deployment using GitHub and Netlify (10%)": {"score": "", "status": "Complete assessment"}
            }
        },
        "Optional Bonus (up to 5%)": {
            "covered": "No",
            "assessment_type": "No assessment provided",
            "score": "",
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
        
        # Set the partial score for Final Product as well
        results["Final Product & Technical Functionality (25%)"]["score"] = f"{numeric_score}/25 (partial)"
    
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
        
        # Try to use the calculated scores to sum up the total
        responsive_score = results["Design & Responsiveness (15%)"]["subcategories"]["Responsive design (mobile-first) (7%)"]["score"]
        flexbox_score = results["Design & Responsiveness (15%)"]["subcategories"]["Effective use of Flexbox/Grid (4%)"]["score"]
        
        # If we have both subscores, calculate the total (excluding color scheme which is manual)
        if responsive_score and flexbox_score:
            try:
                total_score = float(responsive_score) + float(flexbox_score)
                results["Design & Responsiveness (15%)"]["score"] = f"{total_score}/15 (partial)"
            except ValueError:
                # Fallback to using the provided overall score if available
                if score:
                    results["Design & Responsiveness (15%)"]["score"] = f"{score}/15 (partial)"
    
    # Extract Accessibility & Semantic HTML scores
    accessibility_match = re.search(r"Average Accessibility Score:\s*([\d.]+)/([\d.]+)", content)
    if accessibility_match:
        score = accessibility_match.group(1)
        total = accessibility_match.group(2)
        
        try:
            # Convert score to percentage then to points out of 10
            score_float = float(score)
            total_float = float(total)
            percentage = (score_float / total_float) * 100
            points_out_of_10 = round((percentage / 100) * 10 * 2) / 2  # 10% total, rounded to nearest 0.5
            results["Accessibility & Semantic HTML (10%)"]["score"] = f"{points_out_of_10}"
        except ValueError:
            # Keep the original score format if conversion fails
            results["Accessibility & Semantic HTML (10%)"]["score"] = f"{score}/{total}"

    # Extract WCAG compliance score
    wcag_match = re.search(r"WCAG 2\.1 AA Compliance Score:\s*(\d+)/(\d+)", content)
    if wcag_match:
        score = wcag_match.group(1)
        total = wcag_match.group(2)
        
        # Look for the WCAG performance level section specifically
        wcag_perf_match = re.search(r"### WCAG 2\.1 AA Compliance.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
        if wcag_perf_match:
            min_range = wcag_perf_match.group(2)
            max_range = wcag_perf_match.group(3)
            
            # Calculate actual score out of 5 (midpoint of range)
            midpoint = midpoint_percentage(min_range, max_range)
            numeric_score = round((midpoint / 100) * 5 * 2) / 2  # 5% criteria, rounded to nearest 0.5
            results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"] = f"{numeric_score}"
    
    # Try alternative method to extract WCAG compliance if the above didn't work
    if not results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"]:
        alt_wcag_match = re.search(r"## Rubric Evaluation\s+### WCAG 2\.1 AA Compliance.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
        if alt_wcag_match:
            min_range = alt_wcag_match.group(2)
            max_range = alt_wcag_match.group(3)
            
            # Calculate actual score out of 5 (midpoint of range)
            midpoint = midpoint_percentage(min_range, max_range)
            numeric_score = round((midpoint / 100) * 5 * 2) / 2  # 5% criteria, rounded to nearest 0.5
            results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"] = f"{numeric_score}"
    
    # Extract semantic tags score
    semantic_match = re.search(r"### Proper Semantic Tags and ARIA Attributes.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
    if semantic_match:
        min_range = semantic_match.group(2)
        max_range = semantic_match.group(3)
        
        # Calculate actual score out of 3 (midpoint of range)
        midpoint = midpoint_percentage(min_range, max_range)
        numeric_score = round((midpoint / 100) * 3 * 2) / 2  # 3% criteria, rounded to nearest 0.5
        results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Proper semantic tags and ARIA attributes (3%)"]["score"] = f"{numeric_score}"
    
    # Extract navigation accessibility score
    nav_match = re.search(r"### Accessible Navigation and Content.*?\n\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\)", content, re.DOTALL)
    if nav_match:
        min_range = nav_match.group(2)
        max_range = nav_match.group(3)
        
        # Calculate actual score out of 2 (midpoint of range)
        midpoint = midpoint_percentage(min_range, max_range)
        numeric_score = round((midpoint / 100) * 2 * 2) / 2  # 2% criteria, rounded to nearest 0.5
        results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Accessible navigation and content (2%)"]["score"] = f"{numeric_score}"
    
    # Calculate total Accessibility score from subcategories if available
    wcag_score = results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Compliance with WCAG 2.1 AA standards (5%)"]["score"]
    semantic_score = results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Proper semantic tags and ARIA attributes (3%)"]["score"]
    nav_score = results["Accessibility & Semantic HTML (10%)"]["subcategories"]["Accessible navigation and content (2%)"]["score"]
    
    if wcag_score and semantic_score and nav_score:
        try:
            total_accessibility = float(wcag_score) + float(semantic_score) + float(nav_score)
            results["Accessibility & Semantic HTML (10%)"]["score"] = f"{total_accessibility}"
        except ValueError:
            pass  # Keep the previously set score if conversion fails
    
    # Extract AI Integration scores
    ai_scores_match = re.search(r"\*\*Average\*\*\s*\|\s*-\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|\s*([\d.]+)/(\d+)\s*\|", content)
    if ai_scores_match:
        ai_interaction_score = ai_scores_match.group(1)
        prompt_engineering_score = ai_scores_match.group(3)
        critical_evaluation_score = ai_scores_match.group(5)
        implementation_score = ai_scores_match.group(7)
        total_score = ai_scores_match.group(9)
        
        # Use the actual numeric scores directly
        results["AI Integration & Critical Interaction (20%)"]["score"] = f"{total_score}"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Depth and relevance of AI interactions (5%)"]["score"] = f"{ai_interaction_score}"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Prompt engineering evolution (5%)"]["score"] = f"{prompt_engineering_score}"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Critical evaluation of AI-generated output (5%)"]["score"] = f"{critical_evaluation_score}"
        results["AI Integration & Critical Interaction (20%)"]["subcategories"]["Implementation improvements beyond AI suggestions (5%)"]["score"] = f"{implementation_score}"
    
    # Extract Code Organisation score
    code_quality_match = re.search(r"\*\*Assessment:\*\*\s*([\d.]+)/([\d.]+)\s*points\s*\(([\d.]+)%\)", content)
    if code_quality_match:
        score = code_quality_match.group(1)
        total = code_quality_match.group(2)
        
        # Use the provided numeric score directly
        results["Development Process (10%)"]["subcategories"]["Code organisation and documentation (5%)"]["score"] = f"{score}"
        results["Development Process (10%)"]["score"] = f"{score}/10 (partial)"
    
    # Extract Code Quality Validation score
    validation_match = re.search(r"\*\*Code Organisation and Documentation.*\n\*\*Score:\*\*\s*([\d.]+)/([\d.]+)\s*\((\w+)\s*\((\d+)-(\d+)%\)\)", content)
    if validation_match:
        score = validation_match.group(1)
        total = validation_match.group(2)
        
        # If we already have a code quality score, override it with the validation score
        # (since validation is more comprehensive)
        results["Development Process (10%)"]["subcategories"]["Code organisation and documentation (5%)"]["score"] = f"{score}"
        results["Development Process (10%)"]["score"] = f"{score}/10 (partial)"
    
    # Extract Version Control scores
    version_control_overall_match = re.search(r"\*\*Overall Version Control\*\*\s*\|\s*\*\*([\d.]+)/([\d.]+)\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|", content)
    if version_control_overall_match:
        score = version_control_overall_match.group(1)
        results["Version Control (10%)"]["score"] = f"{score}"
    
    # Extract commit frequency score
    commit_freq_match = re.search(r"### Commit Frequency and Distribution.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if commit_freq_match:
        score = commit_freq_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Commit frequency and distribution (3%)"]["score"] = f"{score}"
    
    # Extract commit messages quality score
    commit_msg_match = re.search(r"### Quality of Commit Messages.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if commit_msg_match:
        score = commit_msg_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Quality of commit messages (4%)"]["score"] = f"{score}"
    
    # Extract repository organisation score
    repo_org_match = re.search(r"### Repository Organisation.*?\*\*Performance Level:\*\*\s*(\w+)\s*\((\d+)-(\d+)%\).*?\*\*Points:\*\*\s*([\d.]+)/([\d.]+)", content, re.DOTALL)
    if repo_org_match:
        score = repo_org_match.group(4)
        results["Version Control (10%)"]["subcategories"]["Repository organisation (3%)"]["score"] = f"{score}"
    
    # Extract Deployment score
    deployment_match = re.search(r"\*\*Points:\*\*\s*([\d.]+)/([\d.]+)\s*\(([\d.]+)%\)", content)
    if deployment_match:
        score = deployment_match.group(1)
        results["Deployment (10%)"]["score"] = f"{score}"
        results["Deployment (10%)"]["subcategories"]["Correct deployment using GitHub and Netlify (10%)"]["score"] = f"{score}"
    
    return results

def calculate_total_score(results):
    total_score = 0
    max_possible_score = 0
    available_score = 0
    available_max = 0
    
    for section, data in results.items():
        # Extract the weight from section title (e.g., "Development Process (10%)" -> 10)
        weight_match = re.search(r"\((\d+)%\)", section)
        if weight_match:
            section_weight = int(weight_match.group(1))
            max_possible_score += section_weight
            
            # Extract score value if it exists
            score_text = data["score"]
            if score_text:
                # Try to extract the numeric part before any '/' character
                score_match = re.search(r"([\d.]+)(?:/|$)", score_text)
                if score_match:
                    try:
                        score_value = float(score_match.group(1))
                        total_score += score_value
                        available_score += score_value
                        available_max += section_weight
                    except ValueError:
                        pass
    
    grade_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    available_percentage = (available_score / available_max) * 100 if available_max > 0 else 0
    
    # Determine letter grade based on university scale
    if grade_percentage >= 80:
        letter_grade = "HD (High Distinction)"
    elif grade_percentage >= 70:
        letter_grade = "D (Distinction)"
    elif grade_percentage >= 60:
        letter_grade = "CR (Credit)"
    elif grade_percentage >= 50:
        letter_grade = "P (Pass)"
    else:
        letter_grade = "F (Fail)"
    
    return {
        "total_score": total_score,
        "max_possible": max_possible_score,
        "percentage": grade_percentage,
        "available_score": available_score,
        "available_max": available_max,
        "available_percentage": available_percentage,
        "letter_grade": letter_grade
    }

def create_markdown_table(results, student_id, simplified=False):
    table = f"# Assessment Results for {student_id}\n\n"
    
    if simplified:
        # Simplified version with only the rubric section and score
        table += "| Rubric Section | Score |\n"
        table += "|----------------|-------|\n"
        
        for section, data in results.items():
            # Add section row
            table += f"| **{section}** | {data['score']} |\n"
            
            # Add subcategory rows
            for subcat, subdata in data['subcategories'].items():
                if subdata['score']:  # Only include subcategories with scores
                    table += f"| - {subcat} | {subdata['score']} |\n"
                else:
                    table += f"| - {subcat} | |\n"  # Keep empty subcategories for manual fill-in
    else:
        # Detailed version with assessment coverage information
        table += "| Rubric Section | Covered in Report | Assessment Type | Score |\n"
        table += "|----------------|-------------------|-----------------|-------|\n"
        
        for section, data in results.items():
            # Add section row
            table += f"| **{section}** | {data['covered']} | {data['assessment_type']} | {data['score']} |\n"
            
            # Add subcategory rows
            for subcat, subdata in data['subcategories'].items():
                table += f"| - {subcat} | | {subdata['status']} | {subdata['score']} |\n"
    
    # Calculate and add total score
    total_info = calculate_total_score(results)
    table += "\n\n## Summary\n\n"
    table += f"**Total Score:** {total_info['total_score']:.1f}/{total_info['max_possible']} ({total_info['percentage']:.1f}%)\n\n"
    table += f"**Available Score:** {total_info['available_score']:.1f}/{total_info['available_max']} ({total_info['available_percentage']:.1f}%)\n\n"
    table += f"**Overall Grade:** {total_info['letter_grade']}\n\n"
    table += "Please refer to the full assessment report for detailed feedback on each component."
    
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
        table += f"{section_name:{section_width}} | {data['score']:{score_width}}\n"
        
        # Add subcategory rows
        for subcat, subdata in data['subcategories'].items():
            # Format subcategory name to remove the percentage
            subcat_name = re.sub(r"\s*\(\d+%\)", "", subcat)
            # Indent subcategories for better readability
            if subdata['score']:
                table += f"  - {subcat_name:{section_width-4}} | {subdata['score']:{score_width}}\n"
            else:
                # Fix: Use empty string with proper width formatting
                table += f"  - {subcat_name:{section_width-4}} | {'':{score_width}}\n"
    
    # Calculate and add total score
    total_info = calculate_total_score(results)
    table += "\n" + "=" * (section_width + score_width + 3) + "\n\n"
    table += "Summary\n"
    table += "-" * 30 + "\n\n"
    table += f"Total Score: {total_info['total_score']:.1f}/{total_info['max_possible']} ({total_info['percentage']:.1f}%)\n"
    table += f"Available Score: {total_info['available_score']:.1f}/{total_info['available_max']} ({total_info['available_percentage']:.1f}%)\n"
    table += f"Overall Grade: {total_info['letter_grade']}\n\n"
    table += "Please refer to the full assessment report for detailed feedback on each component."
    
    return header + table


def process_student(student_id, base_dir, simplified=False, ascii_format=False):
    file_path = Path(f"{base_dir}/{student_id}/final_assessment/{student_id}_final_assessment_report.md")
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    results = extract_results_from_report(file_path)
    
    if ascii_format:
        table_content = create_ascii_table(results, student_id)
        suffix = "_ascii"
    else:
        table_content = create_markdown_table(results, student_id, simplified)
        suffix = "_simple" if simplified else ""
    
    output_file = Path(f"{base_dir}/{student_id}/{student_id}_results_table{suffix}.md")
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
        if process_student(student_id, base_dir, simplified, ascii_format):
            success_count += 1
        else:
            failure_count += 1
    
    print(f"\nProcessing complete: {success_count} successful, {failure_count} failed")

def main():
    parser = argparse.ArgumentParser(description='Extract assessment results for students.')
    parser.add_argument('--base-dir', type=str, default='master_assessment_reports',
                        help='Base directory containing student folders (default: master_assessment_reports)')
    parser.add_argument('--simplified', '--simple', action='store_true',
                        help='Generate a simplified table without assessment coverage details')
    parser.add_argument('--ascii', action='store_true',
                        help='Generate an ASCII-formatted table with fixed-width columns for better alignment')
    
    # Create a mutually exclusive group for student_id or --all
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Process all students')
    group.add_argument('student_id', nargs='?', type=str, help='Student ID to process')
    
    args = parser.parse_args()
    
    if args.all:
        process_all_students(args.base_dir, args.simplified, args.ascii)
    else:
        process_student(args.student_id, args.base_dir, args.simplified, args.ascii)

if __name__ == "__main__" :
    main()

