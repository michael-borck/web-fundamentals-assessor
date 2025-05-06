import os
import argparse
import re
import json
from pathlib import Path
import requests
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class AccessibilityChecker:
    def __init__(self, output_dir="accessibility_reports"):
        """
        Initialize the accessibility checker.
        
        Args:
            output_dir: Directory to save accessibility reports
        """
        self.output_dir = output_dir
        self.axe_core_enabled = False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define patterns for semantic HTML tags
        self.semantic_tags = [
            "header", "nav", "main", "article", "section", "aside", "footer",
            "figure", "figcaption", "details", "summary", "time", "mark"
        ]
        
        # Define patterns for ARIA attributes
        self.aria_attributes = [
            "aria-label", "aria-labelledby", "aria-describedby", "aria-hidden",
            "aria-expanded", "aria-controls", "aria-live", "aria-required",
            "aria-disabled", "aria-checked", "aria-selected", "role"
        ]
        
        # Common accessibility issues to check for
        self.accessibility_checks = {
            "images_without_alt": {"regex": r"<img(?!.*?alt=(['\"])).*?>", "explanation": "Images should have alt attributes"},
            "empty_alt": {"regex": r"<img.*?alt=['\"][\s]*?['\"].*?>", "explanation": "Alt attributes should not be empty for meaningful images"},
            "no_lang_attribute": {"regex": r"<html(?!.*?lang=(['\"])).*?>", "explanation": "HTML tag should have a lang attribute"},
            "low_contrast_classes": {"regex": r"class=['\"].*?(text-light|text-white|text-muted|text-secondary|bg-dark|bg-secondary).*?['\"]", "explanation": "Potential low contrast text/background combinations"},
            "tab_index_positive": {"regex": r"tabindex=['\"][1-9][0-9]*['\"]", "explanation": "Avoid positive tabindex values as they disrupt natural tab order"},
            "missing_form_labels": {"regex": r"<(input|select|textarea)(?!.*?(aria-label|aria-labelledby|id)).*?>", "explanation": "Form elements should have associated labels"},
        }
    
    def check_html_file(self, file_path):
        """
        Analyze an HTML file for accessibility issues.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Dictionary with accessibility analysis results
        """
        print(f"Checking accessibility for: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Initialize results
            issues = []
            semantic_tag_count = 0
            aria_attribute_count = 0
            total_semantic_elements = 0
            total_interactive_elements = 0
            
            # Count semantic tags
            for tag in self.semantic_tags:
                count = len(soup.find_all(tag))
                semantic_tag_count += count
                total_semantic_elements += count
            
            # Count ARIA attributes
            for attr in self.aria_attributes:
                count = len(soup.find_all(attrs={attr: True}))
                aria_attribute_count += count
            
            # Count interactive elements
            interactive_tags = ["a", "button", "input", "select", "textarea"]
            for tag in interactive_tags:
                total_interactive_elements += len(soup.find_all(tag))
            
            # Run regex-based accessibility checks
            for issue_type, check in self.accessibility_checks.items():
                matches = re.findall(check["regex"], html_content)
                if matches:
                    issues.append({
                        "type": issue_type,
                        "explanation": check["explanation"],
                        "count": len(matches)
                    })
            
            # Check for proper heading structure
            headings = []
            for i in range(1, 7):
                headings.extend([(i, h.text.strip()) for h in soup.find_all(f'h{i}')])
            
            # Sort headings by their position in the document
            headings_ordered = []
            for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                level = int(h_tag.name[1])
                headings_ordered.append((level, h_tag.text.strip()))
            
            # Check for proper heading hierarchy
            heading_issues = []
            prev_level = 0
            for i, (level, text) in enumerate(headings_ordered):
                if i == 0 and level > 1:
                    heading_issues.append(f"Document does not start with an h1 (starts with h{level})")
                elif i > 0 and level > prev_level + 1:
                    heading_issues.append(f"Heading level jumps from h{prev_level} to h{level} (skipping levels)")
                prev_level = level
            
            # Calculate color contrast (basic detection, not accurate)
            style_tags = soup.find_all('style')
            inline_styles = soup.find_all(style=True)
            color_contrast_issues = []
            
            # Detect potential color contrast issues in style tags
            for style in style_tags:
                text = style.string
                if text and re.search(r'color:\s*#([0-9a-f]{3}|[0-9a-f]{6})\s*;.*background(-color)?:\s*#([0-9a-f]{3}|[0-9a-f]{6})', text, re.IGNORECASE):
                    color_contrast_issues.append("Potential color contrast issue in style tag")
            
            # Check for keyboard navigation on interactive elements
            keyboard_nav_issues = []
            for a in soup.find_all('a', href=True):
                if 'onclick' in a.attrs and not a.get('tabindex') and not a.get('role'):
                    keyboard_nav_issues.append("Link with onclick but no keyboard support")
                if a.get('tabindex') == '-1' and not a.get('aria-hidden'):
                    keyboard_nav_issues.append("Link removed from keyboard navigation without hiding from assistive tech")
            
            for button in soup.find_all('div', attrs={'onclick': True}):
                if not button.get('role') == 'button' and not button.get('tabindex'):
                    keyboard_nav_issues.append("Div with onclick but missing role=button and keyboard support")
            
            # Check for skip links
            has_skip_link = bool(soup.find('a', attrs={'href': '#main'}) or 
                               soup.find('a', attrs={'href': '#content'}) or
                               soup.find('a', string=re.compile('skip.*navigation', re.IGNORECASE)))
            
            # Calculate a basic accessibility score
            score = self._calculate_score(
                semantic_tag_count, 
                aria_attribute_count, 
                len(issues),
                len(heading_issues), 
                len(keyboard_nav_issues),
                has_skip_link,
                total_interactive_elements
            )
            
            return {
                "file_path": file_path,
                "semantic_tag_count": semantic_tag_count,
                "aria_attribute_count": aria_attribute_count,
                "issues": issues,
                "heading_structure": {
                    "headings": headings,
                    "issues": heading_issues
                },
                "keyboard_navigation": {
                    "issues": keyboard_nav_issues
                },
                "has_skip_link": has_skip_link,
                "color_contrast_issues": color_contrast_issues,
                "basic_score": score
            }
        
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    def _calculate_score(self, semantic_tags, aria_attrs, issues_count, heading_issues, keyboard_issues, has_skip_link, interactive_count):
        """
        Calculate a basic accessibility score (0-100).
        
        This is a simplified scoring method and should not replace professional audits.
        """
        # Base points
        score = 70
        
        # Add points for semantic HTML and ARIA
        if semantic_tags >= 5:
            score += 10
        elif semantic_tags > 0:
            score += semantic_tags * 2
        
        # ARIA attributes (but avoid overuse)
        if interactive_count > 0:
            aria_ratio = min(aria_attrs / interactive_count, 1.5)  # Cap at 1.5 ratio
            if aria_ratio > 0.5:
                score += 10 * (aria_ratio / 1.5)
        
        # Deduct for issues
        score -= issues_count * 3
        score -= heading_issues * 4
        score -= keyboard_issues * 5
        
        # Add for skip link
        if has_skip_link:
            score += 5
        
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    def find_html_files(self, folder_path):
        """
        Recursively find all HTML files in a folder.
        
        Args:
            folder_path: Path to the folder to search
            
        Returns:
            List of HTML file paths
        """
        html_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        return html_files
    
    def check_folder(self, folder_path):
        """
        Check all HTML files in a folder for accessibility issues.
        
        Args:
            folder_path: Path to the folder to check
            
        Returns:
            List of accessibility analysis results
        """
        html_files = self.find_html_files(folder_path)
        print(f"Found {len(html_files)} HTML files to check")
        
        results = []
        for file_path in html_files:
            result = self.check_html_file(file_path)
            results.append(result)
        
        return results
    
    def generate_report(self, results, output_file):
        """
        Generate a Markdown report of accessibility analysis results.
        
        Args:
            results: List of accessibility analysis results
            output_file: Path to save the report
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Web Accessibility Analysis Report\n\n")
            
            # Calculate overall stats
            files_checked = len(results)
            overall_score = sum(r.get("basic_score", 0) for r in results if "basic_score" in r) / max(1, files_checked)
            
            # Write summary
            f.write(f"## Summary\n\n")
            f.write(f"- **Files Checked:** {files_checked}\n")
            f.write(f"- **Average Accessibility Score:** {overall_score:.2f}/100\n\n")
            
            # Create WCAG 2.1 AA compliance score based on our basic analysis
            wcag_score = self._calculate_wcag_score(results)
            f.write(f"- **Estimated WCAG 2.1 AA Compliance:** {wcag_score}/5\n\n")
            
            # Add score interpretation
            f.write("### Score Interpretation\n\n")
            f.write("| Score Range | Interpretation |\n")
            f.write("|-------------|---------------|\n")
            f.write("| 90-100 | Excellent accessibility, likely meets WCAG 2.1 AA |\n")
            f.write("| 75-89 | Good accessibility, minor issues to address |\n")
            f.write("| 60-74 | Moderate accessibility, several issues to address |\n")
            f.write("| 40-59 | Poor accessibility, significant improvements needed |\n")
            f.write("| 0-39 | Very poor accessibility, major remediation required |\n\n")
            
            # Overall recommendations
            f.write("### Overall Recommendations\n\n")
            all_issues = []
            for result in results:
                if "issues" in result:
                    all_issues.extend(result["issues"])
            
            if all_issues:
                common_issues = {}
                for issue in all_issues:
                    issue_type = issue["type"]
                    if issue_type in common_issues:
                        common_issues[issue_type]["count"] += issue["count"]
                    else:
                        common_issues[issue_type] = {
                            "explanation": issue["explanation"],
                            "count": issue["count"]
                        }
                
                # Sort issues by count (most frequent first)
                sorted_issues = sorted(common_issues.items(), key=lambda x: x[1]["count"], reverse=True)
                
                f.write("1. **Top issues to address:**\n")
                for issue_type, info in sorted_issues[:5]:  # Top 5 issues
                    f.write(f"   - {info['explanation']} ({info['count']} occurrences)\n")
                
                f.write("\n2. **General recommendations:**\n")
                if not any(r.get("has_skip_link", False) for r in results):
                    f.write("   - Add skip navigation links for keyboard users\n")
                
                heading_issues = sum(len(r.get("heading_structure", {}).get("issues", [])) for r in results)
                if heading_issues > 0:
                    f.write("   - Fix heading structure to ensure proper document outline\n")
                
                keyboard_issues = sum(len(r.get("keyboard_navigation", {}).get("issues", [])) for r in results)
                if keyboard_issues > 0:
                    f.write("   - Improve keyboard navigation for interactive elements\n")
            
            # File-specific results
            f.write("\n## File Analysis\n\n")
            
            # Sort results by score (worst first to focus on biggest issues)
            sorted_results = sorted(results, key=lambda r: r.get("basic_score", 100))
            
            for result in sorted_results:
                file_path = result["file_path"]
                rel_path = os.path.relpath(file_path)
                
                if "error" in result:
                    f.write(f"### {rel_path}\n\n")
                    f.write(f"Error analyzing file: {result['error']}\n\n")
                    continue
                
                score = result.get("basic_score", 0)
                f.write(f"### {rel_path}\n\n")
                f.write(f"**Accessibility Score:** {score:.2f}/100\n\n")
                
                # Semantic HTML usage
                semantic_count = result.get("semantic_tag_count", 0)
                aria_count = result.get("aria_attribute_count", 0)
                f.write(f"**Semantic HTML:** {semantic_count} semantic elements, {aria_count} ARIA attributes\n\n")
                
                # Issues
                if result.get("issues"):
                    f.write("**Issues:**\n\n")
                    for issue in result["issues"]:
                        f.write(f"- {issue['explanation']} ({issue['count']} occurrences)\n")
                    f.write("\n")
                
                # Heading structure
                if result.get("heading_structure", {}).get("issues"):
                    f.write("**Heading Structure Issues:**\n\n")
                    for issue in result["heading_structure"]["issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")
                
                # Keyboard navigation
                if result.get("keyboard_navigation", {}).get("issues"):
                    f.write("**Keyboard Navigation Issues:**\n\n")
                    for issue in result["keyboard_navigation"]["issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")
                
                # Color contrast
                if result.get("color_contrast_issues"):
                    f.write("**Potential Color Contrast Issues:**\n\n")
                    for issue in result["color_contrast_issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")
                
                # Skip links
                f.write(f"**Skip Navigation Link:** {'Present' if result.get('has_skip_link', False) else 'Missing'}\n\n")
                f.write("---\n\n")
    
    def _calculate_wcag_score(self, results):
        """
        Calculate an estimated WCAG 2.1 AA compliance score (0-5).
        """
        if not results:
            return 0
        
        avg_score = sum(r.get("basic_score", 0) for r in results if "basic_score" in r) / len(results)
        
        # Convert the average score (0-100) to a WCAG score (0-5)
        if avg_score >= 90:
            return 5  # Excellent
        elif avg_score >= 80:
            return 4  # Very Good
        elif avg_score >= 70:
            return 3  # Good
        elif avg_score >= 60:
            return 2.5  # Satisfactory
        elif avg_score >= 50:
            return 2  # Needs Improvement
        elif avg_score >= 30:
            return 1  # Poor
        else:
            return 0  # Very Poor
    
    def generate_csv_report(self, results, output_file):
        """
        Generate a CSV report of accessibility analysis results.
        
        Args:
            results: List of accessibility analysis results
            output_file: Path to save the CSV report
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'File', 'Accessibility Score', 'Semantic Elements', 'ARIA Attributes',
                'Issues Count', 'Heading Issues', 'Keyboard Issues', 'Has Skip Link',
                'WCAG 2.1 AA Estimate (0-5)'
            ])
            
            # Write data for each file
            for result in results:
                if "error" in result:
                    writer.writerow([
                        os.path.relpath(result["file_path"]), 
                        'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error'
                    ])
                    continue
                
                writer.writerow([
                    os.path.relpath(result["file_path"]),
                    f"{result.get('basic_score', 0):.2f}",
                    result.get("semantic_tag_count", 0),
                    result.get("aria_attribute_count", 0),
                    sum(issue["count"] for issue in result.get("issues", [])),
                    len(result.get("heading_structure", {}).get("issues", [])),
                    len(result.get("keyboard_navigation", {}).get("issues", [])),
                    "Yes" if result.get("has_skip_link", False) else "No",
                    self._calculate_file_wcag_score(result)
                ])
    
    def _calculate_file_wcag_score(self, result):
        """
        Calculate an estimated WCAG 2.1 AA compliance score (0-5) for a single file.
        """
        if "basic_score" not in result:
            return 0
        
        score = result["basic_score"]
        
        # Convert the score (0-100) to a WCAG score (0-5)
        if score >= 90:
            return 5  # Excellent
        elif score >= 80:
            return 4  # Very Good
        elif score >= 70:
            return 3  # Good
        elif score >= 60:
            return 2.5  # Satisfactory
        elif score >= 50:
            return 2  # Needs Improvement
        elif score >= 30:
            return 1  # Poor
        else:
            return 0  # Very Poor
    
    def generate_summary_report(self, results, output_file):
        """
        Generate a summary Markdown report with just the key accessibility metrics.
        
        Args:
            results: List of accessibility analysis results
            output_file: Path to save the report
        """
        # Calculate overall stats
        files_checked = len(results)
        overall_score = sum(r.get("basic_score", 0) for r in results if "basic_score" in r) / max(1, files_checked)
        wcag_score = self._calculate_wcag_score(results)
        
        # Map WCAG score to rubric performance level
        wcag_performance = ""
        if wcag_score >= 4.5:
            wcag_performance = "Distinction (75-100%)"
        elif wcag_score >= 3.5:
            wcag_performance = "Credit (65-74%)"
        elif wcag_score >= 2.5:
            wcag_performance = "Pass (50-64%)"
        else:
            wcag_performance = "Fail (0-49%)"
        
        # Calculate semantic HTML metrics
        total_semantic = sum(r.get("semantic_tag_count", 0) for r in results if "semantic_tag_count" in r)
        total_aria = sum(r.get("aria_attribute_count", 0) for r in results if "aria_attribute_count" in r)
        
        # Map semantic HTML to rubric performance level
        semantic_performance = ""
        avg_semantic_per_file = total_semantic / max(1, files_checked)
        if avg_semantic_per_file >= 8 and total_aria >= files_checked * 3:
            semantic_performance = "Distinction (75-100%)"
        elif avg_semantic_per_file >= 5 and total_aria >= files_checked:
            semantic_performance = "Credit (65-74%)"
        elif avg_semantic_per_file >= 3:
            semantic_performance = "Pass (50-64%)"
        else:
            semantic_performance = "Fail (0-49%)"
        
        # Calculate accessibility navigation metrics
        skip_links = sum(1 for r in results if r.get("has_skip_link", False))
        keyboard_issues = sum(len(r.get("keyboard_navigation", {}).get("issues", [])) for r in results)
        
        # Map navigation accessibility to rubric performance level
        nav_performance = ""
        if skip_links >= files_checked * 0.8 and keyboard_issues <= files_checked * 0.5:
            nav_performance = "Distinction (75-100%)"
        elif skip_links >= files_checked * 0.5 and keyboard_issues <= files_checked:
            nav_performance = "Credit (65-74%)"
        elif skip_links > 0 or keyboard_issues <= files_checked * 2:
            nav_performance = "Pass (50-64%)"
        else:
            nav_performance = "Fail (0-49%)"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Accessibility Evaluation Summary\n\n")
            
            f.write("## Overview\n\n")
            f.write(f"- **Files Analyzed:** {files_checked}\n")
            f.write(f"- **Average Accessibility Score:** {overall_score:.2f}/100\n")
            f.write(f"- **WCAG 2.1 AA Compliance Score:** {wcag_score}/5\n\n")
            
            f.write("## Rubric Evaluation\n\n")
            
            f.write("### WCAG 2.1 AA Compliance (5%)\n\n")
            f.write(f"**Performance Level:** {wcag_performance}\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Exceeds WCAG 2.1 AA standards; approaches AAA compliance in key areas | 3.75-5 |\n")
            f.write("| Credit (65-74%) | Fully compliant with WCAG 2.1 AA standards | 3.25-3.74 |\n")
            f.write("| Pass (50-64%) | Meets most basic WCAG 2.1 AA requirements | 2.5-3.24 |\n")
            f.write("| Fail (0-49%) | Fails to meet basic accessibility requirements | 0-2.49 |\n\n")
            
            f.write("### Proper Semantic Tags and ARIA Attributes (3%)\n\n")
            f.write(f"**Performance Level:** {semantic_performance}\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Expert implementation of semantic HTML with optimal tag selection for all content types | 2.25-3 |\n")
            f.write("| Credit (65-74%) | Comprehensive use of semantic tags throughout the site | 1.95-2.24 |\n")
            f.write("| Pass (50-64%) | Basic semantic structure with some appropriate tags | 1.5-1.94 |\n")
            f.write("| Fail (0-49%) | Poor semantic structure; inappropriate tag use | 0-1.49 |\n\n")
            
            f.write("### Accessible Navigation and Content (2%)\n\n")
            f.write(f"**Performance Level:** {nav_performance}\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Enhanced accessibility features beyond requirements; excellent user experience for all users regardless of abilities | 1.5-2 |\n")
            f.write("| Credit (65-74%) | Full keyboard accessibility and well-structured content for assistive technologies | 1.3-1.49 |\n")
            f.write("| Pass (50-64%) | Basic keyboard navigation and screen reader support | 1-1.29 |\n")
            f.write("| Fail (0-49%) | Inaccessible navigation or content; significant barriers for users with disabilities | 0-0.99 |\n\n")
            
            f.write("## File-by-File Summary\n\n")
            f.write("| File | Accessibility Score | WCAG 2.1 AA | Semantic Elements | ARIA Attributes | Skip Link | Keyboard Issues |\n")
            f.write("|------|---------------------|-------------|-------------------|----------------|-----------|----------------|\n")
            
            # Sort results by score for the table
            sorted_results = sorted(results, key=lambda r: r.get("basic_score", 0), reverse=True)
            
            for result in sorted_results:
                if "error" in result:
                    f.write(f"| {os.path.relpath(result['file_path'])} | Error | Error | Error | Error | Error | Error |\n")
                    continue
                
                file_path = os.path.relpath(result["file_path"])
                score = result.get("basic_score", 0)
                wcag = self._calculate_file_wcag_score(result)
                semantic = result.get("semantic_tag_count", 0)
                aria = result.get("aria_attribute_count", 0)
                skip = "Yes" if result.get("has_skip_link", False) else "No"
                keyboard = len(result.get("keyboard_navigation", {}).get("issues", []))
                
                f.write(f"| {file_path} | {score:.2f} | {wcag}/5 | {semantic} | {aria} | {skip} | {keyboard} |\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check HTML files for accessibility issues')
    parser.add_argument('folder', help='Folder containing HTML files to check')
    parser.add_argument('--output-dir', '-o', default='accessibility_reports',
                        help='Directory for output reports (default: accessibility_reports)')
    parser.add_argument('--format', '-f', choices=['md', 'csv', 'both'], default='both',
                        help='Output format (md, csv, or both) (default: both)')
    
    args = parser.parse_args()
    
    checker = AccessibilityChecker(args.output_dir)
    
    # Check the folder
    results = checker.check_folder(args.folder)
    
    # Generate reports
    if args.format in ['md', 'both']:
        report_path = os.path.join(args.output_dir, 'accessibility_report.md')
        checker.generate_report(results, report_path)
        print(f"Detailed report saved to {report_path}")
        
        # Generate summary report aligned with rubric
        summary_path = os.path.join(args.output_dir, 'accessibility_summary.md')
        checker.generate_summary_report(results, summary_path)
        print(f"Summary report saved to {summary_path}")
    
    if args.format in ['csv', 'both']:
        csv_path = os.path.join(args.output_dir, 'accessibility_report.csv')
        checker.generate_csv_report(results, csv_path)
        print(f"CSV report saved to {csv_path}")
    
    print("Accessibility analysis complete!")
