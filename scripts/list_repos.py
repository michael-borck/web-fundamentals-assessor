import os
import argparse
from github import Github

# Replace with your GitHub Personal Access Token.
# It's recommended to use environment variables for security.
# export GITHUB_TOKEN="your_token_here"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def list_github_repos(exclude_user=None):
    """
    Lists all GitHub repositories the authenticated user has access to,
    optionally excluding repositories owned by a specific user.
    """
    if not GITHUB_TOKEN:
        print("Error: GitHub token not found.")
        print("Please set the GITHUB_TOKEN environment variable.")
        print("For example (Linux/macOS): export GITHUB_TOKEN='your_token_here'")
        print("For example (Windows): set GITHUB_TOKEN=your_token_here")
        return

    try:
        # Authenticate with GitHub using the token
        g = Github(GITHUB_TOKEN)

        # Get the authenticated user
        user = g.get_user()

        print(f"Listing repositories for user: {user.login}")
        if exclude_user:
            print(f"(Excluding repositories owned by: {exclude_user})")
        print("-" * 30)

        # Get the repositories the user has access to
        repositories = user.get_repos()

        found_repos_count = 0
        excluded_repos_count = 0

        if repositories.totalCount == 0:
            print("No repositories found.")
        else:
            print(f"Found {repositories.totalCount} total accessible repositories.")
            print("Listing allowed repositories:")

            for repo in repositories:
                if exclude_user and repo.owner.login.lower() == exclude_user.lower():
                    excluded_repos_count += 1
                    continue # Skip this repository if it's owned by the excluded user

                found_repos_count += 1
                print(f"- {repo.full_name} (Private: {repo.private})")

        print("-" * 30)
        print(f"Listed {found_repos_count} repositories.")
        if exclude_user:
            print(f"Excluded {excluded_repos_count} repositories owned by {exclude_user}.")


    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your GitHub token and its permissions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List all GitHub repositories you have access to.')
    parser.add_argument(
        '-e', '--exclude-user',
        type=str,
        help='Specify a GitHub username whose repositories should be excluded from the list.'
    )

    args = parser.parse_args()

    list_github_repos(exclude_user=args.exclude_user)

