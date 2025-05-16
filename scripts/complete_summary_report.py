# Updated generate_summary_report to include additional commit pattern analysis

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
