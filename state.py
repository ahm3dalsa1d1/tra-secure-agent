from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    question: str

    sensitive: bool
    search_term: str

    username: str
    password: str

    authenticated: bool
    authorized: bool

    company_data: Optional[dict]

    answer: str