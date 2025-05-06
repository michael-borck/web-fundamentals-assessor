import os
import requests
import argparse
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode


def validate_html_file(file_path, validator_url="https://validator.w3.org/nu/"):
    """
    Validates an HTML file using the W3C HTML validator API and returns the validation report.
    
    Args:
        file_path: Path to the HTML file to validate
        validator_url: URL of the W3C HTML validator service
        
    Returns:
        Tuple of (file_path, file_type, validation_report, error_count, warning_count)
    """
    print(f"Validating HTML file: {file_path}...")
    
    # Read the HTML file content
    with open(file_path, 'rb') as f:
        html_content = f.read()
    
    # Set up the headers for the validator API
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Accept': 'text/plain'  # Get the response as plain text
    }
    
    # Send the request to the validator
    try:
        response = requests.post(
            validator_url,
            params={'out': 'text'},  # Output format as text
            headers=headers,
            data=html_content,
            timeout=30
        )
        
        if response.status_code == 200:
            report = f"Validated on: {response.headers.get('Date', 'Unknown date')}\n\n"
            report += response.text
            
            # Count errors and warnings
            error_count = response.text.count("Error:")
            warning_count = response.text.count("Warning:")
            
            return (file_path, "HTML", report, error_count, warning_count)
        else:
            error_msg = f"Error: Received status code {response.status_code} from validator\n"
            error_msg += f"Response: {response.text[:200]}...\n"
            return (file_path, "HTML", error_msg, -1, -1)  # -1 indicates validation failed
            
    except requests.exceptions.RequestException as e:
        return (file_path, "HTML", f"Validation failed: {str(e)}\n", -1, -1)


def validate_css_file(file_path, validator_url="https://jigsaw.w3.org/css-validator/validator"):
    """
    Validates a CSS file using the W3C CSS validator API and returns the validation report.
    
    Args:
        file_path: Path to the CSS file to validate
        validator_url: URL of the W3C CSS validator service
        
    Returns:
        Tuple of (file_path, file_type, validation_report, error_count, warning_count)
    """
    print(f"Validating CSS file: {file_path}...")
    
    # Read the CSS file content
    with open(file_path, 'rb') as f:
        css_content = f.read()
    
    # Set up the parameters for the validator API
    params = {
        'profile': 'css3',
        'output': 'text',
        'warning': '2'  # Show all warnings
    }
    
    # Send the request to the validator
    try:
        files = {'file': (os.path.basename(file_path), css_content, 'text/css')}
        
        response = requests.post(
            validator_url,
            params=params,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            report = f"Validated on: {response.headers.get('Date', 'Unknown date')}\n\n"
            report += response.text
            
            # Count errors and warnings in CSS validation results
            # CSS validator output format is different from HTML validator
            error_pattern = r"Errors\s+(\d+)"
            warning_pattern = r"Warnings\s+(\d+)"
            
            error_match = re.search(error_pattern, response.text)
            warning_match = re.search(warning_pattern, response.text)
            
            error_count = int(error_match.group(1)) if error_match else 0
            warning_count = int(warning_match.group(1)) if warning_match else 0
            
            return (file_path, "CSS", report, error_count, warning_count)
        else:
            error_msg = f"Error: Received status code {response.status_code} from validator\n"
            error_msg += f"Response: {response.text[:200]}...\n"
            return (file_path, "CSS", error_msg, -1, -1)
            
    except requests.exceptions.RequestException as e:
        return (file_path, "CSS", f"Validation failed: {str(e)}\n", -1, -1)


def find_files(folder_path, extensions):
    """
    Recursively finds all files with the given extensions in the folder and subfolders.
    
    Args:
        folder_path: Path to the folder to search
        extensions: List of file extensions to find (e.g., ['.html', '.htm'])
    
    Returns:
        List of paths to found files
    """
    found_files = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                found_files.append(os.path.join(root, file))
    
    return found_files


def calculate_validation_score(results, file_type):
    """
    Calculate a validation score (0-10) based on validation results.
    
    Args:
        results: List of validation results for HTML or CSS files
        file_type: "HTML" or "CSS"
        
    Returns:
        Validation score (0-10)
    """
    # Filter results for the specified file type
    type_results = [r for r in results if r[1] == file_type]
    
    if not type_results:
        return 0
    
    # Calculate total files and those with errors
    total_files = len(type_results)
    valid_files = sum(1 for r in type_results if r[3] == 0)  # Files with 0 errors
    warning_only_files = sum(1 for r in type_results if r[3] == 0 and r[4] > 0)  # Files with warnings but no errors
    total_errors = sum(r[3] for r in type_results if r[3] > 0)
    total_warnings = sum(r[4] for r in type_results if r[3] >= 0 and r[4] >= 0)
    
    # Files with validation failures (couldn't be validated)
    failed_validations = sum(1 for r in type_results if r[3] == -1)
    
    # Calculate base score based on percentage of valid files
    valid_percentage = valid_files / total_files if total_files > 0 else 0
    
    # Base score (0-8) based on percentage of valid files
    base_score = valid_percentage * 8
    
    # Adjust score based on warnings and errors
    if total_files > 0:
        # Penalty for files with errors
        error_penalty = min(5, total_errors / total_files)
        
        # Smaller penalty for files with only warnings
        warning_penalty = min(2, (warning_only_files / total_files) * 0.8)
        
        # Penalty for failed validations
        validation_failure_penalty = min(3, (failed_validations / total_files) * 2)
        
        # Calculate final score
        score = base_score - error_penalty - warning_penalty - validation_failure_penalty
        
        # Add bonus points for perfect validation (no errors, no warnings)
        if valid_files == total_files and total_warnings == 0:
            score += 2
        # Add small bonus if all files are valid but have some warnings
        elif valid_files == total_files:
            score += 1
    else:
        score = 0
    
    # Ensure score is within bounds (0-10)
    return max(0, min(10, score))


def map_score_to_rubric(score, max_points):
    """
    Map a normalized score (0-10) to rubric performance levels and points.
    
    Args:
        score: Normalized score (0-10)
        max_points: Maximum points available for this component
        
    Returns:
        Tuple of (performance_level, points, percentage)
    """
    if score >= 8.5:  # 85-100%
        performance = "Distinction (75-100%)"
        percentage = score / 10 * 25 + 75  # Map 8.5-10 to 75-100%
        points = max_points * percentage / 100
    elif score >= 7:  # 70-85%
        performance = "Credit (65-74%)"
        percentage = (score - 7) / 1.5 * 9 + 65  # Map 7-8.5 to 65-74%
        points = max_points * percentage / 100
    elif score >= 5:  # 50-70%
        performance = "Pass (50-64%)"
        percentage = (score - 5) / 2 * 14 + 50  # Map 5-7 to 50-64%
        points = max_points * percentage / 100
    else:  # 0-50%
        performance = "Fail (0-49%)"
        percentage = score / 5 * 49  # Map 0-5 to 0-49%
        points = max_points * percentage / 100
    
    return (performance, round(points, 2), round(percentage, 1))


def create_markdown_report(validation_results, output_file):
    """
    Creates a single Markdown file with all validation reports.
    
    Args:
        validation_results: List of (file_path, file_type, report, error_count, warning_count) tuples
        output_file: Path to the output Markdown file
    """
    # Group results by file type
    html_results = [r for r in validation_results if r[1] == "HTML"]
    css_results = [r for r in validation_results if r[1] == "CSS"]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"# Web Validation Report Summary\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total files validated: {len(validation_results)}\n")
        f.write(f"* HTML files: {len(html_results)}\n")
        f.write(f"* CSS files: {len(css_results)}\n\n")
        
        # Calculate validation scores
        html_score = calculate_validation_score(validation_results, "HTML")
        css_score = calculate_validation_score(validation_results, "CSS")
        combined_score = (html_score * len(html_results) + css_score * len(css_results)) / max(1, len(validation_results))
        
        # Map scores to rubric levels
        html_performance, html_points, html_percentage = map_score_to_rubric(html_score, 10)
        css_performance, css_points, css_percentage = map_score_to_rubric(css_score, 10)
        combined_performance, combined_points, combined_percentage = map_score_to_rubric(combined_score, 10)
        
        # Write validation scores
        f.write("## Validation Scores\n\n")
        f.write("| File Type | Score (0-10) | Performance Level | Percentage | Points (max 10) |\n")
        f.write("|-----------|--------------|-------------------|------------|----------------|\n")
        f.write(f"| HTML | {html_score:.2f} | {html_performance} | {html_percentage}% | {html_points} |\n")
        f.write(f"| CSS | {css_score:.2f} | {css_performance} | {css_percentage}% | {css_points} |\n")
        f.write(f"| Combined | {combined_score:.2f} | {combined_performance} | {combined_percentage}% | {combined_points} |\n\n")
        
        # Add score interpretation
        f.write("### Score Interpretation\n\n")
        f.write("The validation score (0-10) is calculated based on:\n\n")
        f.write("- Percentage of files with no errors\n")
        f.write("- Number of errors per file\n")
        f.write("- Number of warnings per file\n")
        f.write("- Validation failures\n\n")
        
        f.write("The score is then mapped to the rubric performance levels:\n\n")
        f.write("| Score Range | Performance Level | Percentage | Description |\n")
        f.write("|-------------|-------------------|------------|-------------|\n")
        f.write("| 8.5-10 | Distinction | 75-100% | Excellent code quality with few or no errors |\n")
        f.write("| 7-8.49 | Credit | 65-74% | Good code quality with minor issues |\n")
        f.write("| 5-6.99 | Pass | 50-64% | Acceptable code quality with some issues |\n")
        f.write("| 0-4.99 | Fail | 0-49% | Poor code quality with significant issues |\n\n")
        
        # Create summary table
        f.write("## Validation Summary\n\n")
        f.write("| File | Type | Errors | Warnings | Status |\n")
        f.write("|------|------|--------|----------|--------|\n")
        
        for file_path, file_type, _, error_count, warning_count in validation_results:
            file_name = os.path.relpath(file_path)
            
            # Determine status
            if error_count == -1:
                status = "❌ Failed to validate"
                error_count = "N/A"
                warning_count = "N/A"
            elif error_count == 0:
                status = "✅ Valid"
            else:
                status = "⚠️ Invalid"
            
            f.write(f"| {file_name} | {file_type} | {error_count} | {warning_count} | {status} |\n")
        
        f.write("\n")
        
        # Create table of contents
        f.write("## Table of Contents\n\n")
        
        # HTML files in TOC
        if html_results:
            f.write("### HTML Files\n\n")
            for idx, (file_path, _, _, _, _) in enumerate(html_results, 1):
                file_name = os.path.relpath(file_path)
                anchor = file_name.replace(' ', '-').replace('.', '').replace('/', '-').lower()
                f.write(f"{idx}. [{file_name}](#{anchor})\n")
            f.write("\n")
        
        # CSS files in TOC
        if css_results:
            f.write("### CSS Files\n\n")
            for idx, (file_path, _, _, _, _) in enumerate(css_results, 1):
                file_name = os.path.relpath(file_path)
                anchor = file_name.replace(' ', '-').replace('.', '').replace('/', '-').lower()
                f.write(f"{idx}. [{file_name}](#{anchor})\n")
            f.write("\n")
        
        f.write("\n---\n\n")
        
        # HTML validation reports
        if html_results:
            f.write("# HTML Validation Results\n\n")
            for file_path, _, report, error_count, warning_count in html_results:
                file_name = os.path.relpath(file_path)
                anchor = file_name.replace(' ', '-').replace('.', '').replace('/', '-').lower()
                f.write(f"<h2 id='{anchor}'>{file_name}</h2>\n\n")
                
                # Add a summary for this file
                if error_count == -1:
                    status = "❌ Failed to validate"
                    error_count = "N/A"
                    warning_count = "N/A"
                elif error_count == 0:
                    status = "✅ Valid"
                else:
                    status = "⚠️ Invalid"
                
                f.write(f"**Status:** {status}  \n")
                f.write(f"**Errors:** {error_count}  \n")
                f.write(f"**Warnings:** {warning_count}  \n\n")
                
                f.write("```\n")  # Code block for formatting
                f.write(report)
                f.write("\n```\n\n")
                f.write("---\n\n")  # Separator between reports
        
        # CSS validation reports
        if css_results:
            f.write("# CSS Validation Results\n\n")
            for file_path, _, report, error_count, warning_count in css_results:
                file_name = os.path.relpath(file_path)
                anchor = file_name.replace(' ', '-').replace('.', '').replace('/', '-').lower()
                f.write(f"<h2 id='{anchor}'>{file_name}</h2>\n\n")
                
                # Add a summary for this file
                if error_count == -1:
                    status = "❌ Failed to validate"
                    error_count = "N/A"
                    warning_count = "N/A"
                elif error_count == 0:
                    status = "✅ Valid"
                else:
                    status = "⚠️ Invalid"
                
                f.write(f"**Status:** {status}  \n")
                f.write(f"**Errors:** {error_count}  \n")
                f.write(f"**Warnings:** {warning_count}  \n\n")
                
                f.write("```\n")  # Code block for formatting
                f.write(report)
                f.write("\n```\n\n")
                f.write("---\n\n")  # Separator between reports


def create_summary_only_report(validation_results, output_file):
    """
    Creates a Markdown file with just the summary table of validation results.
    
    Args:
        validation_results: List of (file_path, file_type, report, error_count, warning_count) tuples
        output_file: Path to the output Markdown file
    """
    # Group results by file type
    html_results = [r for r in validation_results if r[1] == "HTML"]
    css_results = [r for r in validation_results if r[1] == "CSS"]
    
    # Sort results by error count (highest first), then warning count, then filename
    sorted_results = sorted(
        validation_results, 
        key=lambda x: (-1 if x[3] == -1 else x[3], -1 if x[4] == -1 else x[4], os.path.relpath(x[0]))
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"# Web Validation Summary Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Calculate validation scores
        html_score = calculate_validation_score(validation_results, "HTML")
        css_score = calculate_validation_score(validation_results, "CSS")
        combined_score = (html_score * len(html_results) + css_score * len(css_results)) / max(1, len(validation_results))
        
        # Map scores to rubric levels
        html_performance, html_points, html_percentage = map_score_to_rubric(html_score, 10)
        css_performance, css_points, css_percentage = map_score_to_rubric(css_score, 10)
        combined_performance, combined_points, combined_percentage = map_score_to_rubric(combined_score, 10)
        
        # Write validation scores
        f.write("## Rubric Assessment\n\n")
        f.write("### Code Quality (based on validation)\n\n")
        f.write("| Code Type | Score (0-10) | Performance Level | Percentage | Points (max 10) |\n")
        f.write("|-----------|--------------|-------------------|------------|----------------|\n")
        f.write(f"| HTML | {html_score:.2f} | {html_performance} | {html_percentage}% | {html_points} |\n")
        f.write(f"| CSS | {css_score:.2f} | {css_performance} | {css_percentage}% | {css_points} |\n")
        f.write(f"| Combined | {combined_score:.2f} | {combined_performance} | {combined_percentage}% | {combined_points} |\n\n")
        
        # Statistics
        total_errors = sum(r[3] for r in validation_results if r[3] != -1)
        total_warnings = sum(r[4] for r in validation_results if r[4] != -1)
        valid_files = sum(1 for r in validation_results if r[3] == 0 and r[3] != -1)
        invalid_files = sum(1 for r in validation_results if r[3] > 0)
        failed_validations = sum(1 for r in validation_results if r[3] == -1)
        
        f.write(f"## Statistics\n\n")
        f.write(f"- **Total files validated:** {len(validation_results)}\n")
        f.write(f"  - HTML files: {len(html_results)}\n")
        f.write(f"  - CSS files: {len(css_results)}\n")
        f.write(f"- **Valid files:** {valid_files} ({valid_files/len(validation_results)*100:.1f}%)\n")
        f.write(f"- **Invalid files:** {invalid_files} ({invalid_files/len(validation_results)*100:.1f}%)\n")
        f.write(f"- **Failed validations:** {failed_validations}\n")
        f.write(f"- **Total errors:** {total_errors}\n")
        f.write(f"- **Total warnings:** {total_warnings}\n\n")
        
        # Create summary table
        f.write("## Validation Results\n\n")
        f.write("| File | Type | Errors | Warnings | Status |\n")
        f.write("|------|------|--------|----------|--------|\n")
        
        for file_path, file_type, _, error_count, warning_count in sorted_results:
            file_name = os.path.relpath(file_path)
            
            # Determine status
            if error_count == -1:
                status = "❌ Failed to validate"
                error_count = "N/A"
                warning_count = "N/A"
            elif error_count == 0:
                status = "✅ Valid"
            else:
                status = "⚠️ Invalid"
            
            f.write(f"| {file_name} | {file_type} | {error_count} | {warning_count} | {status} |\n")


def create_rubric_report(validation_results, output_file):
    """
    Creates a Markdown file with a rubric-focused assessment.
    
    Args:
        validation_results: List of (file_path, file_type, report, error_count, warning_count) tuples
        output_file: Path to the output Markdown file
    """
    # Group results by file type
    html_results = [r for r in validation_results if r[1] == "HTML"]
    css_results = [r for r in validation_results if r[1] == "CSS"]
    
    # Calculate validation scores
    html_score = calculate_validation_score(validation_results, "HTML")
    css_score = calculate_validation_score(validation_results, "CSS")
    combined_score = (html_score * len(html_results) + css_score * len(css_results)) / max(1, len(validation_results))
    
    # Map scores to rubric performance levels
    _, combined_points, _ = map_score_to_rubric(combined_score, 10)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"# Code Quality Assessment (Based on Validation)\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Calculate relevant statistics
        total_files = len(validation_results)
        valid_html = sum(1 for r in html_results if r[3] == 0 and r[3] != -1)
        valid_css = sum(1 for r in css_results if r[3] == 0 and r[3] != -1)
        
        # Map to rubric criteria
        f.write("## Assessment According to Rubric\n\n")
        
        # Code organization and documentation (5%)
        code_org_score = combined_score * 0.5  # Scale from 0-10 to 0-5
        code_org_performance, code_org_points, _ = map_score_to_rubric(combined_score, 5)
        
        f.write("### Code Organisation and Documentation (5%)\n\n")
        f.write(f"**Score:** {code_org_score:.2f}/5 ({code_org_performance})\n\n")
        f.write("| Performance Level | Description | Points |\n")
        f.write("|-------------------|-------------|--------|\n")
        f.write("| Distinction (75-100%) | Expertly structured code with comprehensive, professional documentation | 3.75-5 |\n")
        f.write("| Credit (65-74%) | Well-organised code with good documentation | 3.25-3.74 |\n")
        f.write("| Pass (50-64%) | Basic organisation and minimal comments | 2.5-3.24 |\n")
        f.write("| Fail (0-49%) | Poorly organised code with inadequate documentation | 0-2.49 |\n\n")
        
        f.write("### Assessment Criteria\n\n")
        f.write("The code quality score is based on W3C validation results:\n\n")
        
        f.write(f"- **HTML Files:** {len(html_results)} files, {valid_html} valid ({valid_html/max(1, len(html_results))*100:.1f}%)\n")
        f.write(f"- **CSS Files:** {len(css_results)} files, {valid_css} valid ({valid_css/max(1, len(css_results))*100:.1f}%)\n")
        f.write(f"- **Combined Score:** {combined_score:.2f}/10\n\n")
        
        f.write("### Recommendations for Improvement\n\n")
        
        # Calculate recommendations based on error patterns
        error_patterns = {}
        warning_patterns = {}
        
        # Find common error types
        for file_path, file_type, report, error_count, warning_count in validation_results:
            if error_count > 0 and report:
                lines = report.split('\n')
                for line in lines:
                    if 'Error:' in line:
                        error_type = line.split('Error:')[1].strip()
                        error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
                    elif 'Warning:' in line:
                        warning_type = line.split('Warning:')[1].strip()
                        warning_patterns[warning_type] = warning_patterns.get(warning_type, 0) + 1
        
        # Sort errors by frequency
        sorted_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
        sorted_warnings = sorted(warning_patterns.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_errors:
            f.write("#### Common HTML/CSS Validation Errors:\n\n")
            for error, count in sorted_errors[:5]:  # Top 5 errors
                f.write(f"- **{error}** ({count} occurrences)\n")
            f.write("\n")
        
        if sorted_warnings:
            f.write("#### Common HTML/CSS Validation Warnings:\n\n")
            for warning, count in sorted_warnings[:5]:  # Top 5 warnings
                f.write(f"- **{warning}** ({count} occurrences)\n")
            f.write("\n")
        
        # Give specific improvement advice
        f.write("#### Key Improvement Areas:\n\n")
        
        if valid_html < len(html_results):
            f.write("1. **HTML Validation**: Fix HTML errors to ensure compliant, semantic markup\n")
            
        if valid_css < len(css_results):
            f.write("2. **CSS Validation**: Address CSS issues to ensure cross-browser compatibility\n")
        
        f.write("3. **Best Practices**: Follow HTML5 and CSS3 best practices for maintainable code\n")
        f.write("4. **Documentation**: Add appropriate comments to explain complex code sections\n")
        
        # Summary
        f.write("\n## Summary\n\n")
        f.write(f"Based on W3C validation results, this project demonstrates " + 
                f"{'excellent' if combined_score >= 8.5 else 'good' if combined_score >= 7 else 'acceptable' if combined_score >= 5 else 'poor'} " +
                f"code quality. The overall score of {combined_score:.2f}/10 translates to {combined_points}/10 points on the rubric assessment scale.\n\n")
        
        if combined_score < 8.5:
            f.write("To improve the code quality score, prioritize fixing validation errors and following web standards more closely.")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Validate HTML and CSS files in a folder recursively')
    parser.add_argument('folder', help='Folder containing files to validate')
    parser.add_argument('--output', '-o', default='validation_report.md', 
                        help='Path for the output Markdown report (default: validation_report.md)')
    parser.add_argument('--summary', '-s', default='validation_summary.md',
                        help='Path for the summary-only report (default: validation_summary.md)')
    parser.add_argument('--rubric', '-r', default='validation_rubric.md',
                        help='Path for the rubric assessment report (default: validation_rubric.md)')
    parser.add_argument('--html-validator', default='https://validator.w3.org/nu/',
                        help='URL of the W3C HTML validator service (default: https://validator.w3.org/nu/)')
    parser.add_argument('--css-validator', default='https://jigsaw.w3.org/css-validator/validator',
                        help='URL of the W3C CSS validator service (default: https://jigsaw.w3.org/css-validator/validator)')
    parser.add_argument('--html-only', action='store_true', help='Validate only HTML files')
    parser.add_argument('--css-only', action='store_true', help='Validate only CSS files')
    parser.add_argument('--parallel', '-p', type=int, default=1,
                        help='Number of parallel validation processes (default: 1)')
    parser.add_argument('--individual', '-i', action='store_true',
                        help='Also save individual validation reports')
    parser.add_argument('--individual-dir', '-d', default='validation_reports',
                        help='Directory for individual reports if enabled (default: validation_reports)')
    parser.add_argument('--summary-only', action='store_true',
                        help='Generate only the summary report without detailed validation reports')
    
    args = parser.parse_args()
    
    # Determine which file types to validate
    validate_html = not args.css_only
    validate_css = not args.html_only
    
    # Find all files to validate
    files_to_validate = []
    if validate_html:
        html_files = find_files(args.folder, ['.html', '.htm'])
        print(f"Found {len(html_files)} HTML files to validate")
        files_to_validate.extend((file_path, 'HTML') for file_path in html_files)
    
    if validate_css:
        css_files = find_files(args.folder, ['.css'])
        print(f"Found {len(css_files)} CSS files to validate")
        files_to_validate.extend((file_path, 'CSS') for file_path in css_files)
    
    validation_results = []
    
    if args.parallel > 1:
        # Parallel processing using concurrent.futures
        from concurrent.futures import ThreadPoolExecutor
        import concurrent.futures
        
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = []
            
            for file_path, file_type in files_to_validate:
                if file_type == 'HTML':
                    futures.append(executor.submit(validate_html_file, file_path, args.html_validator))
                else:  # CSS
                    futures.append(executor.submit(validate_css_file, file_path, args.css_validator))
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                validation_results.append(result)
                print(f"Completed validation for {result[0]}")
    else:
        # Sequential processing
        for file_path, file_type in files_to_validate:
            if file_type == 'HTML':
                result = validate_html_file(file_path, args.html_validator)
            else:  # CSS
                result = validate_css_file(file_path, args.css_validator)
            validation_results.append(result)
    
    # Create the consolidated Markdown report
    if not args.summary_only:
        create_markdown_report(validation_results, args.output)
        print(f"Consolidated report saved to {args.output}")
    
    # Create the summary-only report
    create_summary_only_report(validation_results, args.summary)
    print(f"Summary report saved to {args.summary}")
    
    # Create the rubric assessment report
    create_rubric_report(validation_results, args.rubric)
    print(f"Rubric assessment saved to {args.rubric}")
    
    # Optionally save individual reports
    if args.individual:
        os.makedirs(args.individual_dir, exist_ok=True)
        
        for file_path, file_type, report, _, _ in validation_results:
            relative_path = os.path.relpath(file_path, args.folder)
            output_file = os.path.join(args.individual_dir, f"{relative_path}.{file_type.lower()}-validation.txt")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Validation report for: {file_path}\n")
                f.write(report)
                
            print(f"Individual report saved to {output_file}")
    
    print("Validation complete!")
