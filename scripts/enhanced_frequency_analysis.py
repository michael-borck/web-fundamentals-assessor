# Enhanced analyze_commit_frequency method with more detailed analysis

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
