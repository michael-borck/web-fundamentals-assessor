import os
import sys
import argparse
import json
import subprocess
import glob
import csv
import re
from pathlib import Path
from datetime import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse # Import urllib.parse

class PerformanceTester:
    def __init__(self, output_dir="performance_reports"):
        """
        Initialize the performance tester.

        Args:
            output_dir: Directory to save performance reports
        """
        self.output_dir = output_dir

        # Create output directory and subdirectories
        os.makedirs(output_dir, exist_ok=True)

        # Check for Lighthouse CLI
        try:
            # Use subprocess.run for better error handling and consistency
            result = subprocess.run(["lighthouse", "--version"], capture_output=True, text=True, check=True)
            self.lighthouse_installed = True
            print(f"Lighthouse CLI found. Version: {result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            self.lighthouse_installed = False
            print("Warning: Lighthouse CLI not found. Will attempt to use npx.")
            try:
                # Check if npx is available if lighthouse is not directly installed
                subprocess.run(["npx", "--version"], capture_output=True, text=True, check=True)
                print("npx found. Will use 'npx lighthouse'.")
            except (subprocess.SubprocessError, FileNotFoundError):
                 print("Error: Neither Lighthouse CLI nor npx is available. Please install Node.js and Lighthouse CLI globally (npm install -g lighthouse) or ensure npx is in your PATH.")


        # Output subdirectories - always create these as they are used for report output
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
        # Check for Node.js (required for Lighthouse/npx)
        try:
            node_version = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
            print(f"Node.js version: {node_version.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Node.js is not installed. Please install Node.js to use this script.")
            return False

        # Check for Chrome/Chromium (required by Lighthouse)
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
        chrome_path = None # Store the found path

        # Prioritize chrome_path from arguments if provided (stored in self._chrome_path_arg)
        if hasattr(self, '_chrome_path_arg') and self._chrome_path_arg and os.path.exists(self._chrome_path_arg):
             chrome_found = True
             chrome_path = self._chrome_path_arg
             print(f"Using Chrome/Chromium found at specified path: {chrome_path}")
        else:
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_found = True
                    chrome_path = path
                    break

            if chrome_found:
                print(f"Chrome/Chromium found at: {chrome_path}")
            else:
                print("Error: Chrome or Chromium is not found. Please install Chrome or Chromium to use this script, or specify the path using --chrome-path.")
                return False

        # Update self._chrome_path_arg with the found/provided path for run_lighthouse_cli
        self._chrome_path_arg = chrome_path


        # If Lighthouse is not installed globally, check if npx can run it
        if not self.lighthouse_installed:
            try:
                # Check if 'npx lighthouse' works
                subprocess.run(["npx", "lighthouse", "--help"], capture_output=True, text=True, check=True)
                print("npx can run Lighthouse.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                 print("Error: Lighthouse CLI is not installed globally and npx cannot run it.")
                 print("Please install Node.js and Lighthouse CLI globally: npm install -g lighthouse")
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
        # Ensure the folder exists before walking
        if not os.path.isdir(folder_path):
            print(f"Error: Folder not found at {folder_path}")
            return []

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        return html_files

    def create_temp_server_config(self, folder_path):
        """
        Create a temporary server configuration file for running Lighthouse CI.
        Note: This is primarily for local folder testing with LHCI.

        Args:
            folder_path: Path to the folder containing static files

        Returns:
            Path to the configuration file or None if folder doesn't exist or write fails
        """
        if not os.path.isdir(folder_path):
            print(f"Error: Cannot create LHCI config, folder not found at {folder_path}")
            return None

        config_path = os.path.join(self.output_dir, "lighthouserc.js")

        # Use absolute path for staticDistDir in the config
        abs_folder_path = os.path.abspath(folder_path).replace('\\', '\\\\')

        config_content = f"""
module.exports = {{
  ci: {{
    collect: {{
      staticDistDir: '{abs_folder_path}',
      settings: {{
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
        skipAudits: ['uses-http2'],
      }},
    }},
    upload: {{
      target: 'filesystem',
      outputDir: '{os.path.abspath(self.output_dir).replace('\\', '\\\\')}',
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

        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            print(f"Created Lighthouse CI config at {config_path}")
            return config_path
        except IOError as e:
            print(f"Error writing Lighthouse CI config file {config_path}: {e}")
            return None


    def run_lighthouse_cli(self, url_or_file_path):
        """
        Run Lighthouse CLI on a single URL or HTML file.

        Args:
            url_or_file_path: URL or Path to the HTML file to test

        Returns:
            Tuple of (success, report_paths) or (False, None)
        """
        # Determine if input is a URL or file path
        if urllib.parse.urlparse(url_or_file_path).scheme in ['http', 'https']:
            test_url = url_or_file_path
            # Sanitize URL to get a safe base name for output files
            parsed_url = urllib.parse.urlparse(test_url)
            # Create a file-system friendly name from the URL path and query/fragment if present
            # Handle root path '/'
            path_base = re.sub(r'[^a-zA-Z0-9._-]', '_', parsed_url.path).strip('_') or 'index'
            # If path_base is empty after strip (e.g. root '/'), use 'index'
            if not path_base:
                 path_base = 'index'

            query_fragment_base = re.sub(r'[^a-zA-Z0-9._-]', '_', parsed_url.query + parsed_url.fragment).strip('_')

            # Combine network location, path base, and query/fragment base
            netloc_base = re.sub(r'[^a-zA-Z0-9._-]', '_', parsed_url.netloc).strip('_')

            if query_fragment_base:
                 url_base = f"{netloc_base}_{path_base}_{query_fragment_base}"
            else:
                 url_base = f"{netloc_base}_{path_base}"

            # Avoid excessively long filenames
            url_base = url_base[:100] # Truncate to 100 characters


        else:
            # Assume it's a file path, convert to file:// URL
            # Check if file exists before proceeding
            if not os.path.exists(url_or_file_path):
                print(f"Error: File not found at {url_or_file_path}")
                return False, None

            test_url = f"file://{os.path.abspath(url_or_file_path)}"
            file_base = os.path.splitext(os.path.basename(url_or_file_path))[0]
            url_base = file_base # Use file base name for output

        # Generate output file names: let Lighthouse append its own extensions
        base_output = os.path.join(self.html_dir, url_base)
        html_output  = f"{base_output}.html"
        json_output  = os.path.join(self.json_dir, f"{url_base}.json")


        # Prepare the command
        lighthouse_cmd = []

        if self.lighthouse_installed:
            lighthouse_cmd = ["lighthouse"]
        else:
            lighthouse_cmd = ["npx", "lighthouse"] # Use npx if not globally installed

        lighthouse_cmd.extend([
            test_url,
            "--output=html,json",
            f"--output-path={base_output}",
            "--chrome-flags=--headless", # Run in headless mode
            "--only-categories=performance,accessibility,best-practices,seo", # Limit categories
            "--quiet" # Suppress excessive Lighthouse output
        ])

        # Add chrome-path if available from check_dependencies or constructor
        if hasattr(self, '_chrome_path_arg') and self._chrome_path_arg:
             lighthouse_cmd.append(f"--chrome-path={self._chrome_path_arg}")


        try:
            print(f"Testing {url_or_file_path}...")
            # Use timeout to prevent hanging
            process = subprocess.run(lighthouse_cmd, capture_output=True, text=True, check=True, timeout=180) # Increased timeout to 3 minutes

            # Move the HTML report from base_output.report.html → html_output
            temp_html = f"{base_output}.report.html"
            if os.path.exists(temp_html):
                shutil.move(temp_html, html_output)

            # Now move the JSON report …
            temp_json = f"{base_output}.report.json"
            if os.path.exists(temp_json):
                shutil.move(temp_json, json_output)

            # Lighthouse >= 8.0 saves JSON with a .report.json extension when outputting multiple formats
            # We need to check for this and rename if necessary
            temp_json = f"{html_output}.report.json"
            if os.path.exists(temp_json):
                try:
                    shutil.move(temp_json, json_output)
                    # Verify the move
                    if not os.path.exists(json_output):
                         print(f"Warning: Temporary JSON file {temp_json} was not moved to {json_output}.")
                except Exception as move_error:
                     print(f"Error moving temporary JSON file {temp_json} to {json_output}: {move_error}")
            elif not os.path.exists(json_output):
                 # If the temp file wasn't there and the target isn't there, something went wrong
                 # Check stderr/stdout for clues
                 error_output = process.stderr + process.stdout # Combine for checking
                 if "LighthouseError" in error_output or "Error:" in error_output:
                      print(f"Lighthouse run for {url_or_file_path} failed to produce expected JSON report.")
                 else:
                      print(f"Warning: Expected JSON report {json_output} not found after Lighthouse run for {url_or_file_path}.")


            # If we reach here and json_output exists, it was successful
            if os.path.exists(json_output):
                 return True, (html_output, json_output)
            else:
                 # Indicate failure if JSON report was not generated
                 return False, None


        except FileNotFoundError:
             print(f"Error: Lighthouse command not found. Ensure Lighthouse CLI or npx is installed and in your PATH.")
             return False, None
        except subprocess.CalledProcessError as e:
            print(f"Error running Lighthouse on {url_or_file_path}. Command failed with exit code {e.returncode}.")
            print(f"Stderr: {e.stderr}")
            # Attempt to print stdout as it might contain useful info
            if e.stdout:
                 print(f"Stdout: {e.stdout}")
            return False, None
        except subprocess.TimeoutExpired:
            print(f"Error: Lighthouse timed out testing {url_or_file_path} after {e.timeout} seconds.")
            return False, None
        except Exception as e:
             print(f"An unexpected error occurred while testing {url_or_file_path}: {e}")
             import traceback
             traceback.print_exc()
             return False, None


    def test_sources(self, urls_or_file_paths):
        """
        Test a list of URLs or HTML files using Lighthouse CLI.
        Handles running tests in parallel.

        Args:
            urls_or_file_paths: List of URLs or Paths to the HTML files to test, or a single URL string

        Returns:
            List of paths to successfully generated JSON reports
        """
        # Ensure input is always a list for consistent processing
        if isinstance(urls_or_file_paths, str):
            sources_to_test = [urls_or_file_paths]
        elif isinstance(urls_or_file_paths, list):
            sources_to_test = urls_or_file_paths
        else:
            print(f"Error: Invalid input type for test_sources. Expected string (URL) or list.")
            return []


        if not sources_to_test:
            print("No sources provided to test.")
            return []

        print(f"Found {len(sources_to_test)} source(s) to test")

        json_reports = []
        # Using ThreadPoolExecutor for parallel execution if multiple sources are provided
        # If only one source, it will run sequentially with max_workers=1
        # Use max_workers based on number of sources or CPU cores, whichever is smaller
        max_workers = min(len(sources_to_test), os.cpu_count() or 1)
        if max_workers < 1: # Ensure at least 1 worker
             max_workers = 1

        # Use map to apply run_lighthouse_cli to all sources and collect results
        # Note: executor.map is blocking and returns results in order.
        # Using as_completed for better responsiveness with parallel runs.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
             future_to_source = {executor.submit(self.run_lighthouse_cli, source): source for source in sources_to_test}

             for future in future_to_source.as_completed():
                 source = future_to_source[future]
                 try:
                     # Get the result which is a tuple (success, paths)
                     success, paths = future.result()
                     if success and paths:
                         _, json_path = paths
                         # Double-check the JSON file exists before adding its path
                         if os.path.exists(json_path):
                              json_reports.append(json_path)
                         else:
                              # Warning already printed in run_lighthouse_cli, but keeping for safety
                              pass # Or add a specific warning if needed

                 except Exception as exc:
                     print(f'Exception occurred while testing {source}: {exc}')
                     import traceback
                     traceback.print_exc()


        return json_reports


    def run_lighthouse_ci(self, folder_path):
        """
        Run Lighthouse CI on a folder of static HTML files.
        Note: This method is less relevant for single URL testing.

        Args:
            folder_path: Path to the folder containing static files

        Returns:
            Boolean indicating success
        """
        # Create temporary configuration file
        config_path = self.create_temp_server_config(folder_path)
        if not config_path:
            return False

        # Prepare the command
        # Ensure npx is used if lighthouse CI isn't global
        lhci_cmd = ["npx", "@lhci/cli@latest", "autorun", "--config", config_path]

        try:
            print(f"Running Lighthouse CI on {folder_path}...")
            # Use timeout
            # Set a longer timeout for CI which might involve building and serving
            process = subprocess.run(lhci_cmd, capture_output=True, text=True, check=True, timeout=600) # 10 minutes timeout
            print("Lighthouse CI process completed.")
            print("Stdout:\n", process.stdout)
            print("Stderr:\n", process.stderr)
            return True

        except FileNotFoundError:
            print(f"Error: npx or @lhci/cli not found. Ensure Node.js and Lighthouse CI are installed.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"Error running Lighthouse CI. Command failed with exit code {e.returncode}.")
            print(f"Stderr: {e.stderr}")
            if e.stdout:
                 print(f"Stdout: {e.stdout}")
            return False
        except subprocess.TimeoutExpired:
            print(f"Error: Lighthouse CI timed out after {e.timeout} seconds.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while running Lighthouse CI: {e}")
            import traceback
            traceback.print_exc()
            return False


    def parse_json_report(self, json_path):
        """
        Parse a Lighthouse JSON report to extract key metrics.

        Args:
            json_path: Path to the JSON report file

        Returns:
            Dictionary of metrics or None if parsing fails
        """
        if not os.path.exists(json_path):
             print(f"Error: JSON report file not found at {json_path}")
             return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract scores - provide default 0 and handle potential missing keys safely
            categories = data.get('categories', {})
            scores = {
                'performance': categories.get('performance', {}).get('score', 0) * 100,
                'accessibility': categories.get('accessibility', {}).get('score', 0) * 100,
                'best_practices': categories.get('best-practices', {}).get('score', 0) * 100,
                'seo': categories.get('seo', {}).get('score', 0) * 100,
            }

            # Extract key metrics - provide default 0 and handle potential missing keys safely
            metrics = {}

            # Core Web Vitals and other key metrics
            audits = data.get('audits', {})
            metrics['fcp'] = audits.get('first-contentful-paint', {}).get('numericValue', 0) / 1000 # Convert to seconds
            metrics['lcp'] = audits.get('largest-contentful-paint', {}).get('numericValue', 0) / 1000 # Convert to seconds
            metrics['cls'] = audits.get('cumulative-layout-shift', {}).get('numericValue', 0)
            metrics['tbt'] = audits.get('total-blocking-time', {}).get('numericValue', 0) # Already in ms
            metrics['tti'] = audits.get('interactive', {}).get('numericValue', 0) / 1000 # Convert to seconds

            # Resource metrics
            metrics['total_bytes'] = audits.get('total-byte-weight', {}).get('numericValue', 0) / 1024 / 1024  # Convert to MB
            metrics['image_bytes'] = 0
            metrics['script_bytes'] = 0
            metrics['css_bytes'] = 0
            metrics['font_bytes'] = 0
            metrics['document_bytes'] = 0
            metrics['third_party_bytes'] = 0

            # Extract resource sizes by type from 'resource-summary' audit
            resource_summary_details = audits.get('resource-summary', {}).get('details', {})
            if resource_summary_details and 'items' in resource_summary_details:
                resource_summary_items = resource_summary_details['items']
                for item in resource_summary_items:
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
                        metrics['document_bytes'] = transfer_size # This might be included in total but worth extracting

            # Extract third-party bytes from 'third-party-summary' audit
            third_party_details = audits.get('third-party-summary', {}).get('details', {})
            if third_party_details and 'items' in third_party_details:
                third_party_items = third_party_details['items']
                for item in third_party_items:
                    metrics['third_party_bytes'] += item.get('transferSize', 0) / 1024 / 1024  # Convert to MB


            return {
                'scores': scores,
                'metrics': metrics
            }

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {json_path}. File might be corrupted or empty.")
            return None
        except Exception as e:
            print(f"Error parsing JSON report {json_path}: {e}")
            import traceback
            traceback.print_exc()
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
                print(f"Skipping CSV entry for {json_path} due to parsing error or missing data.")
                continue

            # Extract file/URL identifier from JSON path
            # This should match the base name used for the JSON file
            file_name = os.path.basename(json_path).replace('.json', '')

            row = {
                'source': file_name, # Renamed from 'file' to 'source' for clarity with URLs
                # Use .get() with default 0 or 0.0 to handle cases where a metric might be missing
                'performance_score': data['scores'].get('performance', 0.0),
                'accessibility_score': data['scores'].get('accessibility', 0.0),
                'best_practices_score': data['scores'].get('best_practices', 0.0),
                'seo_score': data['scores'].get('seo', 0.0),
                'first_contentful_paint': data['metrics'].get('fcp', 0.0),
                'largest_contentful_paint': data['metrics'].get('lcp', 0.0),
                'cumulative_layout_shift': data['metrics'].get('cls', 0.0),
                'total_blocking_time': data['metrics'].get('tbt', 0.0),
                'time_to_interactive': data['metrics'].get('tti', 0.0),
                'total_size_mb': data['metrics'].get('total_bytes', 0.0),
                'image_size_mb': data['metrics'].get('image_bytes', 0.0),
                'script_size_mb': data['metrics'].get('script_bytes', 0.0),
                'css_size_mb': data['metrics'].get('css_bytes', 0.0),
                'font_size_mb': data['metrics'].get('font_bytes', 0.0),
                'document_size_mb': data['metrics'].get('document_bytes', 0.0),
                'third_party_size_mb': data['metrics'].get('third_party_bytes', 0.0),
            }

            csv_data.append(row)

        # Write to CSV
        if csv_data:
            try:
                # Use the keys from the first row for fieldnames
                fieldnames = csv_data[0].keys()
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)

                print(f"Summary CSV saved to {output_path}")
            except IOError as e:
                print(f"Error writing CSV file {output_path}: {e}")
            except Exception as e:
                 print(f"An unexpected error occurred while writing CSV: {e}")

        else:
            print("No valid data available to write to CSV.")


    def generate_markdown_report(self, source_identifier, csv_path, output_path):
        """
        Generate a Markdown report with analysis and recommendations.

        Args:
            source_identifier: The folder path or URL(s) that were tested.
            csv_path: Path to the CSV summary file
            output_path: Path to save the Markdown report
        """
        if not os.path.exists(csv_path):
             print(f"Error: CSV summary file not found at {csv_path}. Cannot generate Markdown report.")
             # Still attempt to create an empty markdown file with an error message
             try:
                 with open(output_path, 'w', encoding='utf-8') as f:
                      f.write(f"# Website Performance Analysis Report\n\n")
                      f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                      f.write(f"Source(s) tested: {source_identifier}\n\n")
                      f.write("## Error\n\n")
                      f.write(f"Could not generate the full report because the summary CSV file was not found at `{csv_path}`.\n")
                      f.write("This likely indicates that the performance tests failed to produce any valid JSON reports.\n")
                 print(f"Created placeholder Markdown report at {output_path} due to missing CSV.")
             except IOError as e:
                  print(f"Error writing placeholder Markdown report file {output_path}: {e}")
             return


        try:
            # Load CSV data
            csv_data = []
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to numeric, handling potential errors
                    numeric_row = {}
                    for key, value in row.items():
                        if key == 'source':
                            numeric_row[key] = value
                        else:
                            try:
                                numeric_row[key] = float(value)
                            except (ValueError, TypeError):
                                # Handle cases where conversion fails (e.g., empty string, non-numeric text)
                                numeric_row[key] = 0.0
                    csv_data.append(numeric_row)

            if not csv_data:
                print("No data available in CSV to generate Markdown report.")
                # Still attempt to create an empty markdown file with a message
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Website Performance Analysis Report\n\n")
                        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"Source(s) tested: {source_identifier}\n\n")
                        f.write("## No Data\n\n")
                        f.write("The summary CSV file was empty. No performance data was available to generate the report.\n")
                    print(f"Created placeholder Markdown report at {output_path} due to empty CSV.")
                except IOError as e:
                     print(f"Error writing placeholder Markdown report file {output_path}: {e}")
                return

            num_pages = len(csv_data)

            # Calculate averages
            # Safely calculate averages even if some values are missing (defaulted to 0)
            # Avoid division by zero if csv_data is empty (though checked above)
            avg_scores = {
                'performance': sum(row.get('performance_score', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'accessibility': sum(row.get('accessibility_score', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'best_practices': sum(row.get('best_practices_score', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'seo': sum(row.get('seo_score', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
            }

            avg_metrics = {
                'fcp': sum(row.get('first_contentful_paint', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'lcp': sum(row.get('largest_contentful_paint', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'cls': sum(row.get('cumulative_layout_shift', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'tbt': sum(row.get('total_blocking_time', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'tti': sum(row.get('time_to_interactive', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'total_bytes': sum(row.get('total_size_mb', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'image_bytes': sum(row.get('image_size_mb', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'script_bytes': sum(row.get('script_bytes', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
                'css_bytes': sum(row.get('css_bytes', 0) for row in csv_data) / num_pages if num_pages > 0 else 0,
            }


            # Sort data to find worst performers (only if multiple pages)
            # Use .get() with default to handle potential missing keys gracefully during sorting
            worst_performance = sorted(csv_data, key=lambda x: x.get('performance_score', 0))[:min(3, num_pages)] if num_pages > 1 else csv_data
            worst_accessibility = sorted(csv_data, key=lambda x: x.get('accessibility_score', 0))[:min(3, num_pages)] if num_pages > 1 else csv_data
            largest_pages = sorted(csv_data, key=lambda x: x.get('total_size_mb', 0), reverse=True)[:min(3, num_pages)] if num_pages > 1 else csv_data


            # Map scores to rubric levels
            def get_performance_level(score):
                # Ensure score is treated as a number
                try:
                    score = float(score)
                except (ValueError, TypeError):
                    score = 0.0 # Default to 0 if conversion fails

                if score >= 75: # Adjusted ranges to match rubric descriptions more closely (75-100 for Distinction)
                    return "Distinction (75-100%)"
                elif score >= 65:
                    return "Credit (65-74%)"
                elif score >= 50:
                    return "Pass (50-64%)"
                else:
                    return "Fail (0-49%)"

            perf_level = get_performance_level(avg_scores.get('performance', 0)) # Use .get() for safety

            # Generate recommendations based on metrics
            recommendations = []

            # Use .get() for metrics for safety
            if avg_metrics.get('image_bytes', 0) > 0.5:  # More than 0.5 MB average image size
                recommendations.append("Optimize images by using formats like WebP, compressing, and properly sizing images for their display size")

            if avg_metrics.get('lcp', 0) > 2.5:  # LCP > 2.5s
                recommendations.append("Improve Largest Contentful Paint (LCP) by optimizing server response times, reducing render-blocking resources, and optimizing critical resources")

            if avg_metrics.get('cls', 0) > 0.1:  # CLS > 0.1
                recommendations.append("Improve Cumulative Layout Shift (CLS) by setting size attributes on images and videos, avoiding inserting content above existing content, and using transform animations instead of animations that trigger layout changes")

            if avg_metrics.get('tbt', 0) > 300:  # TBT > 300ms
                recommendations.append("Reduce Total Blocking Time (TBT) by minimizing main thread work, reducing JavaScript execution time, and breaking up long tasks")

            if avg_metrics.get('total_bytes', 0) > 2.0: # More than 2MB total size as a general indicator
                 recommendations.append("Reduce the total page weight by minimizing resource sizes (images, scripts, CSS, etc.) and removing unnecessary assets.")


            # Write Markdown report
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("# Website Performance Analysis Report\n\n")
                    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    # Indicate source type
                    source_desc = "URL" if isinstance(source_identifier, str) and urllib.parse.urlparse(source_identifier).scheme in ['http', 'https'] else "Folder"
                    f.write(f"Source(s) tested ({source_desc}): {source_identifier}\n\n")


                    f.write("## Summary\n\n")
                    if num_pages > 1:
                        f.write(f"- Analyzed {num_pages} pages from {source_identifier}\n")
                    else:
                         f.write(f"- Analyzed {source_identifier}\n")

                    # Use .get() for scores for safety in f-strings
                    f.write(f"- Overall site performance: {avg_scores.get('performance', 0):.1f}/100\n")
                    f.write(f"- Accessibility score: {avg_scores.get('accessibility', 0):.1f}/100\n")
                    f.write(f"- Best practices score: {avg_scores.get('best_practices', 0):.1f}/100\n")
                    f.write(f"- SEO score: {avg_scores.get('seo', 0):.1f}/100\n\n")

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

                    # Calculate points based on performance score (using avg_scores.get)
                    performance_score_for_points = avg_scores.get('performance', 0)
                    # Ensure consistent point scaling based on rubric levels
                    if performance_score_for_points >= 75:
                        # Scale points linearly from 7.5 at 75 to 10 at 100
                        points = min(10.0, 7.5 + (performance_score_for_points - 75) * (2.5/25.0))
                        percentage = min(100.0, 75 + (performance_score_for_points - 75) * (25/25.0))
                    elif performance_score_for_points >= 65:
                         # Scale points linearly from 6.5 at 65 to 7.49 at 74.9
                        points = min(7.49, 6.5 + (performance_score_for_points - 65) * (0.99/9.9))
                        percentage = min(74.9, 65 + (performance_score_for_points - 65) * (9.9/9.9))
                    elif performance_score_for_points >= 50:
                        # Scale points linearly from 5.0 at 50 to 6.49 at 64.9
                        points = min(6.49, 5.0 + (performance_score_for_points - 50) * (1.49/14.9))
                        percentage = min(64.9, 50 + (performance_score_for_points - 50) * (14.9/14.9))
                    else:
                        # Scale points linearly from 0 at 0 to 4.99 at 49.9
                        points = max(0.0, performance_score_for_points * (4.99/49.9))
                        percentage = max(0.0, performance_score_for_points * (49.9/49.9))

                    # Cap points and percentage at max values just in case of floating point inaccuracies
                    points = min(points, 10.0)
                    percentage = min(percentage, 100.0)


                    f.write(f"**Points:** {points:.2f}/10 ({percentage:.1f}%)\n\n")

                    # Core Web Vitals
                    f.write("## Core Web Vitals\n\n")
                    f.write("| Metric | Average Value | Target | Status |\n")
                    f.write("|--------|--------------|--------|--------|\n")

                    # FCP status (using .get() for metrics)
                    fcp_value = avg_metrics.get('fcp', 0.0)
                    fcp_status = "✅ Good" if fcp_value < 1.8 else "⚠️ Needs Improvement" if fcp_value < 3 else "❌ Poor"
                    f.write(f"| First Contentful Paint (FCP) | {fcp_value:.2f}s | < 1.8s | {fcp_status} |\n")

                    # LCP status (using .get() for metrics)
                    lcp_value = avg_metrics.get('lcp', 0.0)
                    lcp_status = "✅ Good" if lcp_value < 2.5 else "⚠️ Needs Improvement" if lcp_value < 4 else "❌ Poor"
                    f.write(f"| Largest Contentful Paint (LCP) | {lcp_value:.2f}s | < 2.5s | {lcp_status} |\n")

                    # CLS status (using .get() for metrics)
                    cls_value = avg_metrics.get('cls', 0.0)
                    cls_status = "✅ Good" if cls_value < 0.1 else "⚠️ Needs Improvement" if cls_value < 0.25 else "❌ Poor"
                    f.write(f"| Cumulative Layout Shift (CLS) | {cls_value:.3f} | < 0.1 | {cls_status} |\n")

                    # TBT status (using .get() for metrics)
                    tbt_value = avg_metrics.get('tbt', 0.0)
                    tbt_status = "✅ Good" if tbt_value < 200 else "⚠️ Needs Improvement" if tbt_value < 600 else "❌ Poor"
                    f.write(f"| Total Blocking Time (TBT) | {tbt_value:.0f}ms | < 200ms | {tbt_status} |\n")

                    # TTI status (using .get() for metrics)
                    tti_value = avg_metrics.get('tti', 0.0)
                    tti_status = "✅ Good" if tti_value < 3.8 else "⚠️ Needs Improvement" if tti_value < 7.3 else "❌ Poor"
                    f.write(f"| Time to Interactive (TTI) | {tti_value:.2f}s | < 3.8s | {tti_status} |\n\n")

                    # Resource Usage
                    f.write("## Resource Usage\n\n")
                    f.write("| Resource Type | Average Size (MB) |\n")
                    f.write("|---------------|-------------------|\n")
                    # Use .get() for metrics in f-strings
                    f.write(f"| Total Size | {avg_metrics.get('total_bytes', 0.0):.2f} |\n")
                    f.write(f"| Images | {avg_metrics.get('image_bytes', 0.0):.2f} |\n")
                    f.write(f"| JavaScript | {avg_metrics.get('script_bytes', 0.0):.2f} |\n")
                    f.write(f"| CSS | {avg_metrics.get('css_bytes', 0.0):.2f} |\n\n")


                    # Largest Pages (only if multiple pages)
                    if num_pages > 1:
                        f.write("## Largest Pages\n\n")
                        f.write("| Source | Total Size (MB) | Performance Score |\n")
                        f.write("|------|-----------------|-------------------|\n")

                        # Use .get() for safety when accessing page data
                        for page in largest_pages:
                            f.write(f"| {page.get('source', 'N/A')} | {page.get('total_size_mb', 0.0):.2f} | {page.get('performance_score', 0.0):.1f} |\n")

                        f.write("\n")

                    # Pages with Lowest Performance Scores (only if multiple pages)
                    if num_pages > 1:
                        f.write("## Pages with Lowest Performance Scores\n\n")
                        f.write("| Source | Performance Score | LCP (s) | TBT (ms) |\n")
                        f.write("|------|-------------------|---------|----------|\n")

                        # Use .get() for safety when accessing page data
                        for page in worst_performance:
                            f.write(f"| {page.get('source', 'N/A')} | {page.get('performance_score', 0.0):.1f} | {page.get('largest_contentful_paint', 0.0):.2f} | {page.get('total_blocking_time', 0.0):.0f} |\n")

                        f.write("\n")


                    # Recommendations
                    f.write("## Recommendations\n\n")

                    if recommendations:
                        for i, rec in enumerate(recommendations, 1):
                            f.write(f"{i}. {rec}\n")
                    else:
                        f.write("The site is performing well according to automated checks. Continue monitoring and maintaining good performance practices.\n")

                    f.write("\n")

                    # Links to individual reports (only if multiple pages)
                    if num_pages > 1:
                        f.write("## Individual Page Reports\n\n")

                        # Find HTML reports in the html output directory
                        html_reports = glob.glob(os.path.join(self.html_dir, "*.html"))

                        if html_reports:
                             # Sort reports alphabetically by filename for consistent order
                             html_reports.sort()
                             for report in html_reports:
                                 file_name = os.path.basename(report)
                                 # Match report file name base with source name in CSV
                                 page_name = file_name.replace('.html', '')

                                 # Find matching data in CSV for score/metric inclusion in the link list
                                 # Use next with a default value to avoid StopIteration if no match is found
                                 matching_data = next((x for x in csv_data if x.get('source') == page_name), None)

                                 # Calculate relative path from the directory where the markdown report is saved
                                 # to the html report directory.
                                 # Get the directory of the markdown report
                                 markdown_report_dir = os.path.dirname(output_path)
                                 # Get the directory of the html report
                                 html_report_dir = os.path.dirname(report)
                                 # Calculate the relative path from markdown_report_dir to html_report_dir
                                 relative_dir_path = os.path.relpath(html_report_dir, markdown_report_dir)
                                 # Construct the full relative path to the html file
                                 rel_path_to_html = os.path.join(relative_dir_path, file_name)


                                 if matching_data:
                                     f.write(f"- [{page_name}]({rel_path_to_html}) - Performance: {matching_data.get('performance_score', 0.0):.1f}, LCP: {matching_data.get('largest_contentful_paint', 0.0):.2f}s\n")
                                 else:
                                      # If no matching data found (shouldn't happen if processing was successful)
                                      f.write(f"- [{page_name}]({rel_path_to_html}) - Metrics not available\n")
                        else:
                             f.write("No individual HTML reports were found.\n")

                print(f"Markdown report saved to {output_path}")

            except IOError as e:
                print(f"Error writing Markdown report file {output_path}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while generating Markdown report: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"Error generating Markdown report: {e}")
            import traceback; traceback.print_exc()


    def test_sources(self, urls_or_file_paths):
        """
        Test a list of URLs or HTML files using Lighthouse CLI.
        Handles running tests in parallel.

        Args:
            urls_or_file_paths: List of URLs or Paths to the HTML files to test, or a single URL string

        Returns:
            List of paths to successfully generated JSON reports
        """
        # Ensure input is always a list for consistent processing
        if isinstance(urls_or_file_paths, str):
            sources_to_test = [urls_or_file_paths]
        elif isinstance(urls_or_file_paths, list):
            sources_to_test = urls_or_file_paths
        else:
            print(f"Error: Invalid input type for test_sources. Expected string (URL) or list.")
            return []


        if not sources_to_test:
            print("No sources provided to test.")
            return []

        print(f"Found {len(sources_to_test)} source(s) to test")

        json_reports = []
        # Using ThreadPoolExecutor for parallel execution if multiple sources are provided
        # If only one source, it will run sequentially with max_workers=1
        # Use max_workers based on number of sources or CPU cores, whichever is smaller
        max_workers = min(len(sources_to_test), os.cpu_count() or 1)
        if max_workers < 1: # Ensure at least 1 worker
             max_workers = 1

        # Using as_completed for better responsiveness with parallel runs.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
             # Map each source to a future
             future_to_source = {executor.submit(self.run_lighthouse_cli, source): source for source in sources_to_test}

             # Process results as they complete
             for future in as_completed(future_to_source):
                 source = future_to_source[future]
                 try:
                     # Get the result which is a tuple (success, paths)
                     success, paths = future.result()
                     if success and paths:
                         _, json_path = paths
                         # Double-check the JSON file exists before adding its path
                         if os.path.exists(json_path):
                              json_reports.append(json_path)
                         else:
                              # Warning already printed in run_lighthouse_cli if JSON was not generated
                              pass # Or add a specific warning here if needed


                 except Exception as exc:
                     print(f'Exception occurred while processing result for {source}: {exc}')
                     import traceback
                     traceback.print_exc()


        return json_reports


    def run_performance_tests(self, folder_path=None, url=None, chrome_path_arg=None, parallel=1, use_ci=False):
        """
        Run performance tests on all HTML files in a folder or a single URL.

        Args:
            folder_path: Path to the folder containing HTML files (optional)
            url: URL of the website to test (optional)
            chrome_path_arg: Path to Chrome/Chromium executable (optional, passed from args)
            parallel: Number of parallel tests to run (only applicable for folder analysis without --use-ci)
            use_ci: Whether to use Lighthouse CI (only applicable for folder analysis)

        Returns:
            Boolean indicating success
        """
        # Store the provided chrome_path for use in run_lighthouse_cli
        self._chrome_path_arg = chrome_path_arg

        if not folder_path and not url:
            print("Error: Either a folder path (--folder) or a URL (--url) must be provided.")
            return False
        if folder_path and url:
             print("Error: Please provide either a folder path (--folder) or a single URL (--url), not both.")
             return False

        # Check dependencies first
        if not self.check_dependencies():
            print("Dependency check failed. Aborting performance tests.")
            return False

        json_reports = []
        source_identifier = "" # To be used in the markdown report title

        if url:
             # Test a single URL
             source_identifier = url
             print(f"Starting performance test for URL: {url}")
             # Call test_sources which is now equipped to handle a single string URL
             json_reports = self.test_sources(url)

        elif folder_path:
            # Test files in a folder
            source_identifier = folder_path
            print(f"Starting performance test for folder: {folder_path}")

            if use_ci:
                print("Using Lighthouse CI for folder analysis.")
                # LHCI handles finding HTML files and running tests internally based on staticDistDir
                success = self.run_lighthouse_ci(folder_path)
                # Note: LHCI autorun exits with non-zero on assertion failures, but might still produce reports.
                # We proceed to collect reports regardless of the CI command's exit status here,
                # as long as the run_lighthouse_ci function itself didn't raise an exception or indicate a fundamental failure.
                if not success:
                     print("Lighthouse CI autorun command did not complete successfully, but checking for reports.")

                # After LHCI runs, find the generated JSON reports in the output directory
                # LHCI puts reports directly in the specified outputDir (self.output_dir)
                json_reports = glob.glob(os.path.join(self.output_dir, "*.json"))
                # Filter out potential config files or other non-report jsons
                json_reports = [f for f in json_reports if os.path.basename(f) not in ['lighthouserc.js', 'ci.log']] # Exclude config and potential LHCI log


            else:
                 # Use individual CLI runs on files found in the folder
                 print(f"Using individual Lighthouse CLI runs for files in folder with parallel={parallel}.")
                 html_files = self.get_html_files(folder_path)
                 if not html_files:
                     print(f"No HTML files found in {folder_path}. Nothing to test.")
                     # Proceed to report generation with empty data
                     pass # Will hit the 'if not json_reports' block later
                 else:
                     # Pass the list of html files to test_sources
                     json_reports = self.test_sources(html_files) # Parallelism is handled within test_sources


        # Check if any JSON reports were generated
        if not json_reports:
            print("No JSON reports were successfully generated. Cannot create detailed reports.")
            # Still create empty CSV and Markdown reports to indicate the process ran but failed to get data
            csv_path = os.path.join(self.csv_dir, "performance_summary.csv")
            self.create_summary_csv([], csv_path) # Pass empty list to create empty CSV with headers
            md_path = os.path.join(self.output_dir, "performance_report.md")
            # Pass a placeholder source identifier if testing failed early
            self.generate_markdown_report(source_identifier if source_identifier else "Unknown Source (No Reports Generated)", csv_path, md_path)
            return False # Indicate failure because no actual test data was produced


        # Create summary CSV
        csv_path = os.path.join(self.csv_dir, "performance_summary.csv")
        self.create_summary_csv(json_reports, csv_path)

        # Generate markdown report
        md_path = os.path.join(self.output_dir, "performance_report.md")
        # Pass the original source identifier (folder or URL)
        self.generate_markdown_report(source_identifier, csv_path, md_path)

        # Clean up temporary LHCI config file if it exists
        lhci_config_path = os.path.join(self.output_dir, "lighthouserc.js")
        if os.path.exists(lhci_config_path):
             try:
                 os.remove(lhci_config_path)
                 print(f"Cleaned up temporary LHCI config file: {lhci_config_path}")
             except OSError as e:
                 print(f"Error removing temporary LHCI config file {lhci_config_path}: {e}")

        # Clean up potential LHCI log file if it exists
        lhci_log_path = os.path.join(self.output_dir, "ci.log")
        if os.path.exists(lhci_log_path):
             try:
                 os.remove(lhci_log_path)
                 print(f"Cleaned up temporary LHCI log file: {lhci_log_path}")
             except OSError as e:
                 print(f"Error removing temporary LHCI log file {lhci_log_path}: {e}")


        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test performance of static HTML files or a website URL using Lighthouse.')
    parser.add_argument('--folder', help='Path to folder containing HTML files (for local testing)')
    parser.add_argument('--url', help='URL of the website to test (e.g., https://example.com). Use instead of --folder for live site testing.')
    parser.add_argument('--output', '-o', default='performance_reports', help='Output directory for reports. Creates html, json, and csv subdirectories.')
    parser.add_argument('--chrome-path', help='Optional: Path to Chrome/Chromium executable if not in default locations.')
    parser.add_argument('--parallel', '-p', type=int, default=1, help='Number of parallel tests to run (only applies to local folder analysis without --use-ci).')
    parser.add_argument('--use-ci', action='store_true', help='Use Lighthouse CI instead of individual CLI runs (only for local folder analysis). Requires @lhci/cli.')

    args = parser.parse_args()

    # Argument validation
    if not args.folder and not args.url:
        parser.error("Error: Either --folder or --url must be provided.")
    if args.folder and args.url:
         parser.error("Error: Please provide either --folder or --url, not both.")
    if args.url and args.parallel > 1:
         print("Warning: --parallel is ignored when testing a single --url.")
    if args.url and args.use_ci:
         print("Warning: --use-ci is ignored when testing a single --url.")


    tester = PerformanceTester(args.output)
    # Pass the chrome_path argument explicitly
    success = tester.run_performance_tests(folder_path=args.folder, url=args.url, chrome_path_arg=args.chrome_path, parallel=args.parallel, use_ci=args.use_ci)

    if success:
        print("Performance testing completed successfully.")
        print(f"Reports saved to {args.output}")
    else:
        print("Performance testing failed.")
        # It might be useful to exit with a non-zero code to indicate failure to the calling script
        sys.exit(1)

