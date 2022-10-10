#!/usr/bin/env python3
"""
file: github_rest.py

description: 封装 github restful api client
author: 张翼
date: 2022-10-10 20:21:00

Copyright 2021 AutraTech. All Rights Reserved.
"""

import os
import requests

API_URL = "https://api.github.com"
GITHUB_TOKEN_PATH = os.environ["HOME"] + "/.AUTRA_GITHUB_TOKEN"


class Client:
    """ Github Restful API client"""

    def __init__(self, repos_name: str):
        self._repos_name = repos_name
        self._token = self._get_token()
        self._session = requests.sessions.Session()
        self._session.headers.update({"Authorization": f"token {self._token}"})

    def check_response(self, response, is_fatal=True):
        """ check API response """
        success_code = {200, 201}
        if response.status_code not in success_code:
            print("#####################################################")
            print(f"Failed, response code: {response.status_code}")
            print(response.text)
            print("#####################################################")
            if is_fatal:
                raise Exception

    def _get_token(self):
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token

        if os.path.exists(GITHUB_TOKEN_PATH):
            with open(GITHUB_TOKEN_PATH, "r", encoding="utf-8") as fin:
                return fin.read().strip()

        print(
            "You didn't register github token, please apply a github token following guide: "
            "https://bg4kuaip34.feishu.cn/wiki/wikcnb4NDFlJOCLVgSLe9bBgyqC")
        token = input("Enter token: ")
        response = requests.get(url=f"{API_URL}/repos/{self._repos_name}",
                                headers={"Authorization": f"token {token}"},
                                timeout=1)
        self.check_response(response)
        with open(GITHUB_TOKEN_PATH, "w", encoding="utf-8") as fout:
            fout.write(token)
        print("Github token is saved sucessfully.")
        return token

    def _get_url(self, api_name, suffix):
        return f"{API_URL}/{api_name}/{self._repos_name}/{suffix}"

    def _mark_status(self,
                     commit_sha,
                     context,
                     state,
                     description,
                     target_url=None):
        body = {
            "context": context,
            "state": state,
            "description": description,
        }
        if target_url:
            body["target_url"] = target_url
        return self._session.post(url=self._get_url("repos",
                                                    f"statuses/{commit_sha}"),
                                  json=body)

    def mark_status_success(self,
                            commit_sha,
                            status_name,
                            description,
                            check_res=True,
                            target_url=None):
        """ mark git status as success """
        response = self._mark_status(commit_sha, status_name, "success",
                                     description, target_url)
        if check_res:
            self.check_response(response)
        return response

    def mark_status_failure(self,
                            commit_sha,
                            status_name,
                            description,
                            check_res=True,
                            target_url=None):
        """ mark git status as failure """
        response = self._mark_status(commit_sha, status_name, "failure",
                                     description, target_url)
        if check_res:
            self.check_response(response)
        return response

    def create_pr(self, head_branch, base_branch):
        """ create pull request """
        with open(os.path.join(os.path.dirname(__file__),
                               "pull_request_content_template"),
                  encoding="utf-8") as fin:
            content_template = fin.read()
            body = {
                "title": head_branch,
                "head": head_branch,
                "base": base_branch,
                "body": content_template
            }
            return self._session.post(url=self._get_url("repos", "pulls"),
                                      json=body)

    def get_pull_request(self, branch_name: str):
        """ get pull request """
        # List all open pull requests
        response = requests.get(
            url=f"{API_URL}/repos/{self._repos_name}/pulls?state=open",
            headers={"Authorization": f"token {self._token}"},
            timeout=1)
        data = response.json()
        # Match branch_name with head"s ref
        for pull_request in data:
            if not isinstance(pull_request, dict):
                continue
            pull_request_head_ref = pull_request["head"]["ref"]
            if pull_request_head_ref == branch_name:
                return pull_request
        return None

    def get_approved_reviewers(self, pull_numbers):
        """ get approved reviewers """
        response = requests.get(
            url=
            f"{API_URL}/repos/{self._repos_name}/pulls/{pull_numbers}/reviews?per_page={100}",
            headers={"Authorization": f"token {self._token}"},
            timeout=1)
        data = response.json()
        approved_reviewers = []
        for reviewer in data:
            if reviewer["state"] == "APPROVED":
                approved_reviewers.append(reviewer["user"]["login"])
        return approved_reviewers
