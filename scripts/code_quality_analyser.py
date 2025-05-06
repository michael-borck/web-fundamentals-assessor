import os
import argparse
import re
import json
import csv
from pathlib import Path
import subprocess
from datetime import datetime
import glob
from collections import defaultdict
import html.parser
import cssutils
import esprima  # For JavaScript parsing
import prettytable

# Suppress cssutils warning logs
import logging
cssutils.log.setLevel(logging.CRITICAL)


class HTMLParsingHandler(html.parser.HTMLParser):
    """Custom HTML parser to check for code organization and quality metrics."""
    
    def __init__(self):
        super().__init__()
        self.tag_count = 0
        self.void_tags = 0
        self.comments = []
        self.indentation_level = 0
        self.indent_issues = 0
        self.semantic_tags = 0
        self.div_span_count = 0
        self.class_count = 0
        self.id_count = 0
        self.inline_styles = 0
        self.inline_scripts = 0
        self.nested_divs = []
        self.current_nesting = 0
        self.max_nesting = 0
        self.open_tags = []
        self.unique_classes = set()
        self.unique_ids = set()
        self.aria_attrs = 0
        self.lines_processed = 0
        self.heading_order = []
        self.forms_with_labels = 0
        self.forms_without_labels = 0
        
        # Define semantic tags
        self.semantic_tag_list = [
            "article", "aside", "details", "figcaption", "figure",
            "footer", "header", "main", "mark", "nav", "section",
            "summary", "time"
        ]
    
    def handle_starttag(self, tag, attrs):
        self.tag_count += 1
        
        # Track nesting of divs
        if tag == 'div':
            self.current_nesting += 1
            self.div_span_count += 1
        elif tag == 'span':
            self.div_span_count += 1
        
        # Track semantic tags
        if tag in self.semantic_tag_list:
            self.semantic_tags += 1
        
        # Track headings
        if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
            heading_level = int(tag[1])
            self.heading_order.append(heading_level)
        
        # Track form elements
        if tag == 'form':
            has_label = False
            for attr, value in attrs:
                if attr == 'aria-label' or attr == 'aria-labelledby':
                    has_label = True
                    break
            if has_label:
                self.forms_with_labels += 1
            else:
                self.forms_without_labels += 1
        
        # Track attributes
        for attr, value in attrs:
            if attr == 'class':
                self.class_count += 1
                for cls in value.split():
                    self.unique_classes.add(cls)
            elif attr == 'id':
                self.id_count += 1
                self.unique_ids.add(value)
            elif attr == 'style':
                self.inline_styles += 1
            elif attr.startswith('aria-'):
                self.aria_attrs += 1
        
        # Track max nesting level
        if self.current_nesting > self.max_nesting:
            self.max_nesting = self.current_nesting
        
        # Add to open tags
        self.open_tags.append(tag)
    
    def handle_endtag(self, tag):
        if tag == 'div':
            self.current_nesting -= 1
        
        # Remove from open tags
        if self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()
    
    def handle_comment(self, data):
        self.comments.append(data.strip())
    
    def handle_data(self, data):
        # Count lines processed
        self.lines_processed += data.count('\n')
    
    def get_metrics(self):
        """Return collected metrics."""
        # Calculate average comment length
        avg_comment_length = sum(len(c) for c in self.comments) / max(1, len(self.comments))
        
        # Calculate semantic tag ratio
        semantic_ratio = self.semantic_tags / max(1, self.tag_count) * 100
        
        # Calculate div/span ratio
        div_span_ratio = self.div_span_count / max(1, self.tag_count) * 100
        
        # Check heading order issues
        heading_issues = 0
        for i in range(1, len(self.heading_order)):
            if self.heading_order[i] > self.heading_order[i-1] + 1:
                heading_issues += 1
        
        # Calculate form label percentage
        total_forms = self.forms_with_labels + self.forms_without_labels
        form_label_percentage = self.forms_with_labels / max(1, total_forms) * 100
        
        return {
            "total_tags": self.tag_count,
            "semantic_tags": self.semantic_tags,
            "semantic_ratio": semantic_ratio,
            "div_span_count": self.div_span_count,
            "div_span_ratio": div_span_ratio,
            "max_div_nesting": self.max_nesting,
            "comments_count": len(self.comments),
            "avg_comment_length": avg_comment_length,
            "class_count": self.class_count,
            "id_count": self.id_count,
            "unique_classes": len(self.unique_classes),
            "unique_ids": len(self.unique_ids),
            "inline_styles": self.inline_styles,
            "inline_scripts": self.inline_scripts,
            "aria_attributes": self.aria_attrs,
            "heading_order_issues": heading_issues,
            "form_label_percentage": form_label_percentage
        }


class CodeQualityAnalyzer:
    def __init__(self, output_dir="code_quality_reports"):
        """
        Initialize the code quality analyzer.
        
        Args:
            output_dir: Directory to save analysis reports
        """
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Settings for best practices
        self.html_best_practices = {
            "semantic_ratio_min": 15,  # Minimum percentage of semantic tags
            "comment_per_size": 50,    # One comment per X lines
            "max_div_nesting": 5,      # Maximum nesting level of divs
            "inline_styles_max": 5,    # Maximum number of inline styles
            "heading_order": True,     # Proper heading order (no skipping)
            "form_label_min": 90,      # Minimum percentage of forms with labels
        }
        
        self.css_best_practices = {
            "max_selector_specificity": 40, # Maximum selector specificity score
            "max_file_size_kb": 100,       # Maximum CSS file size in KB
            "comment_frequency": 20,       # Comments per X CSS rules
            "max_rule_length": 15,         # Maximum properties per rule
            "important_usage_max": 5,      # Maximum !important declarations
            "vendor_prefix_max": 10,       # Maximum vendor prefixes
        }
        
        self.js_best_practices = {
            "max_function_length": 50,     # Maximum lines per function
            "max_complexity": 15,          # Maximum cyclomatic complexity
            "comment_frequency": 20,       # Comments per X lines
            "max_nesting": 3,              # Maximum nesting level
            "max_params": 4,               # Maximum function parameters
            "console_log_max": 0,          # Maximum console.log statements
        }
        
        # Initialize results storage
        self.html_results = []
        self.css_results = []
        self.js_results = []
    
    def find_files(self, folder_path, extensions):
        """Find all files with given extensions in folder and subfolders."""
        found_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    found_files.append(os.path.join(root, file))
        return found_files
    
    def analyze_html_file(self, file_path):
        """Analyze a single HTML file for code quality."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines
            line_count = content.count('\n') + 1
            
            # Check indentation consistency
            indent_style = None
            indent_issues = 0
            for i, line in enumerate(content.split('\n')):
                if line.strip() == '':
                    continue
                
                # Check leading whitespace
                leading_space = len(line) - len(line.lstrip())
                if leading_space > 0:
                    if indent_style is None:
                        if line[0] == '\t':
                            indent_style = 'tab'
                        else:
                            indent_style = 'space'
                    else:
                        if (indent_style == 'tab' and line[0] != '\t') or \
                           (indent_style == 'space' and line[0] == '\t'):
                            indent_issues += 1
            
            # Parse HTML
            parser = HTMLParsingHandler()
            parser.feed(content)
            metrics = parser.get_metrics()
            
            # Add additional metrics
            metrics.update({
                "file_path": file_path,
                "file_size_kb": os.path.getsize(file_path) / 1024,
                "line_count": line_count,
                "indent_issues": indent_issues,
                "doctype_present": content.lower().startswith("<!doctype")
            })
            
            # Add validation errors - we'll check these later using W3C validator
            metrics["validation_errors"] = None
            
            # Run quality checks
            quality_issues = []
            if metrics["semantic_ratio"] < self.html_best_practices["semantic_ratio_min"]:
                quality_issues.append(f"Low semantic HTML usage ({metrics['semantic_ratio']:.1f}%)")
            
            if metrics["comments_count"] < (line_count / self.html_best_practices["comment_per_size"]):
                quality_issues.append(f"Insufficient comments ({metrics['comments_count']} for {line_count} lines)")
            
            if metrics["max_div_nesting"] > self.html_best_practices["max_div_nesting"]:
                quality_issues.append(f"Excessive div nesting (depth: {metrics['max_div_nesting']})")
            
            if metrics["inline_styles"] > self.html_best_practices["inline_styles_max"]:
                quality_issues.append(f"Excessive inline styles ({metrics['inline_styles']})")
            
            if metrics["heading_order_issues"] > 0:
                quality_issues.append(f"Heading order issues ({metrics['heading_order_issues']})")
            
            if metrics["form_label_percentage"] < self.html_best_practices["form_label_min"]:
                quality_issues.append(f"Forms missing labels ({100-metrics['form_label_percentage']:.1f}%)")
            
            if not metrics["doctype_present"]:
                quality_issues.append("Missing DOCTYPE declaration")
            
            metrics["quality_issues"] = quality_issues
            
            # Calculate quality score
            score = self._calculate_html_quality_score(metrics)
            metrics["quality_score"] = score
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing HTML file {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    def analyze_css_file(self, file_path):
        """Analyze a single CSS file for code quality."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines
            line_count = content.count('\n') + 1
            
            # Parse CSS
            stylesheet = cssutils.parseString(content)
            
            # Initialize metrics
            selector_specificities = []
            rule_lengths = []
            important_count = 0
            vendor_prefix_count = 0
            comments_count = 0
            total_rules = 0
            unique_colors = set()
            media_queries = 0
            
            # Analyze rules
            for rule in stylesheet.cssRules:
                if rule.type == rule.COMMENT:
                    comments_count += 1
                
                elif rule.type == rule.STYLE_RULE:
                    total_rules += 1
                    
                    # Calculate selector specificity
                    selector = rule.selectorText
                    specificity = self._calculate_css_specificity(selector)
                    selector_specificities.append(specificity)
                    
                    # Check rule length
                    rule_length = len(rule.style.getProperties())
                    rule_lengths.append(rule_length)
                    
                    # Check for !important
                    for prop in rule.style:
                        if prop.priority == 'important':
                            important_count += 1
                        
                        # Check for vendor prefixes
                        if prop.name.startswith(('-webkit-', '-moz-', '-ms-', '-o-')):
                            vendor_prefix_count += 1
                        
                        # Track unique colors
                        if prop.value and re.search(r'#[0-9a-fA-F]{3,6}|rgb\(|rgba\(|hsl\(|hsla\(', prop.value):
                            unique_colors.add(prop.value)
                
                elif rule.type == rule.MEDIA_RULE:
                    media_queries += 1
            
            # Calculate metrics
            avg_specificity = sum(selector_specificities) / max(1, len(selector_specificities))
            max_specificity = max(selector_specificities) if selector_specificities else 0
            avg_rule_length = sum(rule_lengths) / max(1, len(rule_lengths))
            max_rule_length = max(rule_lengths) if rule_lengths else 0
            
            metrics = {
                "file_path": file_path,
                "file_size_kb": os.path.getsize(file_path) / 1024,
                "line_count": line_count,
                "total_rules": total_rules,
                "avg_specificity": avg_specificity,
                "max_specificity": max_specificity,
                "avg_rule_length": avg_rule_length,
                "max_rule_length": max_rule_length,
                "important_count": important_count,
                "vendor_prefix_count": vendor_prefix_count,
                "comments_count": comments_count,
                "unique_colors": len(unique_colors),
                "media_queries": media_queries
            }
            
            # Run quality checks
            quality_issues = []
            if max_specificity > self.css_best_practices["max_selector_specificity"]:
                quality_issues.append(f"High selector specificity (max: {max_specificity})")
            
            if metrics["file_size_kb"] > self.css_best_practices["max_file_size_kb"]:
                quality_issues.append(f"File size too large ({metrics['file_size_kb']:.1f} KB)")
            
            if comments_count < (total_rules / self.css_best_practices["comment_frequency"]):
                quality_issues.append(f"Insufficient comments ({comments_count} for {total_rules} rules)")
            
            if max_rule_length > self.css_best_practices["max_rule_length"]:
                quality_issues.append(f"Overly complex CSS rules (max properties: {max_rule_length})")
            
            if important_count > self.css_best_practices["important_usage_max"]:
                quality_issues.append(f"Excessive !important usage ({important_count})")
            
            if vendor_prefix_count > self.css_best_practices["vendor_prefix_max"]:
                quality_issues.append(f"High vendor prefix count ({vendor_prefix_count})")
            
            metrics["quality_issues"] = quality_issues
            
            # Calculate quality score
            score = self._calculate_css_quality_score(metrics)
            metrics["quality_score"] = score
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing CSS file {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    def analyze_js_file(self, file_path):
        """Analyze a single JavaScript file for code quality."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines
            line_count = content.count('\n') + 1
            
            # Parse JavaScript
            try:
                ast = esprima.parseScript(content, {'comment': True, 'loc': True})
                parse_success = True
            except Exception as e:
                parse_success = False
                ast = None
                print(f"Warning: Failed to parse JavaScript in {file_path}: {e}")
            
            # Initialize metrics
            metrics = {
                "file_path": file_path,
                "file_size_kb": os.path.getsize(file_path) / 1024,
                "line_count": line_count,
                "parse_success": parse_success
            }
            
            if not parse_success:
                metrics["quality_score"] = 3  # Low score for unparseable JS
                metrics["quality_issues"] = ["JavaScript parsing failed - syntax errors"]
                return metrics
            
            # Count comments
            comments_count = len(ast.comments)
            
            # Analyze functions, complexity, nesting
            functions = []
            function_lengths = []
            max_params = 0
            max_nesting = 0
            current_nesting = 0
            console_logs = 0
            
            # Need to recursively traverse the AST
            # This is a simplified analysis - a real implementation would
            # need more sophisticated AST traversal
            
            # Simple analysis based on content patterns
            # Function count approximation
            function_matches = re.findall(r'function\s+\w*\s*\([^)]*\)', content)
            functions_count = len(function_matches)
            
            # Arrow functions
            arrow_matches = re.findall(r'=>', content)
            functions_count += len(arrow_matches)
            
            # Max parameters approximation
            param_counts = [len(re.findall(r',', m)) + 1 for m in function_matches]
            max_params = max(param_counts) if param_counts else 0
            
            # Nesting approximation (rough estimate based on braces)
            brace_levels = []
            level = 0
            for char in content:
                if char == '{':
                    level += 1
                    brace_levels.append(level)
                elif char == '}':
                    level = max(0, level - 1)
            
            max_nesting = max(brace_levels) if brace_levels else 0
            
            # Console.log count
            console_logs = len(re.findall(r'console\.log', content))
            
            # Collect metrics
            metrics.update({
                "functions_count": functions_count,
                "max_params": max_params,
                "max_nesting": max_nesting,
                "comments_count": comments_count,
                "console_logs": console_logs
            })
            
            # Run quality checks
            quality_issues = []
            if comments_count < (line_count / self.js_best_practices["comment_frequency"]):
                quality_issues.append(f"Insufficient comments ({comments_count} for {line_count} lines)")
            
            if max_nesting > self.js_best_practices["max_nesting"]:
                quality_issues.append(f"Excessive nesting (depth: {max_nesting})")
            
            if max_params > self.js_best_practices["max_params"]:
                quality_issues.append(f"Functions with too many parameters (max: {max_params})")
            
            if console_logs > self.js_best_practices["console_log_max"]:
                quality_issues.append(f"console.log statements should be removed ({console_logs})")
            
            metrics["quality_issues"] = quality_issues
            
            # Calculate quality score
            score = self._calculate_js_quality_score(metrics)
            metrics["quality_score"] = score
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing JavaScript file {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    def _calculate_css_specificity(self, selector):
        """Calculate CSS selector specificity score."""
        # A simplified calculation
        specificity = 0
        
        # Count IDs
        specificity += selector.count('#') * 100
        
        # Count classes, attributes, and pseudo-classes
        specificity += len(re.findall(r'\.|\\:|\\[', selector)) * 10
        
        # Count element names and pseudo-elements
        specificity += len(re.findall(r'[a-zA-Z0-9]+|::before|::after', selector))
        
        return specificity
    
    def _calculate_html_quality_score(self, metrics):
        """Calculate a quality score (0-10) for HTML file."""
        score = 7  # Start with a baseline score
        
        # Adjust for semantic HTML usage
        semantic_ratio = metrics["semantic_ratio"]
        if semantic_ratio >= 30:
            score += 1
        elif semantic_ratio < 10:
            score -= 1
        
        # Adjust for comments
        comment_ratio = metrics["comments_count"] / (metrics["line_count"] / 50)
        if comment_ratio >= 1:
            score += 1
        elif comment_ratio < 0.5:
            score -= 1
        
        # Adjust for div nesting
        if metrics["max_div_nesting"] <= 3:
            score += 0.5
        elif metrics["max_div_nesting"] > 6:
            score -= 1
        
        # Adjust for inline styles
        if metrics["inline_styles"] == 0:
            score += 0.5
        elif metrics["inline_styles"] > 10:
            score -= 1
        
        # Adjust for heading issues
        if metrics["heading_order_issues"] > 0:
            score -= 0.5
        
        # Adjust for form labels
        if metrics["form_label_percentage"] >= 95:
            score += 0.5
        elif metrics["form_label_percentage"] < 80:
            score -= 0.5
        
        # Adjust for doctype
        if not metrics["doctype_present"]:
            score -= 0.5
        
        # Ensure score is within bounds
        return max(0, min(10, score))
    
    def _calculate_css_quality_score(self, metrics):
        """Calculate a quality score (0-10) for CSS file."""
        score = 7  # Start with a baseline score
        
        # Adjust for selector specificity
        if metrics["max_specificity"] <= 20:
            score += 1
        elif metrics["max_specificity"] > 50:
            score -= 1
        
        # Adjust for comments
        comment_ratio = metrics["comments_count"] / max(1, (metrics["total_rules"] / 20))
        if comment_ratio >= 1:
            score += 1
        elif comment_ratio < 0.5:
            score -= 1
        
        # Adjust for rule length
        if metrics["max_rule_length"] <= 10:
            score += 0.5
        elif metrics["max_rule_length"] > 20:
            score -= 1
        
        # Adjust for !important usage
        if metrics["important_count"] == 0:
            score += 0.5
        elif metrics["important_count"] > 10:
            score -= 1
        
        # Adjust for vendor prefixes
        if metrics["vendor_prefix_count"] <= 5:
            score += 0.5
        elif metrics["vendor_prefix_count"] > 20:
            score -= 1
        
        # Adjust for media queries
        if metrics["media_queries"] >= 3:
            score += 0.5
        
        # Ensure score is within bounds
        return max(0, min(10, score))
    
    def _calculate_js_quality_score(self, metrics):
        """Calculate a quality score (0-10) for JavaScript file."""
        if not metrics["parse_success"]:
            return 3  # Syntax errors are a big problem
        
        score = 7  # Start with a baseline score
        
        # Adjust for comments
        comment_ratio = metrics["comments_count"] / (metrics["line_count"] / 20)
        if comment_ratio >= 1:
            score += 1
        elif comment_ratio < 0.5:
            score -= 1
        
        # Adjust for nesting
        if metrics["max_nesting"] <= 2:
            score += 1
        elif metrics["max_nesting"] > 4:
            score -= 1
        
        # Adjust for function parameters
        if metrics["max_params"] <= 3:
            score += 0.5
        elif metrics["max_params"] > 5:
            score -= 1
        
        # Adjust for console.logs
        if metrics["console_logs"] == 0:
            score += 0.5
        elif metrics["console_logs"] > 3:
            score -= 1
        
        # Ensure score is within bounds
        return max(0, min(10, score))
    
    def analyze_folder(self, folder_path):
        """Analyze all HTML, CSS, and JS files in a folder."""
        # Find files
        html_files = self.find_files(folder_path, ['.html', '.htm'])
        css_files = self.find_files(folder_path, ['.css'])
        js_files = self.find_files(folder_path, ['.js'])
        
        print(f"Found {len(html_files)} HTML files, {len(css_files)} CSS files, {len(js_files)} JS files")
        
        # Analyze HTML files
        for file_path in html_files:
            result = self.analyze_html_file(file_path)
            self.html_results.append(result)
        
        # Analyze CSS files
        for file_path in css_files:
            result = self.analyze_css_file(file_path)
            self.css_results.append(result)
        
        # Analyze JS files
        for file_path in js_files:
            result = self.analyze_js_file(file_path)
            self.js_results.append(result)
        
        # Generate reports
        self.generate_reports()
    
    def generate_reports(self):
        """Generate all reports."""
        # Generate CSV reports
        self._generate_csv_reports()
        
        # Generate summary report
        self._generate_summary_report()
        
        # Generate rubric report
        self._generate_rubric_report()
    
    def _generate_csv_reports(self):
        """Generate CSV reports for all file types."""
        # HTML report
        if self.html_results:
            html_csv_path = os.path.join(self.output_dir, "html_quality.csv")
            with open(html_csv_path, 'w', newline='') as f:
                # Determine fields dynamically from the first result that doesn't have an error
                valid_results = [r for r in self.html_results if 'error' not in r]
                if valid_results:
                    fieldnames = [k for k in valid_results[0].keys() if k != 'quality_issues']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in self.html_results:
                        if 'error' not in result:
                            row = {k: v for k, v in result.items() if k != 'quality_issues'}
                            writer.writerow(row)
            print(f"HTML quality report saved to {html_csv_path}")
        
        # CSS report
        if self.css_results:
            css_csv_path = os.path.join(self.output_dir, "css_quality.csv")
            with open(css_csv_path, 'w', newline='') as f:
                valid_results = [r for r in self.css_results if 'error' not in r]
                if valid_results:
                    fieldnames = [k for k in valid_results[0].keys() if k != 'quality_issues']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in self.css_results:
                        if 'error' not in result:
                            row = {k: v for k, v in result.items() if k != 'quality_issues'}
                            writer.writerow(row)
            print(f"CSS quality report saved to {css_csv_path}")
        
        # JS report
        if self.js_results:
            js_csv_path = os.path.join(self.output_dir, "js_quality.csv")
            with open(js_csv_path, 'w', newline='') as f:
                valid_results = [r for r in self.js_results if 'error' not in r]
                if valid_results:
                    fieldnames = [k for k in valid_results[0].keys() if k != 'quality_issues']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in self.js_results:
                        if 'error' not in result:
                            row = {k: v for k, v in result.items() if k != 'quality_issues'}
                            writer.writerow(row)
            print(f"JS quality report saved to {js_csv_path}")
    
    def _generate_summary_report(self):
        """Generate a summary report in Markdown format."""
        summary_path = os.path.join(self.output_dir, "code_quality_summary.md")
        
        with open(summary_path, 'w') as f:
            f.write("# Code Quality Analysis Summary\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall scores
            html_avg = sum(r.get('quality_score', 0) for r in self.html_results if 'error' not in r) / max(1, len([r for r in self.html_results if 'error' not in r]))
            css_avg = sum(r.get('quality_score', 0) for r in self.css_results if 'error' not in r) / max(1, len([r for r in self.css_results if 'error' not in r]))
            js_avg = sum(r.get('quality_score', 0) for r in self.js_results if 'error' not in r) / max(1, len([r for r in self.js_results if 'error' not in r]))
            
                                                                                       # Calculate a weighted average based on number of files
            html_weight = len(self.html_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            css_weight = len(self.css_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            js_weight = len(self.js_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            
            overall_score = (html_avg * html_weight) + (css_avg * css_weight) + (js_avg * js_weight)
            
            f.write("## Overview\n\n")
            f.write(f"- **HTML Files Analyzed:** {len(self.html_results)}\n")
            f.write(f"- **CSS Files Analyzed:** {len(self.css_results)}\n")
            f.write(f"- **JavaScript Files Analyzed:** {len(self.js_results)}\n\n")
            
            f.write("## Quality Scores\n\n")
            f.write("| File Type | Average Score | Quality Level |\n")
            f.write("|-----------|--------------|---------------|\n")
            f.write(f"| HTML | {html_avg:.2f}/10 | {self._score_to_level(html_avg)} |\n")
            f.write(f"| CSS | {css_avg:.2f}/10 | {self._score_to_level(css_avg)} |\n")
            f.write(f"| JavaScript | {js_avg:.2f}/10 | {self._score_to_level(js_avg)} |\n")
            f.write(f"| **Overall** | **{overall_score:.2f}/10** | **{self._score_to_level(overall_score)}** |\n\n")
            
            # HTML results
            if self.html_results:
                f.write("## HTML Quality Analysis\n\n")
                
                # Common issues
                all_issues = [issue for r in self.html_results if 'quality_issues' in r for issue in r.get('quality_issues', [])]
                issue_counts = {}
                for issue in all_issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
                
                f.write("### Common HTML Issues\n\n")
                if issue_counts:
                    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        f.write(f"- {issue} ({count} occurrences)\n")
                else:
                    f.write("No common issues found.\n")
                
                f.write("\n### HTML Files by Score\n\n")
                f.write("| File | Score | Semantic Ratio | Comments | Issues |\n")
                f.write("|------|-------|---------------|----------|--------|\n")
                
                for result in sorted(self.html_results, key=lambda x: x.get('quality_score', 0), reverse=True):
                    if 'error' in result:
                        continue
                    
                    file_name = os.path.basename(result['file_path'])
                    score = result.get('quality_score', 0)
                    semantic_ratio = result.get('semantic_ratio', 0)
                    comments = result.get('comments_count', 0)
                    issues_count = len(result.get('quality_issues', []))
                    
                    f.write(f"| {file_name} | {score:.2f} | {semantic_ratio:.1f}% | {comments} | {issues_count} |\n")
            
            # CSS results
            if self.css_results:
                f.write("\n## CSS Quality Analysis\n\n")
                
                # Common issues
                all_issues = [issue for r in self.css_results if 'quality_issues' in r for issue in r.get('quality_issues', [])]
                issue_counts = {}
                for issue in all_issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
                
                f.write("### Common CSS Issues\n\n")
                if issue_counts:
                    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        f.write(f"- {issue} ({count} occurrences)\n")
                else:
                    f.write("No common issues found.\n")
                
                f.write("\n### CSS Files by Score\n\n")
                f.write("| File | Score | Rules | Specificity | !important | Issues |\n")
                f.write("|------|-------|-------|------------|------------|--------|\n")
                
                for result in sorted(self.css_results, key=lambda x: x.get('quality_score', 0), reverse=True):
                    if 'error' in result:
                        continue
                    
                    file_name = os.path.basename(result['file_path'])
                    score = result.get('quality_score', 0)
                    rules = result.get('total_rules', 0)
                    specificity = result.get('max_specificity', 0)
                    important = result.get('important_count', 0)
                    issues_count = len(result.get('quality_issues', []))
                    
                    f.write(f"| {file_name} | {score:.2f} | {rules} | {specificity} | {important} | {issues_count} |\n")
            
            # JS results
            if self.js_results:
                f.write("\n## JavaScript Quality Analysis\n\n")
                
                # Common issues
                all_issues = [issue for r in self.js_results if 'quality_issues' in r for issue in r.get('quality_issues', [])]
                issue_counts = {}
                for issue in all_issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
                
                f.write("### Common JavaScript Issues\n\n")
                if issue_counts:
                    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        f.write(f"- {issue} ({count} occurrences)\n")
                else:
                    f.write("No common issues found.\n")
                
                f.write("\n### JavaScript Files by Score\n\n")
                f.write("| File | Score | Lines | Functions | Max Nesting | Issues |\n")
                f.write("|------|-------|-------|-----------|-------------|--------|\n")
                
                for result in sorted(self.js_results, key=lambda x: x.get('quality_score', 0), reverse=True):
                    if 'error' in result:
                        continue
                    
                    file_name = os.path.basename(result['file_path'])
                    score = result.get('quality_score', 0)
                    lines = result.get('line_count', 0)
                    functions = result.get('functions_count', 0)
                    nesting = result.get('max_nesting', 0)
                    issues_count = len(result.get('quality_issues', []))
                    
                    f.write(f"| {file_name} | {score:.2f} | {lines} | {functions} | {nesting} | {issues_count} |\n")
            
            # Recommendations
            f.write("\n## Recommendations\n\n")
            
            # HTML recommendations
            if self.html_results:
                f.write("### HTML Improvements\n\n")
                html_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True) if 'issue_counts' in locals() else []
                if html_issues:
                    for issue, count in html_issues[:3]:
                        if "semantic HTML" in issue:
                            f.write("1. **Use more semantic HTML tags**: Replace generic `<div>` and `<span>` elements with semantic tags like `<article>`, `<section>`, `<nav>`, `<header>`, `<footer>`, etc.\n")
                        elif "comments" in issue:
                            f.write("2. **Add more comments**: Document complex structures and explain the purpose of different sections.\n")
                        elif "nesting" in issue:
                            f.write("3. **Reduce div nesting**: Simplify your HTML structure by flattening deeply nested divs.\n")
                        elif "inline styles" in issue:
                            f.write("4. **Remove inline styles**: Move styles to external CSS files for better maintainability.\n")
                        elif "heading" in issue:
                            f.write("5. **Fix heading structure**: Ensure headings follow a proper hierarchical structure (h1 → h2 → h3...).\n")
                        elif "label" in issue:
                            f.write("6. **Add labels to all form elements**: Improve accessibility by properly labeling all form controls.\n")
                else:
                    f.write("Your HTML code quality is good. Continue following best practices.\n")
            
            # CSS recommendations
            if self.css_results:
                f.write("\n### CSS Improvements\n\n")
                css_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True) if 'issue_counts' in locals() else []
                if css_issues:
                    for issue, count in css_issues[:3]:
                        if "specificity" in issue:
                            f.write("1. **Reduce selector specificity**: Use simpler selectors and avoid deep nesting.\n")
                        elif "file size" in issue:
                            f.write("2. **Optimize CSS file size**: Split large files into modules and remove unused styles.\n")
                        elif "comments" in issue:
                            f.write("3. **Add more comments**: Document complex selectors and explain the purpose of different style blocks.\n")
                        elif "complex" in issue:
                            f.write("4. **Simplify CSS rules**: Break down large rule blocks into smaller, more focused rules.\n")
                        elif "!important" in issue:
                            f.write("5. **Avoid !important**: Refactor your CSS to avoid relying on !important declarations.\n")
                        elif "vendor prefix" in issue:
                            f.write("6. **Use a preprocessor or autoprefixer**: Automate vendor prefix handling rather than manual management.\n")
                else:
                    f.write("Your CSS code quality is good. Continue following best practices.\n")
            
            # JS recommendations
            if self.js_results:
                f.write("\n### JavaScript Improvements\n\n")
                js_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True) if 'issue_counts' in locals() else []
                if js_issues:
                    for issue, count in js_issues[:3]:
                        if "comments" in issue:
                            f.write("1. **Add more comments**: Document complex logic and explain the purpose of functions.\n")
                        elif "nesting" in issue:
                            f.write("2. **Reduce nesting**: Simplify control flow by extracting functions and using early returns.\n")
                        elif "parameters" in issue:
                            f.write("3. **Reduce function parameters**: Use objects to pass multiple related parameters.\n")
                        elif "console.log" in issue:
                            f.write("4. **Remove console.log statements**: These should not be present in production code.\n")
                else:
                    f.write("Your JavaScript code quality is good. Continue following best practices.\n")
            
            print(f"Summary report saved to {summary_path}")
    
    def _generate_rubric_report(self):
        """Generate a report specifically for rubric assessment."""
        rubric_path = os.path.join(self.output_dir, "code_quality_rubric.md")
        
        with open(rubric_path, 'w') as f:
            f.write("# Code Quality Assessment for Rubric\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Calculate overall score
            html_avg = sum(r.get('quality_score', 0) for r in self.html_results if 'error' not in r) / max(1, len([r for r in self.html_results if 'error' not in r]))
            css_avg = sum(r.get('quality_score', 0) for r in self.css_results if 'error' not in r) / max(1, len([r for r in self.css_results if 'error' not in r]))
            js_avg = sum(r.get('quality_score', 0) for r in self.js_results if 'error' not in r) / max(1, len([r for r in self.js_results if 'error' not in r]))
            
            # Weight based on number of files
            html_weight = len(self.html_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            css_weight = len(self.css_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            js_weight = len(self.js_results) / max(1, len(self.html_results) + len(self.css_results) + len(self.js_results))
            
            overall_score = (html_avg * html_weight) + (css_avg * css_weight) + (js_avg * js_weight)
            
            # Map to rubric scale
            rubric_performance, rubric_points, rubric_percentage = self._map_to_rubric_scale(overall_score)
            
            f.write("## Code Organisation and Documentation (5%)\n\n")
            f.write(f"**Overall Code Quality Score:** {overall_score:.2f}/10\n\n")
            f.write(f"**Performance Level:** {rubric_performance}\n\n")
            f.write(f"**Assessment:** {rubric_points}/5 points ({rubric_percentage:.1f}%)\n\n")
            
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Expertly structured code with comprehensive, professional documentation | 3.75-5 |\n")
            f.write("| Credit (65-74%) | Well-organised code with good documentation | 3.25-3.74 |\n")
            f.write("| Pass (50-64%) | Basic organisation and minimal comments | 2.5-3.24 |\n")
            f.write("| Fail (0-49%) | Poorly organised code with inadequate documentation | 0-2.49 |\n\n")
            
            # Analysis breakdown
            f.write("## Analysis Breakdown\n\n")
            
            # Comments analysis
            html_comments = sum(r.get('comments_count', 0) for r in self.html_results if 'error' not in r)
            html_lines = sum(r.get('line_count', 0) for r in self.html_results if 'error' not in r)
            css_comments = sum(r.get('comments_count', 0) for r in self.css_results if 'error' not in r)
            css_rules = sum(r.get('total_rules', 0) for r in self.css_results if 'error' not in r)
            js_comments = sum(r.get('comments_count', 0) for r in self.js_results if 'error' not in r)
            js_lines = sum(r.get('line_count', 0) for r in self.js_results if 'error' not in r)
            
            f.write("### Documentation\n\n")
            f.write(f"- HTML: {html_comments} comments for {html_lines} lines ({html_comments/max(1, html_lines)*100:.1f} comments per 100 lines)\n")
            f.write(f"- CSS: {css_comments} comments for {css_rules} rules ({css_comments/max(1, css_rules)*100:.1f} comments per 100 rules)\n")
            f.write(f"- JavaScript: {js_comments} comments for {js_lines} lines ({js_comments/max(1, js_lines)*100:.1f} comments per 100 lines)\n\n")
            
            # Code organization metrics
            html_semantic = sum(r.get('semantic_ratio', 0) for r in self.html_results if 'error' not in r) / max(1, len([r for r in self.html_results if 'error' not in r]))
            css_specificity = sum(r.get('max_specificity', 0) for r in self.css_results if 'error' not in r) / max(1, len([r for r in self.css_results if 'error' not in r]))
            js_nesting = sum(r.get('max_nesting', 0) for r in self.js_results if 'error' not in r) / max(1, len([r for r in self.js_results if 'error' not in r]))
            
            f.write("### Code Organization\n\n")
            f.write(f"- HTML: {html_semantic:.1f}% semantic tags usage (target: >20%)\n")
            f.write(f"- CSS: Average max specificity of {css_specificity:.1f} (target: <30)\n")
            f.write(f"- JavaScript: Average max nesting level of {js_nesting:.1f} (target: <4)\n\n")
            
            # Best practices
            html_inline_styles = sum(r.get('inline_styles', 0) for r in self.html_results if 'error' not in r)
            css_important = sum(r.get('important_count', 0) for r in self.css_results if 'error' not in r)
            js_console_logs = sum(r.get('console_logs', 0) for r in self.js_results if 'error' not in r)
            
            f.write("### Best Practices\n\n")
            f.write(f"- HTML: {html_inline_styles} inline styles detected (target: 0)\n")
            f.write(f"- CSS: {css_important} !important declarations (target: <5)\n")
            f.write(f"- JavaScript: {js_console_logs} console.log statements (target: 0)\n\n")
            
            # Strengths and weaknesses
            f.write("## Strengths and Improvement Areas\n\n")
            
            f.write("### Strengths\n\n")
            strengths = []
            
            if html_semantic > 20:
                strengths.append("Good use of semantic HTML elements")
            if html_comments/max(1, html_lines)*100 > 5:
                strengths.append("Well-commented HTML code")
            if css_comments/max(1, css_rules)*100 > 10:
                strengths.append("Well-commented CSS code")
            if js_comments/max(1, js_lines)*100 > 5:
                strengths.append("Well-commented JavaScript code")
            if css_specificity < 30:
                strengths.append("Good CSS selector specificity")
            if js_nesting < 4:
                strengths.append("Good JavaScript code structure with moderate nesting")
            if html_inline_styles == 0:
                strengths.append("No inline styles found, good separation of concerns")
            if css_important < 5:
                strengths.append("Limited use of !important declarations")
            if js_console_logs == 0:
                strengths.append("No console.log statements in production code")
            
            if strengths:
                for strength in strengths[:5]:  # Show top 5 strengths
                    f.write(f"- {strength}\n")
            else:
                f.write("- No significant strengths identified\n")
            
            f.write("\n### Areas for Improvement\n\n")
            improvements = []
            
            if html_semantic < 20:
                improvements.append("Increase the use of semantic HTML elements")
            if html_comments/max(1, html_lines)*100 < 5:
                improvements.append("Add more comments to HTML code")
            if css_comments/max(1, css_rules)*100 < 10:
                improvements.append("Add more comments to CSS code")
            if js_comments/max(1, js_lines)*100 < 5:
                improvements.append("Add more comments to JavaScript code")
            if css_specificity > 30:
                improvements.append("Reduce CSS selector specificity")
            if js_nesting > 4:
                improvements.append("Reduce JavaScript nesting levels")
            if html_inline_styles > 0:
                improvements.append("Remove inline styles and move to external CSS")
            if css_important > 5:
                improvements.append("Reduce use of !important declarations")
            if js_console_logs > 0:
                improvements.append("Remove console.log statements from production code")
            
            if improvements:
                for improvement in improvements[:5]:  # Show top 5 improvements
                    f.write(f"- {improvement}\n")
            else:
                f.write("- No significant areas for improvement identified\n")
            
            print(f"Rubric assessment report saved to {rubric_path}")
    
    def _score_to_level(self, score):
        """Convert a score to a quality level."""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7:
            return "Good"
        elif score >= 5:
            return "Satisfactory"
        else:
            return "Needs Improvement"
    
    def _map_to_rubric_scale(self, score):
        """
        Map a score (0-10) to the rubric scale.
        
        Returns:
            Tuple of (performance_level, points, percentage)
        """
        if score >= 8.5:
            performance = "Distinction (75-100%)"
            percentage = min(100, 75 + (score - 8.5) * 25 / 1.5)
            points = 5 * percentage / 100
        elif score >= 7:
            performance = "Credit (65-74%)"
            percentage = 65 + (score - 7) * 9 / 1.5
            points = 5 * percentage / 100
        elif score >= 5:
            performance = "Pass (50-64%)"
            percentage = 50 + (score - 5) * 14 / 2
            points = 5 * percentage / 100
        else:
            performance = "Fail (0-49%)"
            percentage = score * 49 / 5
            points = 5 * percentage / 100
        
        return (performance, round(points, 2), percentage)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze code quality of HTML, CSS, and JS files')
    parser.add_argument('folder', help='Path to the folder containing code files')
    parser.add_argument('--output', '-o', default='code_quality_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    analyzer = CodeQualityAnalyzer(args.output)
    analyzer.analyze_folder(args.folder)
    
    print("Code quality analysis complete!")
