#!/usr/bin/env python3
"""
file: github_rest.py

description: 封装 github restful api client
author: 张翼
date: 2022-10-10 20:21:00

Copyright 2021 AutraTech. All Rights Reserved.
"""

import argparse
import subprocess
import webbrowser
import platform

from github_rest import Client

# Linux or Mac
CHROME_PATH = "/usr/bin/google-chrome %s" if platform.system() == "Linux" \
    else "open -a /Applications/Google\\ Chrome.app %s"


def _get_latest_commit_sha() -> str:
    return subprocess.check_output(["git", "rev-parse",
                                    "HEAD"]).decode("ascii").strip()


# Set index to 0 will get HEAD.
def _get_commit_sha(index: int) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD~" + str(index)
                                    ]).decode("ascii").strip()


def _get_current_branch_name() -> str:
    return subprocess.check_output(["git", "branch",
                                    "--show-current"]).decode("ascii").strip()


def _get_base_commit_sha(base_branch="origin/master") -> str:
    return subprocess.check_output(["git", "merge-base", base_branch,
                                    "HEAD"]).decode("ascii").strip()


# Get diff file list between current branch and base branch.
def _get_diff_files(base_commit_sha, args):
    return subprocess.check_output(
        ["git", "diff", base_commit_sha, "--name-only"] +
        args).decode("ascii").strip().split("\n")


def _get_modified_files(base_commit_sha):
    return _get_diff_files(base_commit_sha, args=["--diff-filter=ACM"])


def _mark_unit_test_success(client: Client, commit_sha):
    client.mark_status_success(
        commit_sha=commit_sha,
        status_name="unit-test",
        description="Unit test passed.",
    )


def _push_branch():
    branch_name = _get_current_branch_name()
    subprocess.check_output(
        ["git", "push", "-f", "--set-upstream", "origin", branch_name])


def push_and_create_pr(repos_name: str, browser: bool, mark_ut_success: bool,
                       mark_format_check_success: bool) -> None:
    """ main course: push and create pr """
    client = Client(repos_name)
    _push_branch()
    commit_sha = _get_latest_commit_sha()
    current_branch_name = _get_current_branch_name()
    pull_request = client.get_pull_request(branch_name=current_branch_name)
    # Pass unit test
    if mark_ut_success:
        _mark_unit_test_success(client, commit_sha)
    if mark_format_check_success:
        client.mark_status_success(
            commit_sha=commit_sha,
            status_name="format-check",
            description="Format check passed.",
        )
    # Find a PR associated with branch name
    if pull_request:
        pr_link = pull_request["_links"]["html"]["href"]
        print(
            f"Pull request is already created for branch: {current_branch_name}, PR link: {pr_link}"
        )
        print("Push latest change to PR successfully")
    else:
        response = client.create_pr(current_branch_name, "master")
        client.check_response(response=response, is_fatal=False)
        pr_link = response.json()["html_url"]
        print(f"Push and create pr successfully, PR link: {pr_link}")
    # open browser
    if browser:
        webbrowser.get(CHROME_PATH).open(pr_link)


def main():
    """ main entry of this program """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos-name",
                        type=str,
                        help="Remote repository name, eg. autra_core.")
    parser.add_argument("--command",
                        choices=["publish"],
                        type=str,
                        help="Push change and create pr.")
    parser.add_argument("--browser",
                        choices=[0, 1],
                        help="Open PR in browser or not.",
                        type=int,
                        default=0)
    parser.add_argument("--mark-ut-success",
                        choices=[0, 1],
                        help="Whether to mark unit test success.",
                        type=int,
                        default=0)
    parser.add_argument("--mark-format-check-success",
                        choices=[0, 1],
                        help="Whether to mark format check success.",
                        type=int,
                        default=0)
    args = parser.parse_args()

    if args.command == "publish":
        push_and_create_pr(
            repos_name=args.repos_name,
            browser=args.browser,
            mark_ut_success=args.mark_ut_success,
            mark_format_check_success=args.mark_format_check_success,
        )


if __name__ == "__main__":
    main()
