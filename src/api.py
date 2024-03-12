from github import Github
from github import Auth

from langchain_community.chat_models import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import create_tagging_chain_pydantic
from datetime import datetime
import requests
import time
import os


class Tags(BaseModel):
    difficulty: int = Field(
        ...,
        description="Describe the difficulty for debugging this issue, the higher the number the more difficult.",
        enum=[1, 2, 3, 4, 5],
    )
    characteristics:str = Field(
        ...,
        description="Pick the most relevant characteristic that makes this issue hard to debug.",
        enum= [
            "Reproducibility",
            "Intermittent issue",
            "Concurrency",
            "Environment Differences",
            "Third-party Libraries and APIs",
            "Others",
        ]
    )
    reason: str = Field(
        ...,
        description="Describe the reason you pick this characteristic.",
    )


class Analyzer:
    def __init__(self, repo: str) -> None:
        self.owner, self.name = repo.split("/")
        self.llm = ChatOpenAI(
            base_url="https://app.qusic.me/openai/v1",
            api_key=os.environ["OPENAI_TOKEN"],
            temperature=0,
        )

    def get_issues(self):
        headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
        result = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": open("./request.graphql").read(),
                "variables": {"owner": self.owner, "name": self.name},
            },
            headers=headers,
            timeout=10
        )
        if result.status_code == 200:
            result = result.json()
            for issue in result['data']['repository']['issues']['nodes']:
                closed_at = datetime.strptime(issue["closedAt"], "%Y-%m-%dT%H:%M:%SZ")
                created_at = datetime.strptime(issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
                duration = closed_at - created_at
                for timeline in issue['timelineItems']['nodes']:
                    if "closer" in timeline and timeline['closer']:
                        print(duration)
                        print(issue['url'])

        # self.get_completion(issue.title, issue.body, issue.html_url)

    def get_completion(self, title: str, content: str, url: str):
        template = """The following text represents a GitHub bug report taken from the issue trackers of a large database application, delimited by `$$$`.
        Based on this bug report, could you assign a difficulty level (1-5) for debugging this bug? Additionally, for the reason behind your assigned difficulty level,
        please identify three key words that describe the characteristics making this bug challenging to debug.
        $$$
        title: {title}
        content: {content}
        $$$
        """
        # prompt = ChatPromptTemplate.from_template(template)
        # output_parser = StrOutputParser()
        # chain = prompt | model | output_parser
        # result = chain.invoke({"title": title, "content": content})
        chain = create_tagging_chain_pydantic(Tags, self.llm)
        result = chain.run(content)

        print("====================================================")
        print(url)
        print(result)
        print("----------------------------------------------------")


api = Analyzer("apache/arrow-datafusion")
api.get_issues()
