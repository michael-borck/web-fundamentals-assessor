import os
import argparse
import json
import subprocess
import glob
import csv
import re
from pathlib import Path
from datetime import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor

class PerformanceTester:
    def __init__(self, output_dir="performance_reports"):
        """
        Initialize the performance tester.
        
        Args:
            output_dir: Directory to save performance reports
        """
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Check for Lighthouse CLI
        try:
            subprocess.run(["lighthouse", "--version"], capture_output=True, text=True, check=True)
            self.lighthouse_installed = True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.lighthouse_installed = False
            print("Warning: Lighthouse CLI not found. Will attempt to use npx.")
        
        # Output subdirectories
        self.html_dir = os.path.join(output_dir, "html")
        self.json_dir = os.path.join(output_dir, "json")
        self.csv_dir = os.path.join(output_dir, "csv")
        
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
    
    def check_dependencies(self):
        """
        Check if all dependencies are installed.
        
        Returns:
            Boolean indicating if dependencies are met
        """
        # Check for Node.js
        try:
            node_version = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
            print(f"Node.js version: {node_version.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Node.js is not installed. Please install Node.js to use this script.")
            return False
        
        # Check for Chrome/Chromium
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
        
        chrome_found = False
        chrome_path = None
        
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                chrome_path = path
                break
        
        if chrome_found:
            print(f"Chrome/Chromium found at: {chrome_path}")
        else:
            print("Error: Chrome or Chromium is not found. Please install Chrome or Chromium to use this script.")
            return False
        
        # If Lighthouse is not installed, check if we can use npx
        if not self.lighthouse_installed:
            try:
                subprocess.run(["npx", "--version"], capture_output=True, text=True, check=True)
                print("Using npx to run Lighthouse")
            except (subprocess.SubprocessError, FileNotFoundError):
                print("Error: Neither Lighthouse CLI nor npx is available.")
                print("Please install Lighthouse CLI globally: npm install -g lighthouse")
                return False
        
        return True
    
    def get_html_files(self, folder_path):
        """
        Find all HTML files in a folder and its subfolders.
        
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
    
    def create_temp_server_config(self, folder_path):
        """
        Create a temporary server configuration file for running Lighthouse CI.
        
        Args:
            folder_path: Path to the folder containing static files
            
        Returns:
            Path to the configuration file
        """
        config_path = os.path.join(self.output_dir, "lighthouserc.js")
        
        config_content = f"""
module.exports = {{
  ci: {{
    collect: {{
      staticDistDir: '{folder_path.replace('\\', '\\\\')}',
      settings: {{
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
        skipAudits: ['uses-http2'],
      }},
    }},
    upload: {{
      target: 'filesystem',
      outputDir: '{self.output_dir.replace('\\', '\\\\')}',
    }},
    assert: {{
      assertions: {{
        'categories:performance': ['warn', {{'minScore': 0.5}}],
        'categories:accessibility': ['warn', {{'minScore': 0.7}}],
        'categories:best-practices': ['warn', {{'minScore': 0.8}}],
        'categories:seo': ['warn', {{'minScore': 0.8}}],
      }},
    }},
  }},
}};
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return config_path
    
    def run_lighthouse_cli(self, html_file, chrome_path=None):
        """
        Run Lighthouse CLI on a single HTML file.
        
        Args:
            html_file: Path to the HTML file to test
            chrome_path: Path to Chrome/Chromium executable (optional)
            
        Returns:
            Tuple of (success, report_paths)
        """
        # Convert the HTML file to a file:// URL
        file_url = f"file://{os.path.abspath(html_file)}"
        
        # Generate output file names
        file_base = os.path.splitext(os.path.basename(html_file))[0]
        html_output = os.path.join(self.html_dir, f"{file_base}.html")
        json_output = os.path.join(self.json_dir, f"{file_base}.json")
        
        # Prepare the command
        lighthouse_cmd = []
        
        if self.lighthouse_installed:
            lighthouse_cmd = ["lighthouse"]
        else:
            lighthouse_cmd = ["npx", "lighthouse"]
        
        lighthouse_cmd.extend([
            file_url,
            "--output=html,json",
            f"--output-path={html_output}",
            "--chrome-flags=--headless",
            "--only-categories=performance,accessibility,best-practices,seo",
            "--quiet"
        ])
        
        if chrome_path:
            lighthouse_cmd.append(f"--chrome-path={chrome_path}")
        
        try:
            print(f"Testing {html_file}...")
            process = subprocess.run(lighthouse_cmd, capture_output=True, text=True, check=True)
            
            # JSON file has .report.json extension, we need to rename it
            temp_json = f"{html_output}.report.json"
            if os.path.exists(temp_json):
                shutil.move(temp_json, json_output)
            
            return True, (html_output, json_output)
        
        except subprocess.SubprocessError as e:
            print(f"Error running Lighthouse on {html_file}: {e}")
            print(f"Stderr: {e.stderr}")
            return False, None
    
    def run_lighthouse_ci(self, folder_path):
        """
        Run Lighthouse CI on a folder of static HTML files.
        
        Args:
            folder_path: Path to the folder containing static files
            
        Returns:
            Boolean indicating success
        """
        # Create temporary configuration file
        config_path = self.create_temp_server_config(folder_path)
        
        # Prepare the command
        lhci_cmd = ["npx", "@lhci/cli@latest", "autorun", "--config", config_path]
        
        try:
            print(f"Running Lighthouse CI on {folder_path}...")
            process = subprocess.run(lhci_cmd, capture_output=True, text=True, check=True)
            return True
        
        except subprocess.SubprocessError as e:
            print(f"Error running Lighthouse CI: {e}")
            print(f"Stderr: {e.stderr}")
            return False
    
    def parse_json_report(self, json_path):
        """
        Parse a Lighthouse JSON report to extract key metrics.
        
        Args:
            json_path: Path to the JSON report file
            
        Returns:
            Dictionary of metrics
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Extract scores
            categories = data.get('categories', {})
            scores = {
                'performance': categories.get('performance', {}).get('score', 0) * 100,
                'accessibility': categories.get('accessibility', {}).get('score', 0) * 100,
                'best_practices': categories.get('best-practices', {}).get('score', 0) * 100,
                'seo': categories.get('seo', {}).get('score', 0) * 100,
            }
            
            # Extract key metrics
            metrics = {}
            
            # Core Web Vitals
            audits = data.get('audits', {})
            metrics['fcp'] = audits.get('first-contentful-paint', {}).get('numericValue', 0) / 1000
            metrics['lcp'] = audits.get('largest-contentful-paint', {}).get('numericValue', 0) / 1000
            metrics['cls'] = audits.get('cumulative-layout-shift', {}).get('numericValue', 0)
            metrics['tbt'] = audits.get('total-blocking-time', {}).get('numericValue', 0)
            metrics['tti'] = audits.get('interactive', {}).get('numericValue', 0) / 1000
            
            # Resource metrics
            metrics['total_bytes'] = audits.get('total-byte-weight', {}).get('numericValue', 0) / 1024 / 1024  # Convert to MB
            metrics['image_bytes'] = 0
            metrics['script_bytes'] = 0
            metrics['css_bytes'] = 0
            metrics['font_bytes'] = 0
            metrics['document_bytes'] = 0
            metrics['third_party_bytes'] = 0
            
            # Extract resource sizes by type
            resource_summary = audits.get('resource-summary', {}).get('details', {}).get('items', [])
            for item in resource_summary:
                resource_type = item.get('resourceType', '')
                transfer_size = item.get('transferSize', 0) / 1024 / 1024  # Convert to MB
                
                if resource_type == 'image':
                    metrics['image_bytes'] = transfer_size
                elif resource_type == 'script':
                    metrics['script_bytes'] = transfer_size
                elif resource_type == 'stylesheet':
                    metrics['css_bytes'] = transfer_size
                elif resource_type == 'font':
                    metrics['font_bytes'] = transfer_size
                elif resource_type == 'document':
                    metrics['document_bytes'] = transfer_size
                
            third_party = audits.get('third-party-summary', {}).get('details', {}).get('items', [])
            for item in third_party:
                metrics['third_party_bytes'] += item.get('transferSize', 0) / 1024 / 1024  # Convert to MB
            
            return {
                'scores': scores,
                'metrics': metrics
            }
        
        except Exception as e:
            print(f"Error parsing JSON report {json_path}: {e}")
            return None
    
    def create_summary_csv(self, json_reports, output_path):
        """
        Create a CSV summary of all performance metrics.
        
        Args:
            json_reports: List of paths to JSON report files
            output_path: Path to save the CSV file
        """
        csv_data = []
        
        for json_path in json_reports:
            data = self.parse_json_report(json_path)
            if not data:
                continue
            
            file_name = os.path.basename(json_path).replace('.json', '')
            
            row = {
                'file': file_name,
                'performance_score': data['scores']['performance'],
                'accessibility_score': data['scores']['accessibility'],
                'best_practices_score': data['scores']['best_practices'],
                'seo_score': data['scores']['seo'],
                'first_contentful_paint': data['metrics']['fcp'],
                'largest_contentful_paint': data['metrics']['lcp'],
                'cumulative_layout_shift': data['metrics']['cls'],
                'total_blocking_time': data['metrics']['tbt'],
                'time_to_interactive': data['metrics']['tti'],
                'total_size_mb': data['metrics']['total_bytes'],
                'image_size_mb': data['metrics']['image_bytes'],
                'script_size_mb': data['metrics']['script_bytes'],
                'css_size_mb': data['metrics']['css_bytes'],
                'font_size_mb': data['metrics']['font_bytes'],
                'document_size_mb': data['metrics']['document_bytes'],
                'third_party_size_mb': data['metrics']['third_party_bytes'],
            }
            
            csv_data.append(row)
        
        # Write to CSV
        if csv_data:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"Summary CSV saved to {output_path}")
        else:
            print("No data to write to CSV")
    
    def generate_markdown_report(self, folder_path, csv_path, output_path):
        """
        Generate a Markdown report with analysis and recommendations.
        
        Args:
            folder_path: Path to the folder containing static files
            csv_path: Path to the CSV summary file
            output_path: Path to save the Markdown report
        """
        try:
            # Load CSV data
            csv_data = []
            with open(csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to numeric
                    numeric_row = {}
                    for key, value in row.items():
                        if key == 'file':
                            numeric_row[key] = value
                        else:
                            try:
                                numeric_row[key] = float(value)
                            except ValueError:
                                numeric_row[key] = 0
                    
                    csv_data.append(numeric_row)
            
            # Calculate averages
            avg_scores = {
                'performance': sum(row['performance_score'] for row in csv_data) / len(csv_data),
                'accessibility': sum(row['accessibility_score'] for row in csv_data) / len(csv_data),
                'best_practices': sum(row['best_practices_score'] for row in csv_data) / len(csv_data),
                'seo': sum(row['seo_score'] for row in csv_data) / len(csv_data),
            }
            
            avg_metrics = {
                'fcp': sum(row['first_contentful_paint'] for row in csv_data) / len(csv_data),
                'lcp': sum(row['largest_contentful_paint'] for row in csv_data) / len(csv_data),
                'cls': sum(row['cumulative_layout_shift'] for row in csv_data) / len(csv_data),
                'tbt': sum(row['total_blocking_time'] for row in csv_data) / len(csv_data),
                'tti': sum(row['time_to_interactive'] for row in csv_data) / len(csv_data),
                'total_bytes': sum(row['total_size_mb'] for row in csv_data) / len(csv_data),
                'image_bytes': sum(row['image_size_mb'] for row in csv_data) / len(csv_data),
                'script_bytes': sum(row['script_size_mb'] for row in csv_data) / len(csv_data),
                'css_bytes': sum(row['css_size_mb'] for row in csv_data) / len(csv_data),
            }
            
            # Sort data to find worst performers
            worst_performance = sorted(csv_data, key=lambda x: x['performance_score'])[:3]
            worst_accessibility = sorted(csv_data, key=lambda x: x['accessibility_score'])[:3]
            largest_pages = sorted(csv_data, key=lambda x: x['total_size_mb'], reverse=True)[:3]
            
            # Map scores to rubric levels
            def get_performance_level(score):
                if score >= 90:
                    return "Distinction (75-100%)"
                elif score >= 80:
                    return "Credit (65-74%)"
                elif score >= 70:
                    return "Pass (50-64%)"
                else:
                    return "Fail (0-49%)"
            
            perf_level = get_performance_level(avg_scores['performance'])
            
            # Generate recommendations based on metrics
            recommendations = []
            
            if avg_metrics['image_bytes'] > 0.5:  # More than 0.5 MB average image size
                recommendations.append("Optimize images by using formats like WebP, compressing, and properly sizing images for their display size")
            
            if avg_metrics['lcp'] > 2.5:  # LCP > 2.5s
                recommendations.append("Improve Largest Contentful Paint (LCP) by optimizing server response times, reducing render-blocking resources, and optimizing critical resources")
            
            if avg_metrics['cls'] > 0.1:  # CLS > 0.1
                recommendations.append("Improve Cumulative Layout Shift (CLS) by setting size attributes on images and videos, avoiding inserting content above existing content, and using transform animations instead of animations that trigger layout changes")
            
            if avg_metrics['tbt'] > 300:  # TBT > 300ms
                recommendations.append("Reduce Total Blocking Time (TBT) by minimizing main thread work, reducing JavaScript execution time, and breaking up long tasks")
            
            # Write Markdown report
            with open(output_path, 'w') as f:
                f.write("# Website Performance Analysis Report\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Summary\n\n")
                f.write(f"- Analyzed {len(csv_data)} HTML pages in {folder_path}\n")
                f.write(f"- Overall site performance: {avg_scores['performance']:.1f}/100\n")
                f.write(f"- Accessibility score: {avg_scores['accessibility']:.1f}/100\n")
                f.write(f"- Best practices score: {avg_scores['best_practices']:.1f}/100\n")
                f.write(f"- SEO score: {avg_scores['seo']:.1f}/100\n\n")
                
                # Rubric Assessment
                f.write("## Rubric Assessment\n\n")
                f.write("### Site Interactivity and Performance (10%)\n\n")
                f.write(f"**Performance Level:** {perf_level}\n\n")
                
                f.write("| Performance Level | Description | Points |\n")
                f.write("|-------------------|-------------|--------|\n")
                f.write("| Distinction (75-100%) | Excellent interactivity with intuitive UX; optimised performance across all devices and connection speeds | 7.5-10 |\n")
                f.write("| Credit (65-74%) | Good interactivity with smooth transitions; site loads quickly on most devices | 6.5-7.49 |\n")
                f.write("| Pass (50-64%) | Basic interactivity implemented; site loads and functions adequately | 5-6.49 |\n")
                f.write("| Fail (0-49%) | Poor interactivity; site experiences performance issues or loading problems | 0-4.99 |\n\n")
                
                # Calculate points based on performance score
                if avg_scores['performance'] >= 90:
                    points = min(10, 7.5 + (avg_scores['performance'] - 90) * 0.25)
                    percentage = min(100, 75 + (avg_scores['performance'] - 90) * 0.25 * 10)
                elif avg_scores['performance'] >= 80:
                    points = 6.5 + (avg_scores['performance'] - 80) * 0.1
                    percentage = 65 + (avg_scores['performance'] - 80) * 0.1 * 10
                elif avg_scores['performance'] >= 70:
                    points = 5 + (avg_scores['performance'] - 70) * 0.15
                    percentage = 50 + (avg_scores['performance'] - 70) * 0.15 * 10
                else:
                    points = avg_scores['performance'] * 0.07
                    percentage = avg_scores['performance'] * 0.7
                
                f.write(f"**Points:** {points:.2f}/10 ({percentage:.1f}%)\n\n")
                
                # Core Web Vitals
                f.write("## Core Web Vitals\n\n")
                f.write("| Metric | Average Value | Target | Status |\n")
                f.write("|--------|--------------|--------|--------|\n")
                
                # FCP status
                fcp_status = "✅ Good" if avg_metrics['fcp'] < 1.8 else "⚠️ Needs Improvement" if avg_metrics['fcp'] < 3 else "❌ Poor"
                f.write(f"| First Contentful Paint (FCP) | {avg_metrics['fcp']:.2f}s | < 1.8s | {fcp_status} |\n")
                
                # LCP status
                lcp_status = "✅ Good" if avg_metrics['lcp'] < 2.5 else "⚠️ Needs Improvement" if avg_metrics['lcp'] < 4 else "❌ Poor"
                f.write(f"| Largest Contentful Paint (LCP) | {avg_metrics['lcp']:.2f}s | < 2.5s | {lcp_status} |\n")
                
                # CLS status
                cls_status = "✅ Good" if avg_metrics['cls'] < 0.1 else "⚠️ Needs Improvement" if avg_metrics['cls'] < 0.25 else "❌ Poor"
                f.write(f"| Cumulative Layout Shift (CLS) | {avg_metrics['cls']:.3f} | < 0.1 | {cls_status} |\n")
                
                # TBT status
                tbt_status = "✅ Good" if avg_metrics['tbt'] < 200 else "⚠️ Needs Improvement" if avg_metrics['tbt'] < 600 else "❌ Poor"
                f.write(f"| Total Blocking Time (TBT) | {avg_metrics['tbt']:.0f}ms | < 200ms | {tbt_status} |\n")
                
                # TTI status
                tti_status = "✅ Good" if avg_metrics['tti'] < 3.8 else "⚠️ Needs Improvement" if avg_metrics['tti'] < 7.3 else "❌ Poor"
                f.write(f"| Time to Interactive (TTI) | {avg_metrics['tti']:.2f}s | < 3.8s | {tti_status} |\n\n")
                
                # Resource Usage
                f.write("## Resource Usage\n\n")
                f.write("| Resource Type | Average Size (MB) |\n")
                f.write("|---------------|-------------------|\n")
                f.write(f"| Total Size | {avg_metrics['total_bytes']:.2f} |\n")
                f.write(f"| Images | {avg_metrics['image_bytes']:.2f} |\n")
                f.write(f"| JavaScript | {avg_metrics['script_bytes']:.2f} |\n")
                f.write(f"| CSS | {avg_metrics['css_bytes']:.2f} |\n\n")
                
                # Largest Pages
                f.write("## Largest Pages\n\n")
                f.write("| File | Total Size (MB) | Performance Score |\n")
                f.write("|------|-----------------|-------------------|\n")
                
                for page in largest_pages:
                    f.write(f"| {page['file']} | {page['total_size_mb']:.2f} | {page['performance_score']:.1f} |\n")
                
                f.write("\n")
                
                # Worst Performing Pages
                f.write("## Pages with Lowest Performance Scores\n\n")
                f.write("| File | Performance Score | LCP (s) | TBT (ms) |\n")
                f.write("|------|-------------------|---------|----------|\n")
                
                for page in worst_performance:
                    f.write(f"| {page['file']} | {page['performance_score']:.1f} | {page['largest_contentful_paint']:.2f} | {page['total_blocking_time']:.0f} |\n")
                
                f.write("\n")
                
                # Recommendations
                f.write("## Recommendations\n\n")
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        f.write(f"{i}. {rec}\n")
                else:
                    f.write("The site is performing well. Continue monitoring and maintaining good performance practices.\n")
                
                f.write("\n")
                
                # Links to individual reports
                f.write("## Individual Page Reports\n\n")
                
                # Find HTML reports
                html_reports = glob.glob(os.path.join(self.html_dir, "*.html"))
                
                for report in sorted(html_reports):
                    file_name = os.path.basename(report)
                    page_name = file_name.replace('.html', '')
                    
                    # Find matching JSON data
                    matching_data = next((x for x in csv_data if x['file'] == page_name), None)
                    
                    if matching_data:
                        rel_path = os.path.relpath(report, os.path.dirname(output_path))
                        f.write(f"- [{page_name}]({rel_path}) - Performance: {matching_data['performance_score']:.1f}, LCP: {matching_data['largest_contentful_paint']:.2f}s\n")
                
                print(f"Markdown report saved to {output_path}")
        
        except Exception as e:
            print(f"Error generating Markdown report: {e}")
    
    def test_html_files(self, folder_path, chrome_path=None, parallel=1):
        """
        Test all HTML files in a folder using Lighthouse CLI.
        
        Args:
            folder_path: Path to the folder containing HTML files
            chrome_path: Path to Chrome/Chromium executable (optional)
            parallel: Number of parallel tests to run
            
        Returns:
            List of JSON report paths
        """
        html_files = self.get_html_files(folder_path)
        print(f"Found {len(html_files)} HTML files to test")
        
        json_reports = []
        
        if parallel > 1:
            # Run tests in parallel
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = []
                for html_file in html_files:
                    futures.append(executor.submit(self.run_lighthouse_cli, html_file, chrome_path))
                
                for future in futures:
                    success, paths = future.result()
                    if success and paths:
                        _, json_path = paths
                        json_reports.append(json_path)
        else:
            # Run tests sequentially
            for html_file in html_files:
                success, paths = self.run_lighthouse_cli(html_file, chrome_path)
                if success and paths:
                    _, json_path = paths
                    json_reports.append(json_path)
        
        return json_reports
    
    def run_performance_tests(self, folder_path, chrome_path=None, parallel=1, use_ci=False):
        """
        Run performance tests on all HTML files in a folder.
        
        Args:
            folder_path: Path to the folder containing HTML files
            chrome_path: Path to Chrome/Chromium executable (optional)
            parallel: Number of parallel tests to run
            use_ci: Whether to use Lighthouse CI
            
        Returns:
            Boolean indicating success
        """
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Run tests
        if use_ci:
            success = self.run_lighthouse_ci(folder_path)
            if not success:
                return False
            
            # Find JSON reports
            json_reports = glob.glob(os.path.join(self.output_dir, "*.json"))
        else:
            json_reports = self.test_html_files(folder_path, chrome_path, parallel)
        
        if not json_reports:
            print("No reports were generated")
            return False
        
        # Create summary CSV
        csv_path = os.path.join(self.csv_dir, "performance_summary.csv")
        self.create_summary_csv(json_reports, csv_path)
        
        # Generate markdown report
        md_path = os.path.join(self.output_dir, "performance_report.md")
        self.generate_markdown_report(folder_path, csv_path, md_path)
        
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test performance of static HTML files')
    parser.add_argument('folder', help='Path to folder containing HTML files')
    parser.add_argument('--output', '-o', default='performance_reports', help='Output directory for reports')
    parser.add_argument('--chrome-path', help='Path to Chrome/Chromium executable')
    parser.add_argument('--parallel', '-p', type=int, default=1, help='Number of parallel tests to run')
    parser.add_argument('--use-ci', action='store_true', help='Use Lighthouse CI instead of CLI')
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.output)
    success = tester.run_performance_tests(args.folder, args.chrome_path, args.parallel, args.use_ci)
    
    if success:
        print("Performance testing completed successfully")
        print(f"Reports saved to {args.output}")
    else:
        print("Performance testing failed")
        sys.exit(1)

