import os
import sys
import argparse
import requests
import json
import yaml
import re
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin
import time
import concurrent.futures


class DeploymentAnalyzer:
    def __init__(self, github_repo_url, netlify_url, output_dir="deployment_analysis"):
        """
        Initialize the deployment analyzer.
        
        Args:
            github_repo_url: URL to the GitHub repository
            netlify_url: URL to the Netlify deployment
            output_dir: Directory to save analysis reports
        """


        self.github_repo_url = github_repo_url if github_repo_url else None
        self.netlify_url = netlify_url if netlify_url else None
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract repository owner and name from URL
        self.repo_owner, self.repo_name = self._extract_repo_info()
        
        # GitHub API details
        self.github_api_base = "https://api.github.com"
        self.github_headers = {}
       
        if self.github_repo_url: # Check if the URL exists before getting token
            # GitHub token (optional, increases rate limits)
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                self.github_headers["Authorization"] = f"token {github_token}"
        else:
            print("Warning: No GitHub URL provided. GitHub API features will be skipped.")

        
        # Netlify deployment details
        # Netlify deployment details - Handle cases where Netlify URL is missing/invalid
        self.netlify_domain = None
        if self.netlify_url: # Check if Netlify URL exists before parsing
             try:
                 parsed_url = urlparse(self.netlify_url)
                 self.netlify_domain = parsed_url.netloc
                 if not self.netlify_domain:
                      print(f"Warning: Could not extract domain from Netlify URL: {self.netlify_url}")
             except Exception as e:
                 print(f"Error parsing Netlify URL {self.netlify_url}: {e}")
                 self.netlify_domain = None # Ensure it's None on error


        if not self.netlify_domain:
             print("Warning: No valid Netlify URL provided. Netlify features will be skipped.")

        # Initialize scoring criteria
        self.github_workflow_criteria = {
            'has_workflow_files': {"max_score": 2},         # Example max score
            'has_netlify_deploy': {"max_score": 3},         # Example max score
            'build_steps_present': {"max_score": 2},        # Example max score
            'test_steps_present': {"max_score": 1},         # Example max score
            'conditional_deploy': {"max_score": 1},         # Example max score
            'cache_dependencies': {"max_score": 1}          # Example max score
        }

        self.netlify_criteria = {
            'site_loads': {"max_score": 3},                 # Example max score
            'custom_domain': {"max_score": 1},              # Example max score
            'ssl_configured': {"max_score": 2},             # Example max score
            'fast_load_time': {"max_score": 2},             # Example max score (perhaps tiered scoring based on this max)
            'passes_basic_seo': {"max_score": 1},           # Example max score
            'responsive_design': {"max_score": 1}           # Example max score
        }
    
    def _extract_repo_info(self):
        """Extract repository owner and name from the GitHub URL."""
        if not self.github_repo_url:
            # print("Warning: No GitHub URL provided. Skipping repository info extraction.") # Already printed in __init__
            return None, None # Return None, None immediately if no URL

        # Handle HTTPS GitHub URLs
        https_pattern = r"github\.com/([^/]+)/([^/]+)"
        https_match = re.search(https_pattern, self.github_repo_url)
        
        if https_match:
            return https_match.group(1), https_match.group(2)
        
        # Handle SSH GitHub URLs
        ssh_pattern = r"git@github\.com:([^/]+)/([^/]+)"
        ssh_match = re.search(ssh_pattern, self.github_repo_url)
        
        if ssh_match:
            # Remove .git suffix if present
            repo_name = ssh_match.group(2)
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            return ssh_match.group(1), repo_name
        
        raise ValueError("Invalid GitHub repository URL format. Use either HTTPS (https://github.com/owner/repo) or SSH (git@github.com:owner/repo) format.")
   
    # Example helper method structure (implement the actual logic)
    def _check_github_workflows(self):
         """Checks for GitHub Actions workflow file and recent runs."""
         print("Checking GitHub workflows...")
         workflow_present = False
         build_success = False
         deployment_success = False

         if not self.repo_owner or not self.repo_name:
             print("Skipping GitHub workflow check: Missing repository info.")
             return workflow_present, build_success, deployment_success # Return defaults

         # Use GitHub API to check for workflow files in .github/workflows
         # Use GitHub API to check recent workflow runs and their status

         return workflow_present, build_success, deployment_success


    # Example helper method structure (implement the actual logic)
    def _check_netlify_status(self):
        """Checks if the Netlify site is active."""
        print("Checking Netlify site status...")
        if not self.netlify_domain:
            print("Skipping Netlify status check: Missing Netlify domain.")
            return 0 # Return 0 if domain is missing

        # Try to fetch the Netlify site URL and check response status code
        try:
            response = requests.get(f"https://{self.netlify_domain}", timeout=10) # Add timeout
            if response.status_code == 200:
                print("Netlify site is active.")
                return 1 # Return 1 for active
            else:
                print(f"Netlify site returned status code: {response.status_code}")
                return 0 # Return 0 for not active or error
        except requests.exceptions.RequestException as e:
            print(f"Error checking Netlify site status for {self.netlify_domain}: {e}")
            return 0 # Return 0 on request error


    def get_repo_contents(self, path=""):
        """Get contents of a repository directory."""
        url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
        
        try:
            response = requests.get(url, headers=self.github_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching repository contents: {e}")
            return None
    
    def get_workflow_files(self):
        """Get GitHub Actions workflow files from the repository."""
        workflows_path = ".github/workflows"
        
        try:
            workflow_contents = self.get_repo_contents(workflows_path)
            
            if not workflow_contents:
                print(f"No workflow files found in {workflows_path}")
                return []
            
            workflow_files = []
            
            for item in workflow_contents:
                if item["type"] == "file" and (item["name"].endswith(".yml") or item["name"].endswith(".yaml")):
                    url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{item['path']}"
                    response = requests.get(url, headers=self.github_headers)
                    response.raise_for_status()
                    
                    content = response.json()
                    workflow_files.append({
                        "name": item["name"],
                        "path": item["path"],
                        "content": content.get("content", ""),
                        "encoding": content.get("encoding", "")
                    })
            
            return workflow_files
            
        except requests.RequestException as e:
            print(f"Error fetching workflow files: {e}")
            return []
    
    def get_netlify_config(self):
        """Get Netlify configuration files from the repository."""
        netlify_files = []
        
        # Check for netlify.toml
        try:
            netlify_toml = self.get_repo_contents("netlify.toml")
            if netlify_toml and netlify_toml.get("type") == "file":
                url = netlify_toml["download_url"]
                response = requests.get(url)
                response.raise_for_status()
                
                netlify_files.append({
                    "name": "netlify.toml",
                    "content": response.text
                })
        except:
            pass
        
        # Check for _redirects
        try:
            redirects = self.get_repo_contents("_redirects")
            if redirects and redirects.get("type") == "file":
                url = redirects["download_url"]
                response = requests.get(url)
                response.raise_for_status()
                
                netlify_files.append({
                    "name": "_redirects",
                    "content": response.text
                })
        except:
            pass
        
        # Check for _headers
        try:
            headers = self.get_repo_contents("_headers")
            if headers and headers.get("type") == "file":
                url = headers["download_url"]
                response = requests.get(url)
                response.raise_for_status()
                
                netlify_files.append({
                    "name": "_headers",
                    "content": response.text
                })
        except:
            pass
        
        return netlify_files
    
    def analyze_workflow_files(self, workflow_files):
        """
        Analyze GitHub workflow files for CI/CD implementation.
        
        Args:
            workflow_files: List of workflow file dictionaries
            
        Returns:
            Dictionary with workflow analysis results
        """
        if not workflow_files:
            return {
                "has_workflow_files": False,
                "netlify_deploy_workflows": [],
                "build_steps_present": False,
                "test_steps_present": False,
                "conditional_deploy": False,
                "cache_dependencies": False,
                "workflow_score": 3,
                "workflows_analyzed": 0
            }
        
        # Initialize results
        results = {
            "has_workflow_files": True,
            "netlify_deploy_workflows": [],
            "build_steps_present": False,
            "test_steps_present": False,
            "conditional_deploy": False,
            "cache_dependencies": False,
            "workflow_details": [],
            "workflows_analyzed": len(workflow_files)
        }
        
        for workflow in workflow_files:
            # Decode base64 content if needed
            if workflow["encoding"] == "base64":
                import base64
                content = base64.b64decode(workflow["content"]).decode("utf-8")
            else:
                content = workflow["content"]
            
            # Parse YAML content
            try:
                workflow_data = yaml.safe_load(content)
                
                # Check if this workflow is related to Netlify deployment
                is_netlify_workflow = self._is_netlify_workflow(workflow_data)
                
                # Check for build steps
                has_build_steps = self._has_build_steps(workflow_data)
                
                # Check for test steps
                has_test_steps = self._has_test_steps(workflow_data)
                
                # Check for conditional deployment
                has_conditional_deploy = self._has_conditional_deploy(workflow_data)
                
                # Check for dependency caching
                has_cache = self._has_cache_dependencies(workflow_data)
                
                # Update overall results
                if is_netlify_workflow:
                    results["netlify_deploy_workflows"].append(workflow["name"])
                
                if has_build_steps:
                    results["build_steps_present"] = True
                
                if has_test_steps:
                    results["test_steps_present"] = True
                
                if has_conditional_deploy:
                    results["conditional_deploy"] = True
                
                if has_cache:
                    results["cache_dependencies"] = True
                
                # Add details for this workflow
                results["workflow_details"].append({
                    "name": workflow["name"],
                    "is_netlify_workflow": is_netlify_workflow,
                    "has_build_steps": has_build_steps,
                    "has_test_steps": has_test_steps,
                    "has_conditional_deploy": has_conditional_deploy,
                    "has_cache_dependencies": has_cache
                })
                
            except yaml.YAMLError as e:
                print(f"Error parsing workflow YAML {workflow['name']}: {e}")
                results["workflow_details"].append({
                    "name": workflow["name"],
                    "error": str(e)
                })
        
        # Calculate workflow score
        workflow_score = self._calculate_workflow_score(results)
        results["workflow_score"] = workflow_score
        
        return results
    
    def _is_netlify_workflow(self, workflow_data):
        """Check if a workflow is related to Netlify deployment."""
        if not workflow_data:
            return False
        
        # Convert to string for simple text search
        workflow_str = str(workflow_data).lower()
        
        # Check for Netlify-related keywords
        netlify_keywords = [
            "netlify", "netlify-cli", "netlify deploy", "netlify-action", "netlify.toml"
        ]
        
        for keyword in netlify_keywords:
            if keyword in workflow_str:
                return True
        
        # Check for common Netlify GitHub Actions
        if "uses:" in workflow_str and any(action in workflow_str for action in [
            "actions/netlify", "netlify/actions", "nwtgck/actions-netlify", "jsmrcaga/action-netlify-deploy"
        ]):
            return True
        
        return False
    
    def _has_build_steps(self, workflow_data):
        """Check if a workflow has build steps."""
        if not workflow_data:
            return False
        
        # Convert to string for simple text search
        workflow_str = str(workflow_data).lower()
        
        # Check for build-related keywords
        build_keywords = [
            "npm run build", "yarn build", "build:", "steps:", "run: build",
            "npm ci", "yarn install", "pnpm install", "npm install"
        ]
        
        for keyword in build_keywords:
            if keyword in workflow_str:
                return True
        
        return False
    
    def _has_test_steps(self, workflow_data):
        """Check if a workflow has test steps."""
        if not workflow_data:
            return False
        
        # Convert to string for simple text search
        workflow_str = str(workflow_data).lower()
        
        # Check for test-related keywords
        test_keywords = [
            "npm test", "yarn test", "npm run test", "test:", "testing:",
            "jest", "mocha", "cypress", "playwright", "run: test"
        ]
        
        for keyword in test_keywords:
            if keyword in workflow_str:
                return True
        
        return False
    
    def _has_conditional_deploy(self, workflow_data):
        """Check if a workflow has conditional deployment."""
        if not workflow_data:
            return False
        
        # Check for typical conditions in workflow structure
        try:
            # Check for "on" section with branch filters
            on_section = workflow_data.get("on", {})
            
            # Check push with branches
            if isinstance(on_section, dict) and "push" in on_section:
                push_config = on_section["push"]
                if isinstance(push_config, dict) and ("branches" in push_config or "tags" in push_config):
                    return True
            
            # Check pull_request with branches
            if isinstance(on_section, dict) and "pull_request" in on_section:
                pr_config = on_section["pull_request"]
                if isinstance(pr_config, dict) and "branches" in pr_config:
                    return True
            
            # Check for "if" conditions in jobs or steps
            jobs = workflow_data.get("jobs", {})
            for job_name, job_config in jobs.items():
                # Check job-level "if"
                if "if" in job_config:
                    return True
                
                # Check step-level "if"
                steps = job_config.get("steps", [])
                for step in steps:
                    if isinstance(step, dict) and "if" in step:
                        return True
        
        except (TypeError, AttributeError):
            pass
        
        return False
    
    def _has_cache_dependencies(self, workflow_data):
        """Check if a workflow caches dependencies."""
        if not workflow_data:
            return False
        
        # Convert to string for simple text search
        workflow_str = str(workflow_data).lower()
        
        # Check for cache-related keywords
        cache_keywords = [
            "actions/cache", "cache:", "cache-dependency-path", "node-modules-cache"
        ]
        
        for keyword in cache_keywords:
            if keyword in workflow_str:
                return True
        
        return False
    
    def _calculate_workflow_score(self, results):
        """
        Calculate a score (0-10) for the workflow implementation.
        
        Args:
            results: Dictionary with workflow analysis results
            
        Returns:
            Score on a scale of 0-10
        """
        score = 5  # Start with a neutral score
        
        # Score based on having workflow files
        if not results["has_workflow_files"]:
            return 3  # Basic score for no workflow files
        
        # Score based on Netlify deployment workflows
        if results["netlify_deploy_workflows"]:
            score += 2
        else:
            score -= 1
        
        # Score based on build steps
        if results["build_steps_present"]:
            score += 1
        else:
            score -= 1
        
        # Score based on test steps (nice to have)
        if results["test_steps_present"]:
            score += 1
        
        # Score based on conditional deployment
        if results["conditional_deploy"]:
            score += 1
        else:
            score -= 0.5
        
        # Score based on dependency caching
        if results["cache_dependencies"]:
            score += 1
        
        # Ensure score is within bounds
        return max(0, min(10, score))
    
    def analyze_netlify_deployment(self):
        """
        Analyze the Netlify deployment.
        
        Returns:
            Dictionary with Netlify deployment analysis results
        """
        results = {
            "site_url": self.netlify_url,
            "site_loads": False,
            "is_netlify_domain": False,
            "custom_domain": False,
            "ssl_configured": False,
            "load_time": None,
            "basic_seo": {},
            "responsive_design": False,
            "netlify_score": 0
        }
        
        # Check if it's a Netlify domain
        netlify_domain_patterns = [
            r"\.netlify\.app$",
            r"\.netlify\.com$"
        ]
        
        for pattern in netlify_domain_patterns:
            if re.search(pattern, self.netlify_domain):
                results["is_netlify_domain"] = True
                break
        
        # If not a Netlify domain, it's a custom domain
        if not results["is_netlify_domain"]:
            results["custom_domain"] = True
        
        # Check if site loads and measure load time
        try:
            start_time = time.time()
            response = requests.get(self.netlify_url, timeout=10)
            end_time = time.time()
            
            load_time = end_time - start_time
            results["load_time"] = load_time
            
            # Check if site loads successfully
            if response.status_code == 200:
                results["site_loads"] = True
                
                # Check SSL (HTTPS)
                if self.netlify_url.startswith("https://"):
                    results["ssl_configured"] = True
                
                # Check basic SEO elements
                seo_results = self._check_basic_seo(response.text)
                results["basic_seo"] = seo_results
                
                # Check responsive design
                if self._has_responsive_design(response.text):
                    results["responsive_design"] = True
        
        except requests.RequestException as e:
            print(f"Error checking Netlify deployment: {e}")
            results["error"] = str(e)
        
        # Calculate Netlify score
        netlify_score = self._calculate_netlify_score(results)
        results["netlify_score"] = netlify_score
        
        return results
    
    def _check_basic_seo(self, html_content):
        """
        Check for basic SEO elements in the HTML content.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Dictionary with SEO analysis results
        """
        seo_results = {
            "has_title": False,
            "has_meta_description": False,
            "has_viewport_meta": False,
            "has_h1": False,
            "has_img_alt": True,  # Default to true, will be set to false if we find images without alt
            "seo_score": 0
        }
        
        # Check for title tag
        title_pattern = r"<title>(.+?)</title>"
        title_match = re.search(title_pattern, html_content, re.IGNORECASE)
        if title_match:
            seo_results["has_title"] = True
        
        # Check for meta description - FIXED PATTERN
        meta_desc_pattern = r'<meta\s+name=["|\']description["|\']s*content=["|\'](.+?)["|\']s*/?>'
        meta_desc_match = re.search(meta_desc_pattern, html_content, re.IGNORECASE)
        if meta_desc_match:
            seo_results["has_meta_description"] = True
        
        # Check for viewport meta tag - FIXED PATTERN
        viewport_pattern = r'<meta\s+name=["|\']viewport["|\']s*content=["|\'](.+?)["|\']s*/?>'
        viewport_match = re.search(viewport_pattern, html_content, re.IGNORECASE)
        if viewport_match:
            seo_results["has_viewport_meta"] = True
        
        # Check for h1 tag
        h1_pattern = r"<h1\b[^>]*>(.*?)</h1>"
        h1_match = re.search(h1_pattern, html_content, re.IGNORECASE)
        if h1_match:
            seo_results["has_h1"] = True
        
        # Check for images without alt attributes
        img_pattern = r"<img\b[^>]*>"
        img_matches = re.finditer(img_pattern, html_content, re.IGNORECASE)
        
        for img_match in img_matches:
            img_tag = img_match.group(0)
            alt_pattern = r'\balt=["|\'](.+?)["|\']'
            alt_match = re.search(alt_pattern, img_tag, re.IGNORECASE)
            
            if not alt_match:
                seo_results["has_img_alt"] = False
                break
        
        # Calculate SEO score
        seo_score = 0
        if seo_results["has_title"]:
            seo_score += 2
        if seo_results["has_meta_description"]:
            seo_score += 2
        if seo_results["has_viewport_meta"]:
            seo_score += 2
        if seo_results["has_h1"]:
            seo_score += 2
        if seo_results["has_img_alt"]:
            seo_score += 2
        
        seo_results["seo_score"] = seo_score / 10  # Normalize to 0-1 scale
        
        return seo_results
    
    def _has_responsive_design(self, html_content):
        """
        Check if the HTML content has responsive design elements.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Boolean indicating if responsive design elements are present
        """
        # Check for viewport meta tag (most important for responsiveness)
        viewport_pattern = r'<meta\s+name=["|\']viewport["|\']s*content=["|\'](.+?)["|\']s*/?>'
        viewport_match = re.search(viewport_pattern, html_content, re.IGNORECASE)
        if viewport_match:
            return True
        
        # Check for responsive CSS frameworks
        responsive_frameworks = [
            "bootstrap", "tailwind", "bulma", "foundation", "materialize",
            "semantic-ui", "pure-css", "skeleton", "milligram", "flex", "grid"
        ]
        
        for framework in responsive_frameworks:
            if framework in html_content.lower():
                return True
        
        # Check for media queries
        media_query_pattern = r"@media\s*\("
        media_query_match = re.search(media_query_pattern, html_content, re.IGNORECASE)
        if media_query_match:
            return True
        
        return False
    
    def _calculate_netlify_score(self, results):
        """
        Calculate a score (0-10) for the Netlify deployment.
        
        Args:
            results: Dictionary with Netlify deployment analysis results
            
        Returns:
            Score on a scale of 0-10
        """
        score = 5  # Start with a neutral score
        
        # Score based on site loading
        if results["site_loads"]:
            score += 2
        else:
            return 2  # If site doesn't load, return low score immediately
        
        # Score based on SSL configuration
        if results["ssl_configured"]:
            score += 1
        else:
            score -= 1
        
        # Score based on load time
        load_time = results["load_time"]
        if load_time is not None:
            if load_time < 1.0:
                score += 1.5  # Excellent load time
            elif load_time < 2.0:
                score += 1  # Good load time
            elif load_time < 3.0:
                score += 0.5  # Acceptable load time
            elif load_time > 5.0:
                score -= 1  # Poor load time
        
        # Score based on SEO
        seo_score = results["basic_seo"].get("seo_score", 0)
        score += seo_score
        
        # Score based on responsive design
        if results["responsive_design"]:
            score += 0.5
        
        # Score based on custom domain (bonus)
        if results["custom_domain"]:
            score += 0.5
        
        # Ensure score is within bounds
        return max(0, min(10, score))
    
    def calculate_overall_score(self, workflow_score, netlify_score):
        """
        Calculate overall deployment score based on workflow and Netlify scores.
        
        Args:
            workflow_score: Score for GitHub workflow (0-10)
            netlify_score: Score for Netlify deployment (0-10)
            
        Returns:
            Overall score (0-10)
        """
        # Weight the workflow and Netlify scores
        # Give more weight to Netlify since a working site is more important than the workflow
        workflow_weight = 0.4
        netlify_weight = 0.6
        
        overall_score = (workflow_score * workflow_weight) + (netlify_score * netlify_weight)
        
        return overall_score
    
    def map_to_rubric(self, score):
        """
        Map a score (0-10) to the rubric scale.
        
        Args:
            score: Score on a 0-10 scale
            
        Returns:
            Tuple of (performance_level, points_out_of_10, percentage)
        """
        if score >= 8.5:
            performance = "Distinction (75-100%)"
            percentage = min(100, 75 + (score - 8.5) * 25 / 1.5)
            points = 10 * percentage / 100
        elif score >= 7:
            performance = "Credit (65-74%)"
            percentage = 65 + (score - 7) * 9 / 1.5
            points = 10 * percentage / 100
        elif score >= 5:
            performance = "Pass (50-64%)"
            percentage = 50 + (score - 5) * 14 / 2
            points = 10 * percentage / 100
        else:
            performance = "Fail (0-49%)"
            percentage = score * 49 / 5
            points = 10 * percentage / 100
        
        return (performance, round(points, 2), round(percentage, 1))
    
    def analyze_deployment(self):
        """
        Perform a complete analysis of the deployment.
        
        Returns:
            Dictionary with analysis results
        """
        # --- Assign zero score immediately if URLs are missing ---
        # This is the main check for the "zero marks if no URL" rule
        if not self.github_repo_url or not self.netlify_url:
            print("Missing GitHub or Netlify URL. Assigning zero score for deployment.")
            details_msg = "Missing GitHub or Netlify URL. Full deployment analysis skipped."
            recommendations_msg = "Ensure both a valid GitHub repository URL and Netlify deployment URL are provided for a full assessment."

            # Return a dictionary with all scores set to 0
            total_max_score = sum(crit["max_score"] for crit_type in [self.github_workflow_criteria, self.netlify_criteria] for crit in crit_type.values())
            points_earned = 0
            percentage = (points_earned / total_max_score) * 100 if total_max_score > 0 else 0

            return {
                "github_workflow_score": 0,
                "netlify_status_score": 0,
                "build_settings_score": 0,
                "custom_domain_score": 0,
                "https_score": 0,
                "redirects_score": 0,
                "overall_score": 0, # Sum of scores before weighting
                "performance_level": "Incomplete Submission - Missing URLs",
                "points": points_earned,
                "percentage": percentage,
                "details": details_msg,
                "recommendations": recommendations_msg
            }

        # Get and analyze workflow files
        workflow_files = self.get_workflow_files()
        workflow_analysis = self.analyze_workflow_files(workflow_files)
        
        # Get and analyze Netlify config files
        netlify_config_files = self.get_netlify_config()
        
        # Analyze Netlify deployment
        netlify_analysis = self.analyze_netlify_deployment()
        
        # Calculate overall score
        workflow_score = workflow_analysis["workflow_score"]
        netlify_score = netlify_analysis["netlify_score"]
        overall_score = self.calculate_overall_score(workflow_score, netlify_score)
        
        # Map to rubric
        performance_level, points, percentage = self.map_to_rubric(overall_score)
        
        # Generate the report
        self.generate_deployment_report(
            workflow_analysis, 
            netlify_config_files,
            netlify_analysis,
            overall_score,
            performance_level,
            points,
            percentage
        )
        
        return {
            "workflow_analysis": workflow_analysis,
            "netlify_config_files": netlify_config_files,
            "netlify_analysis": netlify_analysis,
            "overall_score": overall_score,
            "performance_level": performance_level,
            "points": points,
            "percentage": percentage
        }
    
    def generate_deployment_report(self, workflow_analysis, netlify_config_files, 
                                   netlify_analysis, overall_score, performance_level,
                                   points, percentage):
        """
        Generate a deployment analysis report in Markdown format.
        
        Args:
            workflow_analysis: Results of GitHub workflow analysis
            netlify_config_files: List of Netlify configuration files
            netlify_analysis: Results of Netlify deployment analysis
            overall_score: Overall deployment score
            performance_level: Performance level according to rubric
            points: Points awarded out of 10
            percentage: Percentage score
        """
        report_path = os.path.join(self.output_dir, "deployment_analysis.md")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Deployment Analysis Report\n\n")
            f.write(f"**GitHub Repository:** [{self.repo_owner}/{self.repo_name}]({self.github_repo_url})\n\n")
            f.write(f"**Netlify Deployment:** [{self.netlify_domain}]({self.netlify_url})\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall assessment
            f.write("## Overall Assessment\n\n")
            f.write(f"**Overall Score:** {overall_score:.2f}/10\n\n")
            f.write(f"**Performance Level:** {performance_level}\n\n")
            f.write(f"**Points:** {points}/10 ({percentage}%)\n\n")
            
            f.write("### Rubric Criteria\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Expert deployment with optimised settings and CI/CD implementation | 7.5-10 |\n")
            f.write("| Credit (65-74%) | Smooth deployment with proper configuration | 6.5-7.49 |\n")
            f.write("| Pass (50-64%) | Basic deployment with functional site | 5-6.49 |\n")
            f.write("| Fail (0-49%) | Deployment issues or incorrect implementation | 0-4.99 |\n\n")
            
            # GitHub workflow analysis
            f.write("## GitHub Workflow Analysis\n\n")
            
            workflow_score = workflow_analysis["workflow_score"]
            f.write(f"**Workflow Score:** {workflow_score:.2f}/10\n\n")
            
            if workflow_analysis["has_workflow_files"]:
                f.write(f"- **Workflow Files Found:** Yes ({workflow_analysis['workflows_analyzed']} files)\n")
                
                if workflow_analysis["netlify_deploy_workflows"]:
                    f.write(f"- **Netlify Deployment Workflows:** Yes ({len(workflow_analysis['netlify_deploy_workflows'])} files)\n")
                    for workflow in workflow_analysis["netlify_deploy_workflows"]:
                        f.write(f"  - {workflow}\n")
                else:
                    f.write("- **Netlify Deployment Workflows:** No\n")
                
                f.write(f"- **Build Steps Present:** {'Yes' if workflow_analysis['build_steps_present'] else 'No'}\n")
                f.write(f"- **Test Steps Present:** {'Yes' if workflow_analysis['test_steps_present'] else 'No'}\n")
                f.write(f"- **Conditional Deployment:** {'Yes' if workflow_analysis['conditional_deploy'] else 'No'}\n")
                f.write(f"- **Dependency Caching:** {'Yes' if workflow_analysis['cache_dependencies'] else 'No'}\n")
            else:
                f.write("- **Workflow Files Found:** No\n")
            
            # Netlify configuration
            f.write("\n## Netlify Configuration\n\n")
            
            if netlify_config_files:
                f.write(f"**Configuration Files Found:** Yes ({len(netlify_config_files)} files)\n\n")
                
                for config_file in netlify_config_files:
                    f.write(f"### {config_file['name']}\n\n")
                    f.write("```\n")
                    f.write(config_file['content'][:500])  # Show only first 500 characters
                    if len(config_file['content']) > 500:
                        f.write("\n... (truncated)")
                    f.write("\n```\n\n")
            else:
                f.write("**Configuration Files Found:** No\n\n")
                f.write("No Netlify configuration files (netlify.toml, _redirects, _headers) were found in the repository.\n\n")
            
            # Netlify deployment analysis
            f.write("## Netlify Deployment Analysis\n\n")
            
            netlify_score = netlify_analysis["netlify_score"]
            f.write(f"**Netlify Score:** {netlify_score:.2f}/10\n\n")
            
            f.write(f"- **Site URL:** [{netlify_analysis['site_url']}]({netlify_analysis['site_url']})\n")
            f.write(f"- **Site Loads:** {'Yes' if netlify_analysis['site_loads'] else 'No'}\n")
            
            if netlify_analysis["site_loads"]:
                f.write(f"- **Load Time:** {netlify_analysis['load_time']:.2f} seconds\n")
                f.write(f"- **SSL Configured:** {'Yes' if netlify_analysis['ssl_configured'] else 'No'}\n")
                f.write(f"- **Custom Domain:** {'Yes' if netlify_analysis['custom_domain'] else 'No'}\n")
                f.write(f"- **Responsive Design:** {'Yes' if netlify_analysis['responsive_design'] else 'No'}\n")
                
                # SEO details
                seo_results = netlify_analysis["basic_seo"]
                f.write("- **Basic SEO:**\n")
                f.write(f"  - Title tag: {'Present' if seo_results.get('has_title', False) else 'Missing'}\n")
                f.write(f"  - Meta description: {'Present' if seo_results.get('has_meta_description', False) else 'Missing'}\n")
                f.write(f"  - Viewport meta tag: {'Present' if seo_results.get('has_viewport_meta', False) else 'Missing'}\n")
                f.write(f"  - H1 heading: {'Present' if seo_results.get('has_h1', False) else 'Missing'}\n")
                f.write(f"  - Image alt attributes: {'Properly used' if seo_results.get('has_img_alt', False) else 'Missing on some images'}\n")
            
            # Strengths and recommendations
            f.write("\n## Strengths and Recommendations\n\n")
            
            # Identify strengths
            f.write("### Strengths\n\n")
            strengths = []
            
            # GitHub workflow strengths
            if workflow_analysis["has_workflow_files"]:
                strengths.append("GitHub Actions workflows are set up for automation")
                
                if workflow_analysis["netlify_deploy_workflows"]:
                    strengths.append("Automated Netlify deployment configured in workflows")
                
                if workflow_analysis["build_steps_present"]:
                    strengths.append("Build steps are properly configured in workflows")
                
                if workflow_analysis["test_steps_present"]:
                    strengths.append("Test steps are included in the CI/CD process")
                
                if workflow_analysis["conditional_deploy"]:
                    strengths.append("Conditional deployment logic prevents unnecessary deployments")
                
                if workflow_analysis["cache_dependencies"]:
                    strengths.append("Dependency caching improves workflow efficiency")
            
            # Netlify strengths
            if netlify_analysis["site_loads"]:
                strengths.append("Site is successfully deployed and accessible")
                
                if netlify_analysis["ssl_configured"]:
                    strengths.append("SSL is properly configured (HTTPS)")
                
                if netlify_analysis["custom_domain"]:
                    strengths.append("Custom domain is configured instead of default Netlify domain")
                
                if netlify_analysis["load_time"] and netlify_analysis["load_time"] < 2.0:
                    strengths.append(f"Site loads quickly ({netlify_analysis['load_time']:.2f} seconds)")
                
                if netlify_analysis["responsive_design"]:
                    strengths.append("Site implements responsive design principles")
                
                # SEO strengths
                seo_score = netlify_analysis["basic_seo"].get("seo_score", 0)
                if seo_score > 0.7:
                    strengths.append("Good implementation of basic SEO elements")
            
            # Config file strengths
            if netlify_config_files:
                strengths.append("Netlify configuration files are present in the repository")
            
            # If no strengths found
            if not strengths:
                strengths.append("Basic GitHub and Netlify integration is established")
            
            # Write strengths
            for strength in strengths:
                f.write(f"- {strength}\n")
            
            # Identify recommendations
            f.write("\n### Recommendations\n\n")
            recommendations = []
            
            # GitHub workflow recommendations
            if not workflow_analysis["has_workflow_files"]:
                recommendations.append("Set up GitHub Actions workflows for CI/CD automation")
            else:
                if not workflow_analysis["netlify_deploy_workflows"]:
                    recommendations.append("Configure a workflow specifically for Netlify deployment")
                
                if not workflow_analysis["build_steps_present"]:
                    recommendations.append("Add build steps to your workflow to ensure proper compilation")
                
                if not workflow_analysis["test_steps_present"]:
                    recommendations.append("Consider adding test steps to ensure code quality")
                
                if not workflow_analysis["conditional_deploy"]:
                    recommendations.append("Add conditional logic to only deploy on specific branches or events")
                
                if not workflow_analysis["cache_dependencies"]:
                    recommendations.append("Implement dependency caching to speed up workflows")
            
            # Netlify recommendations
            if not netlify_analysis["site_loads"]:
                recommendations.append("Fix deployment issues as the site is not loading properly")
            else:
                if not netlify_analysis["ssl_configured"]:
                    recommendations.append("Configure SSL to use HTTPS for better security")
                
                if netlify_analysis["load_time"] and netlify_analysis["load_time"] > 3.0:
                    recommendations.append(f"Optimize site performance to reduce load time ({netlify_analysis['load_time']:.2f} seconds)")
                
                if not netlify_analysis["responsive_design"]:
                    recommendations.append("Implement responsive design for better mobile experience")
                
                # SEO recommendations
                seo_results = netlify_analysis["basic_seo"]
                if not seo_results.get("has_title", False):
                    recommendations.append("Add a descriptive title tag")
                
                if not seo_results.get("has_meta_description", False):
                    recommendations.append("Add a meta description for better SEO")
                
                if not seo_results.get("has_viewport_meta", False):
                    recommendations.append("Add a viewport meta tag for proper mobile display")
                
                if not seo_results.get("has_h1", False):
                    recommendations.append("Include at least one H1 heading")
                
                if not seo_results.get("has_img_alt", False):
                    recommendations.append("Add alt attributes to all images for accessibility")
            
            # Config file recommendations
            if not netlify_config_files:
                recommendations.append("Add Netlify configuration files (netlify.toml) for more control over deployment settings")
            
            # If no recommendations found
            if not recommendations:
                recommendations.append("Continue maintaining current deployment practices")
            
            # Write recommendations
            for recommendation in recommendations:
                f.write(f"- {recommendation}\n")
            
            # Conclusion
            f.write("\n## Conclusion\n\n")
            
            if overall_score >= 8.5:
                f.write("The deployment setup demonstrates excellent practices with both GitHub workflows and Netlify configuration. The CI/CD pipeline is well-optimized and the site is performing well.\n")
            elif overall_score >= 7:
                f.write("The deployment setup shows good practices with proper configuration of GitHub workflows and Netlify. With a few improvements, it could reach excellent status.\n")
            elif overall_score >= 5:
                f.write("The deployment setup meets basic requirements with a functional site, but there are several areas that could be improved for better efficiency and reliability.\n")
            else:
                f.write("The deployment setup has significant issues that need to be addressed. Focus on the recommendations to improve the deployment process and site functionality.\n")
        
        print(f"Deployment analysis report saved to {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze GitHub and Netlify deployment")
    parser.add_argument("github_repo_url", help="URL to the GitHub repository")
    parser.add_argument("netlify_url", help="URL to the Netlify deployment")
    parser.add_argument("--output", "-o", default="deployment_analysis", help="Output directory for reports")
    
    args = parser.parse_args()
    
    analyzer = DeploymentAnalyzer(args.github_repo_url, args.netlify_url, args.output)
    
    print(f"Analyzing deployment for repository: {args.github_repo_url}")
    print(f"Netlify URL: {args.netlify_url}")
    
    analysis_results = analyzer.analyze_deployment()
    
    print("\nAnalysis complete!")
    print(f"Overall Score: {analysis_results['overall_score']:.2f}/10")
    print(f"Performance Level: {analysis_results['performance_level']}")
    print(f"Points: {analysis_results['points']}/10 ({analysis_results['percentage']}%)")
    print(f"Report saved to {os.path.join(args.output, 'deployment_analysis.md')}")
