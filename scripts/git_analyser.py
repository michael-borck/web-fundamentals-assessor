import os
import sys
import argparse
import re
import json
import csv
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict, Counter


class GitRepoAnalyzer:
    def __init__(self, repo_path, output_dir="git_analysis_reports"):
        """
        Initialize the Git repository analyzer.
        
        Args:
            repo_path: Path to the Git repository
            output_dir: Directory to save analysis reports
        """
        self.repo_path = repo_path
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if the path is a valid Git repository
        self.is_git_repo = self._is_git_repo()
        
        # Initialize scoring criteria
        self.commit_message_criteria = {
            'min_length': 10,         # Minimum acceptable commit message length
            'max_length': 72,         # Maximum recommended commit message length
            'descriptive_words': [    # Words that indicate descriptive messages
                'add', 'fix', 'update', 'change', 'remove', 'refactor', 
                'implement', 'improve', 'optimize', 'resolve', 'revise'
            ],
            'detail_threshold': 20    # Length threshold for detailed messages
        }
        
        self.repo_organization_criteria = {
            'readme_exists': True,    # Repository should have a README file
            'license_exists': False,  # Educational projects may not need a license
            'gitignore_exists': True, # Repository should have a .gitignore file
            'max_top_level_dirs': 10, # Maximum recommended top-level directories
            'max_file_count': 1000,   # Maximum recommended file count
            'branch_count': 2         # Minimum recommended branch count
        }
        
        self.commit_frequency_criteria = {
            'days_analyzed': 30,      # Number of days to analyze for frequency
            'min_commits_per_week': 3, # Minimum recommended commits per week
            'max_gap_days': 7,        # Maximum recommended gap between commits
            'min_contributors': 1,    # Minimum recommended contributors
            'even_distribution': 0.3  # Maximum standard deviation ratio for evenness
        }
    
    def _is_git_repo(self):
        """Check if the path is a valid Git repository."""
        try:
            env = os.environ.copy()
            env['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
                env=env
            )
            return result.stdout.strip() == 'true'
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
   

    def _score_to_level(self, score):
        """
        Convert a numeric score to a quality level label.
        
        Args:
            score: Numeric score (0-10)
            
        Returns:
            String indicating quality level
        """
        if score >= 7.5:
            return "Distinction"
        elif score >= 6.5:
            return "Credit"
        elif score >= 5.0:
            return "Pass"
        else:
            return "Fail"
    
    def _map_to_rubric(self, score, max_points):
        """
        Map a 0-10 score to rubric performance levels and point values.
        
        Args:
            score: Score on a 0-10 scale
            max_points: Maximum points available for this criterion
            
        Returns:
            Tuple of (performance_level, points)
        """
        # Calculate percentage based on 0-10 scale
        percentage = (score / 10) * 100
        
        # Determine performance level
        if percentage >= 75:
            performance = "Distinction (75-100%)"
            # Map to points range 75-100% of max_points
            points = max(max_points * 0.75, min(max_points, (percentage / 100) * max_points))
        elif percentage >= 65:
            performance = "Credit (65-74%)"
            # Map to points range 65-74% of max_points
            points = max(max_points * 0.65, min(max_points * 0.74, (percentage / 100) * max_points))
        elif percentage >= 50:
            performance = "Pass (50-64%)"
            # Map to points range 50-64% of max_points
            points = max(max_points * 0.5, min(max_points * 0.64, (percentage / 100) * max_points))
        else:
            performance = "Fail (0-49%)"
            # Map to points range 0-49% of max_points
            points = min(max_points * 0.49, (percentage / 100) * max_points)
        
        return performance, round(points, 2)
    

    def run_git_command(self, command):
        """Run a Git command in the repository directory."""
        if not self.is_git_repo:
            raise ValueError("Not a valid Git repository")
        
        try:
            env = os.environ.copy()
            env['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
                env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            print(f"Error output: {e.stderr}")
            return None
    
    def get_commit_history(self):
        """
        Get the commit history of the repository.
        
        Returns:
            List of commit data dictionaries
        """
        # Get raw commit log with detailed information
        git_log_command = [
            'git', 'log', 
            '--pretty=format:{%n  "hash": "%H",%n  "abbreviated_hash": "%h",%n  "parent_hashes": "%P",%n  "author_name": "%an",%n  "author_email": "%ae",%n  "author_date": "%ai",%n  "committer_name": "%cn",%n  "committer_email": "%ce",%n  "committer_date": "%ci",%n  "subject": "%s",%n  "body": "%b",%n  "notes": "%N"%n},',
        ]
        log_output = self.run_git_command(git_log_command)
        
        if not log_output:
            return []
        
        # Parse the JSON output
        json_output = f"[{log_output.rstrip(',')}]"
        try:
            commits = json.loads(json_output)
        except json.JSONDecodeError as e:
            print(f"Error parsing Git log output: {e}")
            return []
        
        # Get stats for each commit (files changed, insertions, deletions)
        for commit in commits:
            stats_command = ['git', 'show', '--stat', '--format=format:', commit['hash']]
            stats_output = self.run_git_command(stats_command)
            
            if stats_output:
                # Parse stats output
                files_changed = 0
                insertions = 0
                deletions = 0
                
                stats_summary = stats_output.strip().split('\n')[-1]
                if stats_summary:
                    # Extract numbers for files changed, insertions, and deletions
                    files_match = re.search(r'(\d+) file', stats_summary)
                    insertions_match = re.search(r'(\d+) insertion', stats_summary)
                    deletions_match = re.search(r'(\d+) deletion', stats_summary)
                    
                    if files_match:
                        files_changed = int(files_match.group(1))
                    if insertions_match:
                        insertions = int(insertions_match.group(1))
                    if deletions_match:
                        deletions = int(deletions_match.group(1))
                
                commit['stats'] = {
                    'files_changed': files_changed,
                    'insertions': insertions,
                    'deletions': deletions
                }
            else:
                commit['stats'] = {
                    'files_changed': 0,
                    'insertions': 0,
                    'deletions': 0
                }
        
        return commits
    
    def get_branches(self):
        """Get all branches in the repository."""
        branch_command = ['git', 'branch', '--all']
        branch_output = self.run_git_command(branch_command)
        
        if not branch_output:
            return []
        
        branches = []
        for line in branch_output.split('\n'):
            branch = line.strip().replace('* ', '')
            if branch:
                branches.append(branch)
        
        return branches
    
    def get_repository_structure(self):
        """Get the structure of the repository."""
        try:
            file_count = 0
            dir_count = 0
            top_level_dirs = []
            
            # Walk the repository directory
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                # Count files and directories
                file_count += len(files)
                dir_count += len(dirs)
                
                # Record top-level directories
                if root == self.repo_path:
                    top_level_dirs = dirs.copy()
            
            # Check for important files
            readme_exists = any(
                os.path.exists(os.path.join(self.repo_path, f)) 
                for f in ['README.md', 'README.txt', 'README']
            )
            
            license_exists = any(
                os.path.exists(os.path.join(self.repo_path, f)) 
                for f in ['LICENSE', 'LICENSE.md', 'LICENSE.txt']
            )
            
            gitignore_exists = os.path.exists(os.path.join(self.repo_path, '.gitignore'))
            
            return {
                'file_count': file_count,
                'directory_count': dir_count,
                'top_level_directories': top_level_dirs,
                'readme_exists': readme_exists,
                'license_exists': license_exists,
                'gitignore_exists': gitignore_exists
            }
        
        except Exception as e:
            print(f"Error analyzing repository structure: {e}")
            return None
    
    def analyze_commit_messages(self, commits):
        """
        Analyze the quality of commit messages.
        
        Args:
            commits: List of commit data dictionaries
            
        Returns:
            Dictionary with commit message analysis results
        """
        if not commits:
            return {
                'total_commits': 0,
                'average_length': 0,
                'quality_score': 0,
                'quality_breakdown': {},
                'top_words': [],
                'unique_contributors': []
            }
        
        # Initialize metrics
        total_commits = len(commits)
        message_lengths = []
        quality_scores = []
        quality_breakdown = {
            'excellent': 0,
            'good': 0,
            'acceptable': 0,
            'poor': 0
        }
        all_words = []
        contributors = set()
        
        # Analyze each commit message
        for commit in commits:
            subject = commit.get('subject', '')
            body = commit.get('body', '')
            author = commit.get('author_name', '')
            
            # Add to contributors
            contributors.add(author)
            
            # Calculate message length
            message = f"{subject} {body}".strip()
            message_length = len(message)
            message_lengths.append(message_length)
            
            # Extract words for word frequency analysis
            words = re.findall(r'\b[a-zA-Z]+\b', message.lower())
            all_words.extend(words)
            
            # Score the message quality
            score = self._score_commit_message(subject, body)
            quality_scores.append(score)
            
            # Classify the quality
            if score >= 8:
                quality_breakdown['excellent'] += 1
            elif score >= 6:
                quality_breakdown['good'] += 1
            elif score >= 4:
                quality_breakdown['acceptable'] += 1
            else:
                quality_breakdown['poor'] += 1
        
        # Calculate average message length
        average_length = sum(message_lengths) / total_commits if message_lengths else 0
        
        # Calculate average quality score
        average_quality = sum(quality_scores) / total_commits if quality_scores else 0
        
        # Get top words
        word_counts = Counter(all_words)
        # Exclude common words
        common_words = {'to', 'the', 'a', 'and', 'in', 'for', 'of', 'on', 'with', 'an'}
        filtered_word_counts = {word: count for word, count in word_counts.items() if word not in common_words}
        top_words = sorted(filtered_word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_commits': total_commits,
            'average_length': average_length,
            'quality_score': average_quality,
            'quality_breakdown': quality_breakdown,
            'top_words': top_words,
            'unique_contributors': list(contributors)
        }
    
    def _score_commit_message(self, subject, body):
        """
        Score the quality of a commit message on a scale of 0-10.
        
        Args:
            subject: Commit message subject/title
            body: Commit message body
            
        Returns:
            Quality score (0-10)
        """
        score = 5  # Start with a neutral score
        
        # Check if subject exists and is not empty
        if not subject:
            return 0
        
        # Evaluate subject length
        subject_length = len(subject)
        if subject_length < self.commit_message_criteria['min_length']:
            score -= 2  # Too short
        elif subject_length > self.commit_message_criteria['max_length']:
            score -= 1  # Too long
        elif self.commit_message_criteria['min_length'] <= subject_length <= 50:
            score += 1  # Good length
        
        # Check for descriptive words in subject
        has_descriptive_word = any(word in subject.lower() for word in self.commit_message_criteria['descriptive_words'])
        if has_descriptive_word:
            score += 1
        
        # Check if subject starts with a verb (common good practice)
        if re.match(r'^[A-Z]?[a-z]+s?\b', subject):
            score += 1
        
        # Check for detailed body
        if body and len(body) > self.commit_message_criteria['detail_threshold']:
            score += 2
        
        # Check for explanation of why the change was made (often indicated by "because", "since", etc.)
        if body and re.search(r'\b(because|since|as|to allow|to fix|to enable|in order to)\b', body, re.IGNORECASE):
            score += 1
        
        # Penalize for all caps (SHOUTING)
        if subject.isupper():
            score -= 1
        
        # Check for issue references (#123, GH-123, etc.)
        if re.search(r'(^|\s)#\d+\b|GH-\d+', subject + ' ' + body):
            score += 1
        
        # Ensure score is within bounds
        return max(0, min(10, score))
   
    
    def analyze_commit_frequency(self, commits):
        """
        Analyze the frequency and distribution of commits.
        
        Args:
            commits: List of commit data dictionaries
            
        Returns:
            Dictionary with commit frequency analysis results
        """
        if not commits:
            return {
                'commits_per_day': {},
                'commits_per_author': {},
                'daily_stats': {
                    'mean': 0,
                    'median': 0,
                    'std_dev': 0
                },
                'commit_gaps': [],
                'largest_gap': 0,
                'frequency_score': 0
            }
        
        # Sort commits by date
        sorted_commits = sorted(commits, key=lambda x: x.get('author_date', ''))
        
        # Calculate date range
        try:
            first_commit_date = datetime.strptime(sorted_commits[-1]['author_date'].split()[0], '%Y-%m-%d')
            last_commit_date = datetime.strptime(sorted_commits[0]['author_date'].split()[0], '%Y-%m-%d')
            
            # Ensure we analyze at least the specified days
            analysis_start_date = max(
                first_commit_date,
                last_commit_date - timedelta(days=self.commit_frequency_criteria['days_analyzed'])
            )
            
            # Calculate total project duration in days
            project_duration = (last_commit_date - first_commit_date).days + 1
            
            # Initialize data structures
            commits_per_day = defaultdict(int)
            commits_per_author = defaultdict(int)
            
            # Generate all dates in range
            current_date = analysis_start_date
            while current_date <= last_commit_date:
                commits_per_day[current_date.strftime('%Y-%m-%d')] = 0
                current_date += timedelta(days=1)
            
            # Count commits per day and author
            for commit in commits:
                commit_date = datetime.strptime(commit['author_date'].split()[0], '%Y-%m-%d')
                author = commit['author_name']
                
                if commit_date >= analysis_start_date:
                    commits_per_day[commit_date.strftime('%Y-%m-%d')] += 1
                    commits_per_author[author] += 1
            
            # Calculate gaps between commits
            commit_dates = [date for date, count in commits_per_day.items() if count > 0]
            commit_dates = sorted(commit_dates)
            
            gaps = []
            for i in range(1, len(commit_dates)):
                date1 = datetime.strptime(commit_dates[i-1], '%Y-%m-%d')
                date2 = datetime.strptime(commit_dates[i], '%Y-%m-%d')
                gap = (date2 - date1).days
                if gap > 1:  # Only count gaps larger than 1 day
                    gaps.append(gap)
            
            largest_gap = max(gaps) if gaps else 0
            
            # Calculate daily commit statistics
            daily_counts = list(commits_per_day.values())
            mean_commits = np.mean(daily_counts)
            median_commits = np.median(daily_counts)
            std_dev = np.std(daily_counts)
            std_dev_ratio = std_dev / mean_commits if mean_commits > 0 else 0
            
            # Calculate weekly commits
            days_analyzed = (last_commit_date - analysis_start_date).days + 1
            weeks_analyzed = max(1, days_analyzed / 7)
            total_commits = sum(daily_counts)
            commits_per_week = total_commits / weeks_analyzed
            
            # Calculate days with commits vs total days
            days_with_commits = sum(1 for count in daily_counts if count > 0)
            commit_day_ratio = days_with_commits / max(1, len(daily_counts))
            
            # Detect "commit burst" pattern
            max_commits_in_day = max(daily_counts) if daily_counts else 0
            commit_burst_ratio = max_commits_in_day / max(1, total_commits)
            
            # Calculate frequency score
            frequency_score = self._calculate_frequency_score(
                commits_per_week=commits_per_week,
                largest_gap=largest_gap,
                std_dev_ratio=std_dev_ratio,
                contributor_count=len(commits_per_author)
            )
            
            return {
                'commits_per_day': commits_per_day,
                'commits_per_author': commits_per_author,
                'daily_stats': {
                    'mean': mean_commits,
                    'median': median_commits,
                    'std_dev': std_dev
                },
                'std_dev_ratio': std_dev_ratio,
                'commit_gaps': gaps,
                'largest_gap': largest_gap,
                'commits_per_week': commits_per_week,
                'frequency_score': frequency_score,
                'project_duration': project_duration,
                'days_with_commits': days_with_commits,
                'commit_day_ratio': commit_day_ratio,
                'commit_burst_ratio': commit_burst_ratio,
                'max_commits_in_day': max_commits_in_day
            }
        
        except Exception as e:
            print(f"Error analyzing commit frequency: {e}")
            return {
                'error': str(e)
            }
      
        def _calculate_frequency_score(self, commits_per_week, largest_gap, std_dev_ratio, contributor_count):
            """
            Calculate a score for commit frequency and distribution.
            
            Args:
                commits_per_week: Average number of commits per week
                largest_gap: Largest gap between commits (in days)
                std_dev_ratio: Standard deviation of daily commits divided by mean
                contributor_count: Number of unique contributors
                
            Returns:
                Frequency score (0-10)
            """
            score = 5  # Start with a neutral score
            
            # Evaluate commits per week
            if commits_per_week >= self.commit_frequency_criteria['min_commits_per_week'] * 2:
                score += 2  # Excellent
            elif commits_per_week >= self.commit_frequency_criteria['min_commits_per_week']:
                score += 1  # Good
            elif commits_per_week >= self.commit_frequency_criteria['min_commits_per_week'] / 2:
                score -= 1  # Below recommended
            else:
                score -= 2  # Poor
            
            # Evaluate largest gap
            if largest_gap == 0:
                # No gaps means all commits are on the same day - this is bad practice
                score -= 4  # Severely penalize same-day commits
            elif largest_gap <= self.commit_frequency_criteria['max_gap_days'] / 2:
                score += 0.5  # Small gaps
            elif largest_gap > self.commit_frequency_criteria['max_gap_days']:
                score -= 1  # Too large gaps
            elif largest_gap > self.commit_frequency_criteria['max_gap_days'] * 2:
                score -= 2  # Very large gaps
            
            # Evaluate commit distribution evenness
            if std_dev_ratio <= self.commit_frequency_criteria['even_distribution'] / 2:
                score += 1  # Very even distribution
            elif std_dev_ratio <= self.commit_frequency_criteria['even_distribution']:
                score += 0.5  # Good distribution
            elif std_dev_ratio > self.commit_frequency_criteria['even_distribution'] * 2:
                score -= 1  # Very uneven distribution
            
            # Additional check for "commit burst" pattern (many commits in very short time)
            if commits_per_week > 10 and largest_gap <= 1:
                # This indicates a likely "commit burst" where many commits were made in a short period
                score -= 3  # Severely penalize commit bursts
            
            # Evaluate number of contributors
            if contributor_count >= self.commit_frequency_criteria['min_contributors'] * 2:
                score += 1  # Multiple contributors
            elif contributor_count >= self.commit_frequency_criteria['min_contributors']:
                score += 0.5  # Sufficient contributors
            else:
                score -= 0.5  # Too few contributors
            
            # Ensure score is within bounds
            return max(0, min(10, score))
        
    def analyze_repository_organization(self, repo_structure, branch_count):
        """
        Analyze the organization of the repository.
        
        Args:
            repo_structure: Dictionary with repository structure information
            branch_count: Number of branches
            
        Returns:
            Dictionary with repository organization analysis results
        """
        if not repo_structure:
            return {
                'organization_score': 0
            }
        
        score = 5  # Start with a neutral score
        
        # Evaluate README presence
        if repo_structure['readme_exists']:
            score += 1
        elif self.repo_organization_criteria['readme_exists']:
            score -= 1
        
        # Evaluate LICENSE presence
        if repo_structure['license_exists'] == self.repo_organization_criteria['license_exists']:
            score += 0.5
        
        # Evaluate .gitignore presence
        if repo_structure['gitignore_exists']:
            score += 1
        elif self.repo_organization_criteria['gitignore_exists']:
            score -= 1
        
        # Evaluate number of top-level directories
        top_level_count = len(repo_structure['top_level_directories'])
        if top_level_count <= self.repo_organization_criteria['max_top_level_dirs'] / 2:
            score += 1  # Very organized
        elif top_level_count <= self.repo_organization_criteria['max_top_level_dirs']:
            score += 0.5  # Good organization
        elif top_level_count > self.repo_organization_criteria['max_top_level_dirs'] * 2:
            score -= 1  # Too many directories
        
        # Evaluate total file count
        if repo_structure['file_count'] <= self.repo_organization_criteria['max_file_count'] / 2:
            score += 0.5  # Reasonable file count
        elif repo_structure['file_count'] > self.repo_organization_criteria['max_file_count']:
            score -= 0.5  # Too many files
        
        # Evaluate branch count
        if branch_count >= self.repo_organization_criteria['branch_count'] * 2:
            score += 1  # Excellent branch usage
        elif branch_count >= self.repo_organization_criteria['branch_count']:
            score += 0.5  # Good branch usage
        else:
            score -= 0.5  # Poor branch usage
        
        # Ensure score is within bounds
        return {
            'organization_score': max(0, min(10, score)),
            'branch_count': branch_count,
            **repo_structure
        }
    
    def analyze_repository(self):
        """
        Perform a complete analysis of the repository.
        
        Returns:
            Dictionary with all analysis results
        """
        if not self.is_git_repo:
            return {
                'error': 'Not a valid Git repository'
            }
        
        # Get commit history
        commits = self.get_commit_history()
        
        # Get branches
        branches = self.get_branches()
        
        # Get repository structure
        repo_structure = self.get_repository_structure()
        
        # Analyze commit messages
        message_analysis = self.analyze_commit_messages(commits)
        
        # Analyze commit frequency
        frequency_analysis = self.analyze_commit_frequency(commits)
        
        # Analyze repository organization
        organization_analysis = self.analyze_repository_organization(repo_structure, len(branches))
        
        # Generate reports
        self.generate_commit_report(commits)
        self.generate_graphs(commits, message_analysis, frequency_analysis)
        self.generate_summary_report(message_analysis, frequency_analysis, organization_analysis)
        
        return {
            'commits': commits,
            'branches': branches,
            'repo_structure': repo_structure,
            'message_analysis': message_analysis,
            'frequency_analysis': frequency_analysis,
            'organization_analysis': organization_analysis
        }
    
    def generate_commit_report(self, commits):
        """
        Generate a detailed CSV report of all commits.
        
        Args:
            commits: List of commit data dictionaries
        """
        if not commits:
            return
        
        # Prepare CSV file
        csv_path = os.path.join(self.output_dir, 'commit_details.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Hash', 
                'Author', 
                'Date', 
                'Subject', 
                'Body Length',
                'Files Changed',
                'Insertions',
                'Deletions'
            ])
            
            # Write commit data
            for commit in commits:
                writer.writerow([
                    commit.get('abbreviated_hash', ''),
                    commit.get('author_name', ''),
                    commit.get('author_date', '').split()[0],  # Just the date part
                    commit.get('subject', ''),
                    len(commit.get('body', '')),
                    commit.get('stats', {}).get('files_changed', 0),
                    commit.get('stats', {}).get('insertions', 0),
                    commit.get('stats', {}).get('deletions', 0)
                ])
        
        print(f"Commit report saved to {csv_path}")
    
    def generate_graphs(self, commits, message_analysis, frequency_analysis):
        """
        Generate visual graphs of repository metrics.
        
        Args:
            commits: List of commit data dictionaries
            message_analysis: Results of commit message analysis
            frequency_analysis: Results of commit frequency analysis
        """
        if not commits:
            return
        
        # Set up the plot style
        plt.style.use('ggplot')
        
        # Create figure for commit frequency over time
        plt.figure(figsize=(12, 6))
        
        # Convert commits per day to pandas Series for easier plotting
        dates = []
        counts = []
        
        for date, count in sorted(frequency_analysis.get('commits_per_day', {}).items()):
            dates.append(date)
            counts.append(count)
        
        if dates and counts:
            plt.bar(dates, counts, color='royalblue')
            plt.title('Commit Frequency Over Time')
            plt.xlabel('Date')
            plt.ylabel('Number of Commits')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save the plot
            frequency_plot_path = os.path.join(self.output_dir, 'commit_frequency.png')
            plt.savefig(frequency_plot_path)
            plt.close()
            
            print(f"Commit frequency graph saved to {frequency_plot_path}")
        
        # Create figure for commit message quality breakdown
        quality_breakdown = message_analysis.get('quality_breakdown', {})
        
        if quality_breakdown:
            plt.figure(figsize=(10, 6))
            labels = list(quality_breakdown.keys())
            values = list(quality_breakdown.values())
            
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=['#4CAF50', '#8BC34A', '#FFC107', '#FF5722'])
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Commit Message Quality Distribution')
            
            # Save the plot
            quality_plot_path = os.path.join(self.output_dir, 'message_quality.png')
            plt.savefig(quality_plot_path)
            plt.close()
            
            print(f"Message quality graph saved to {quality_plot_path}")
        
        # Create figure for commit distribution by author
        commits_per_author = frequency_analysis.get('commits_per_author', {})
        
        if commits_per_author:
            plt.figure(figsize=(10, 6))
            
            # Sort by number of commits
            authors = []
            commit_counts = []
            
            for author, count in sorted(commits_per_author.items(), key=lambda x: x[1], reverse=True):
                authors.append(author)
                commit_counts.append(count)
            
            # Limit to top 10 contributors for readability
            if len(authors) > 10:
                other_count = sum(commit_counts[10:])
                authors = authors[:10] + ['Others']
                commit_counts = commit_counts[:10] + [other_count]
            
            plt.bar(authors, commit_counts, color='teal')
            plt.title('Commits by Author')
            plt.xlabel('Author')
            plt.ylabel('Number of Commits')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save the plot
            author_plot_path = os.path.join(self.output_dir, 'commits_by_author.png')
            plt.savefig(author_plot_path)
            plt.close()
            
            print(f"Commits by author graph saved to {author_plot_path}")
    
            
    def generate_summary_report(self, message_analysis, frequency_analysis, organization_analysis):
        """
        Generate a summary report in Markdown format.
        
        Args:
            message_analysis: Results of commit message analysis
            frequency_analysis: Results of commit frequency analysis
            organization_analysis: Results of repository organization analysis
        """
        summary_path = os.path.join(self.output_dir, 'git_analysis_summary.md')
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Git Repository Analysis Summary\n\n")
            f.write(f"Repository: {os.path.basename(self.repo_path)}\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Calculate overall scores
            message_score = message_analysis.get('quality_score', 0)
            frequency_score = frequency_analysis.get('frequency_score', 0)
            organization_score = organization_analysis.get('organization_score', 0)
            
            # Weight the scores based on rubric importance
            commit_message_weight = 0.4  # 4% of total grade
            commit_frequency_weight = 0.3  # 3% of total grade
            repo_organization_weight = 0.3  # 3% of total grade
            
            weighted_score = (
                message_score * commit_message_weight +
                frequency_score * commit_frequency_weight +
                organization_score * repo_organization_weight
            )
            
            f.write("## Overview\n\n")
            f.write(f"- **Total Commits:** {message_analysis.get('total_commits', 0)}\n")
            f.write(f"- **Unique Contributors:** {len(message_analysis.get('unique_contributors', []))}\n")
            f.write(f"- **Branches:** {organization_analysis.get('branch_count', 0)}\n")
            f.write(f"- **Repository Size:** {organization_analysis.get('file_count', 0)} files in {organization_analysis.get('directory_count', 0)} directories\n\n")
            
            # Overall scores section
            f.write("## Overall Scores\n\n")
            f.write("| Category | Score | Quality Level |\n")
            f.write("|----------|-------|---------------|\n")
            f.write(f"| Commit Message Quality | {message_score:.2f}/10 | {self._score_to_level(message_score)} |\n")
            f.write(f"| Commit Frequency | {frequency_score:.2f}/10 | {self._score_to_level(frequency_score)} |\n")
            f.write(f"| Repository Organization | {organization_score:.2f}/10 | {self._score_to_level(organization_score)} |\n")
            f.write(f"| **Overall Version Control** | **{weighted_score:.2f}/10** | **{self._score_to_level(weighted_score)}** |\n\n")
            
            # Rubric assessment section
            f.write("## Rubric Assessment\n\n")
            
            # Map scores to rubric performance levels
            # For commit frequency
            cf_performance, cf_points = self._map_to_rubric(frequency_score, 3)
            f.write("### Commit Frequency and Distribution (3%)\n\n")
            f.write(f"**Performance Level:** {cf_performance}\n\n")
            f.write(f"**Points:** {cf_points}/3\n\n")
            
            # Add observations about commit frequency
            f.write("**Observations:**\n\n")
            commits_per_week = frequency_analysis.get('commits_per_week', 0)
            largest_gap = frequency_analysis.get('largest_gap', 0)
            project_duration = frequency_analysis.get('project_duration', 0)
            days_with_commits = frequency_analysis.get('days_with_commits', 0)
            commit_day_ratio = frequency_analysis.get('commit_day_ratio', 0)
            max_commits_in_day = frequency_analysis.get('max_commits_in_day', 0)
            commit_burst_ratio = frequency_analysis.get('commit_burst_ratio', 0)
            total_commits = message_analysis.get('total_commits', 0)
            
            f.write(f"- Project duration: {project_duration} days\n")
            f.write(f"- Days with at least one commit: {days_with_commits} days ({commit_day_ratio*100:.1f}% of analyzed period)\n")
            f.write(f"- Average commits per week: {commits_per_week:.2f}\n")
            f.write(f"- Largest gap between commits: {largest_gap} days\n")
            f.write(f"- Maximum commits in a single day: {max_commits_in_day} ({commit_burst_ratio*100:.1f}% of all commits)\n\n")
            
            # Warning signs and improvement recommendations
            f.write("**Assessment:**\n\n")
            
            if project_duration <= 1:
                f.write("- **CRITICAL ISSUE**: All commits were made on a single day. This indicates a last-minute approach rather than an iterative development process.\n")
            elif commit_day_ratio < 0.2:
                f.write(f"- **MAJOR ISSUE**: Commits occurred on only {days_with_commits} days out of {project_duration} days ({commit_day_ratio*100:.1f}%). This indicates a very sporadic development pattern.\n")
            
            if commit_burst_ratio > 0.5:
                f.write(f"- **MAJOR ISSUE**: {max_commits_in_day} commits ({commit_burst_ratio*100:.1f}% of total) were made in a single day, suggesting a 'commit burst' rather than regular development.\n")
            
            if commits_per_week < 3:
                f.write(f"- **ISSUE**: Commit frequency of {commits_per_week:.2f} per week is below the recommended minimum of 3 commits per week.\n")
            
            if largest_gap > 7:
                f.write(f"- **ISSUE**: Maximum gap between commits ({largest_gap} days) exceeds the recommended maximum of 7 days.\n")
            
            if days_with_commits / max(1, project_duration) >= 0.4 and commits_per_week >= 3:
                f.write("- **POSITIVE**: Regular commit pattern observed with consistent activity across the development period.\n")
            
            if 0.1 <= commit_burst_ratio <= 0.3 and commit_day_ratio >= 0.3:
                f.write("- **POSITIVE**: Balanced distribution of commits with no excessive concentration on a single day.\n")
            
            f.write("\n**Rubric criteria:**\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Optimal commit frequency with logical development progression | 2.25-3 |\n")
            f.write("| Credit (65-74%) | Regular commits throughout development process | 1.95-2.24 |\n")
            f.write("| Pass (50-64%) | Infrequent commits with uneven distribution | 1.5-1.94 |\n")
            f.write("| Fail (0-49%) | Very few commits or poor distribution | 0-1.49 |\n\n")
            
            # For commit messages
            cm_performance, cm_points = self._map_to_rubric(message_score, 4)
            f.write("### Quality of Commit Messages (4%)\n\n")
            f.write(f"**Performance Level:** {cm_performance}\n\n")
            f.write(f"**Points:** {cm_points}/4\n\n")
            
            # Add observations about commit messages
            f.write("**Observations:**\n\n")
            quality_breakdown = message_analysis.get('quality_breakdown', {})
            avg_msg_length = message_analysis.get('average_length', 0)
            
            f.write(f"- Average commit message length: {avg_msg_length:.1f} characters\n")
            f.write("- Message quality breakdown:\n")
            for quality, count in quality_breakdown.items():
                percentage = (count / message_analysis.get('total_commits', 1)) * 100
                f.write(f"  - {quality.capitalize()}: {count} ({percentage:.1f}%)\n")
            
            top_words = message_analysis.get('top_words', [])
            if top_words:
                f.write("\n- Most common descriptive words in commit messages:\n")
                for word, count in top_words[:5]:
                    f.write(f"  - '{word}': used {count} times\n")
            
            f.write("\n**Assessment:**\n\n")
            
            if quality_breakdown.get('excellent', 0) / max(1, total_commits) >= 0.7:
                f.write("- **POSITIVE**: Majority of commit messages are excellent, showing detailed descriptions of changes.\n")
            
            if quality_breakdown.get('poor', 0) > 0:
                poor_percentage = quality_breakdown.get('poor', 0) / max(1, total_commits) * 100
                f.write(f"- **ISSUE**: {poor_percentage:.1f}% of commit messages are poor quality, lacking descriptive content.\n")
            
            if avg_msg_length < 10:
                f.write("- **ISSUE**: Average commit message length is too short. Messages should be descriptive of the changes.\n")
            elif avg_msg_length > 100:
                f.write("- **POSITIVE**: Commit messages are detailed with good explanations of changes.\n")
            
            f.write("\n**Rubric criteria:**\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Comprehensive, well-structured messages following best practices | 3-4 |\n")
            f.write("| Credit (65-74%) | Clear, consistent messages describing changes | 2.6-2.99 |\n")
            f.write("| Pass (50-64%) | Basic descriptive messages | 2-2.59 |\n")
            f.write("| Fail (0-49%) | Vague or unhelpful commit messages | 0-1.99 |\n\n")
            
            # For repository organization
            ro_performance, ro_points = self._map_to_rubric(organization_score, 3)
            f.write("### Repository Organisation (3%)\n\n")
            f.write(f"**Performance Level:** {ro_performance}\n\n")
            f.write(f"**Points:** {ro_points}/3\n\n")
            
            # Add observations about repository organization
            f.write("**Observations:**\n\n")
            f.write(f"- README exists: {'Yes' if organization_analysis.get('readme_exists', False) else 'No'}\n")
            f.write(f"- .gitignore exists: {'Yes' if organization_analysis.get('gitignore_exists', False) else 'No'}\n")
            f.write(f"- Number of branches: {organization_analysis.get('branch_count', 0)}\n")
            f.write(f"- Number of top-level directories: {len(organization_analysis.get('top_level_directories', []))}\n")
            f.write(f"- Top-level directories: {', '.join(organization_analysis.get('top_level_directories', []))}\n\n")
            
            f.write("**Assessment:**\n\n")
            
            if not organization_analysis.get('readme_exists', False):
                f.write("- **ISSUE**: README file is missing. A README is essential for explaining the project purpose and setup.\n")
            else:
                f.write("- **POSITIVE**: Repository includes a README file.\n")
            
            if not organization_analysis.get('gitignore_exists', False):
                f.write("- **ISSUE**: .gitignore file is missing. A .gitignore helps prevent unwanted files from being committed.\n")
            else:
                f.write("- **POSITIVE**: Repository includes a .gitignore file.\n")
            
            branch_count = organization_analysis.get('branch_count', 0)
            if branch_count < 2:
                f.write("- **ISSUE**: Repository uses only one branch. Multiple branches (e.g., main/development) are recommended.\n")
            elif branch_count >= 3:
                f.write(f"- **POSITIVE**: Repository utilizes {branch_count} branches, indicating a good branching strategy.\n")
            else:
                f.write("- **POSITIVE**: Repository uses multiple branches.\n")
            
            f.write("\n**Rubric criteria:**\n\n")
            f.write("| Performance Level | Description | Points |\n")
            f.write("|-------------------|-------------|--------|\n")
            f.write("| Distinction (75-100%) | Professional-level organisation with optimal structure and branch strategy | 2.25-3 |\n")
            f.write("| Credit (65-74%) | Well-organised with logical file structure | 1.95-2.24 |\n")
            f.write("| Pass (50-64%) | Basic organisation with standard structure | 1.5-1.94 |\n")
            f.write("| Fail (0-49%) | Poor repository organisation | 0-1.49 |\n\n")
            
            # Total version control score
            total_points = cf_points + cm_points + ro_points
            total_percentage = (total_points / 10) * 100
            f.write("### Total Version Control Score\n\n")
            f.write(f"**Total Points:** {total_points:.2f}/10 ({total_percentage:.1f}%)\n\n")
            
            # Performance level
            overall_performance = "Fail (0-49%)"
            if total_percentage >= 75:
                overall_performance = "Distinction (75-100%)"
            elif total_percentage >= 65:
                overall_performance = "Credit (65-74%)"
            elif total_percentage >= 50:
                overall_performance = "Pass (50-64%)"
            
            f.write(f"**Overall Performance Level:** {overall_performance}\n\n")
            
            # Recommendations for improvement
            f.write("## Recommendations for Improvement\n\n")
            
            if frequency_score < 5:
                f.write("### Commit Frequency and Distribution\n\n")
                f.write("1. **Commit regularly** throughout the development process, not just at the end.\n")
                f.write("2. **Aim for at least 3-4 commits per week** during active development.\n")
                f.write("3. **Make smaller, focused commits** rather than large batches of changes.\n")
                f.write("4. **Avoid gaps** of more than a week between commits.\n\n")
            
            if message_score < 7:
                f.write("### Commit Message Quality\n\n")
                f.write("1. **Write descriptive commit messages** that explain what changes were made and why.\n")
                f.write("2. **Follow the format**: Short title (50-72 characters) + detailed body when needed.\n")
                f.write("3. **Use imperative mood** for commit titles (e.g., \"Add feature\" not \"Added feature\").\n")
                f.write("4. **Reference issue numbers** where applicable.\n\n")
            
            if organization_score < 7:
                f.write("### Repository Organization\n\n")
                f.write("1. **Create a comprehensive README** explaining the project purpose, setup, and usage.\n")
                f.write("2. **Add a .gitignore file** to exclude unwanted files (compiled code, dependencies, etc.).\n")
                f.write("3. **Use a branching strategy**: At minimum, maintain separate main and development branches.\n")
                f.write("4. **Organize files logically** with a clear directory structure.\n\n")
            
            f.write("## Academic Integrity Statement\n\n")
            f.write("This report is automatically generated based on Git history analysis and provides an objective assessment of version control practices. Scores are mapped to rubric criteria as defined in the assignment specification.\n")
        
        print(f"Summary report saved to {summary_path}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a Git repository for quality metrics.")
    parser.add_argument("repo_path", help="Path to the Git repository to analyze")
    parser.add_argument("--output", required=False, default="git_analysis_reports", 
                      help="Directory to save analysis reports")
    args = parser.parse_args()
    
    # Create analyzer instance
    analyzer = GitRepoAnalyzer(args.repo_path, args.output)
    
    # Run the analysis
    analysis_results = analyzer.analyze_repository()
    
    # Print basic info to stdout for command-line feedback
    if 'error' in analysis_results:
        print(f"Error analyzing repository: {analysis_results['error']}")
    else:
        print(f"\nGit Repository Analysis Summary")
        print(f"Repository: {os.path.basename(args.repo_path)}")
        
        message_analysis = analysis_results.get('message_analysis', {})
        frequency_analysis = analysis_results.get('frequency_analysis', {})
        organization_analysis = analysis_results.get('organization_analysis', {})
        
        print(f"\nTotal Commits: {message_analysis.get('total_commits', 0)}")
        print(f"Unique Contributors: {len(message_analysis.get('unique_contributors', []))}")
        print(f"Branches: {len(analysis_results.get('branches', []))}")
        
        # Calculate overall scores based on rubric criteria
        message_score = message_analysis.get('quality_score', 0)
        frequency_score = frequency_analysis.get('frequency_score', 0)
        organization_score = organization_analysis.get('organization_score', 0)
        
        # Weight the scores based on the assignment rubric
        # Version Control (10%): Commit frequency (3%), Commit messages (4%), Repo organization (3%)
        commit_message_weight = 0.4  # 40% of version control score (4% of total)
        commit_frequency_weight = 0.3  # 30% of version control score (3% of total)
        repo_organization_weight = 0.3  # 30% of version control score (3% of total)
        
        weighted_score = (
            message_score * commit_message_weight +
            frequency_score * commit_frequency_weight +
            organization_score * repo_organization_weight
        )
        
        # Map to performance levels
        performance_level = "Fail (0-49%)"
        if weighted_score >= 7.5:
            performance_level = "Distinction (75-100%)"
        elif weighted_score >= 6.5:
            performance_level = "Credit (65-74%)"
        elif weighted_score >= 5.0:
            performance_level = "Pass (50-64%)"
        
        # Calculate percentage
        percentage = (weighted_score / 10) * 100
        
        print(f"\nScores (0-10 scale):")
        print(f"Commit Message Quality: {message_score:.2f}")
        print(f"Commit Frequency: {frequency_score:.2f}")
        print(f"Repository Organization: {organization_score:.2f}")
        print(f"Overall Version Control Score: {weighted_score:.2f}/10 ({percentage:.1f}%)")
        print(f"Performance Level: {performance_level}")
        
        # Points based on total weight (10% of assignment)
        points = weighted_score
        print(f"Points: {points:.2f}/10 ({percentage:.1f}%)")
        
        print(f"\nDetailed reports saved to: {args.output}/")
        
        # Additional version control metrics specifically for assignment requirements
        commits_per_week = frequency_analysis.get('commits_per_week', 0)
        largest_gap = frequency_analysis.get('largest_gap', 0)
        
        print("\nKey Version Control Metrics:")
        print(f"Commits per Week: {commits_per_week:.2f}")
        print(f"Largest Gap Between Commits (days): {largest_gap}")
        
        # Commit message quality breakdown
        quality_breakdown = message_analysis.get('quality_breakdown', {})
        print("\nCommit Message Quality Distribution:")
        for quality, count in quality_breakdown.items():
            percentage = (count / message_analysis.get('total_commits', 1)) * 100
            print(f"- {quality.capitalize()}: {count} ({percentage:.1f}%)")
