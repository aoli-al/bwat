from github import Github
from github import Auth

from openai import OpenAI
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam
import os


class Analyzer:
    def __init__(self, repo: str) -> None:
        self.repo_name = repo
        self.g = Github(auth=Auth.Token(os.environ["GITHUB_TOKEN"]))
        self.openai = OpenAI(base_url="https://app.qusic.me/openai/v1", api_key=os.environ["OPENAI_TOKEN"])
        self.repo = self.g.get_repo(self.repo_name)


    def get_issues(self):
        issues = self.repo.get_issues(labels=["bug"])
        for issue in issues:
            self.get_completion(issue.title, issue.body)
            break

    def get_completion(self, title: str, content: str):
        messages = [
            {"content": "Please read the following bug report and classify which type of bug the developer has encountered.", "role": "system"},
            {"content": f"title: {title}; content: {content}", "role": "user"}
        ]
        response = self.openai.chat.completions.create(messages=messages, model="gpt-4-turbo-preview")
        print(response)


api = Analyzer("apache/arrow-datafusion")
api.get_issues()