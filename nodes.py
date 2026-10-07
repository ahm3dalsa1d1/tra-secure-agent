import os

from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from mcp_client import get_company_from_mcp
from state import AgentState


load_dotenv()


# ---------------------------------------------------------
# LLM setup
# ---------------------------------------------------------

llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


# ---------------------------------------------------------
# Structured output model
# ---------------------------------------------------------

class RequestClassification(BaseModel):
    sensitive: bool
    search_term: str | None = None

classifier_llm = llm.with_structured_output(RequestClassification)


# ---------------------------------------------------------
# 1. Classify request
# ---------------------------------------------------------

def classify_request(state: AgentState):
    question = state["question"]

    prompt = f"""
You are a request classifier.

Determine whether the user's request is asking for protected
company information.

Protected requests include:
- Looking up a company by CR number
- Looking up a company's CR number
- Looking up a specific company

If the request is protected, extract the company name or CR number
into search_term.

If the request is general, search_term should be null.

Examples:

User:
"What is a CR number?"

sensitive = false
search_term = null


User:
"Give me the company with CR number 123456"

sensitive = true
search_term = "123456"


User:
"Find Oman Telecommunications Company"

sensitive = true
search_term = "Oman Telecommunications Company"


User question:
{question}
"""

    result = classifier_llm.invoke(prompt)

    return {
        "sensitive": result.sensitive,
        "search_term": result.search_term
    }

# ---------------------------------------------------------
# 2. General question
# ---------------------------------------------------------

def answer_general(state: AgentState):
    question = state["question"]

    response = llm.invoke(
        f"""
Answer the following user question normally.

Question:
{question}
"""
    )

    return {
        "answer": response.content
    }


# ---------------------------------------------------------
# 3. Authentication
# ---------------------------------------------------------

def authenticate(state: AgentState):
    username = state.get("username")
    password = state.get("password")

    # TEMPORARY test users.
    # We will replace this later with proper authentication.
    users = {
        "ahmed": {
            "password": "1234",
            "authorization_level": 2
        },
        "user": {
            "password": "abcd",
            "authorization_level": 1
        }
    }

    user = users.get(username)

    if user is None:
        return {
            "authenticated": False,
            "authorized": False
        }

    if user["password"] != password:
        return {
            "authenticated": False,
            "authorized": False
        }

    authenticated = True

    # Let's say protected company data needs level 2.
    authorized = user["authorization_level"] >= 2

    return {
        "authenticated": authenticated,
        "authorized": authorized
    }


# ---------------------------------------------------------
# 4. Company lookup
# ---------------------------------------------------------

def company_lookup(state: AgentState):
    search_term = state.get("search_term")

    if not search_term:
        return {
            "company_data": None
        }

    result = get_company_from_mcp(search_term)

    if not result:
        return {
            "company_data": None
        }

    if not result.get("found"):
        return {
            "company_data": None
        }

    return {
        "company_data": result
    }
    # TEMPORARY fake data.
    # Later this is where our MCP client will be used.

    # company = {
    #     "name_en": "Example Company",
    #     "name_ar": "شركة المثال",
    #     "cr_number": "123456"
    # }

    # return {
    #     "company_data": company
    # }


# ---------------------------------------------------------
# 5. Answer using company data
# ---------------------------------------------------------

def answer_company(state: AgentState):
    company = state.get("company_data")

    if company is None:
        return {
            "answer": "No company matching your request was found."
        }

    return {
        "answer": (
            f"Company: {company.get('name_en', 'N/A')}\n"
            f"Arabic Name: {company.get('name_ar', 'N/A')}\n"
            f"CR Number: {company.get('cr_number', 'N/A')}"
        )
    }

# ---------------------------------------------------------
# 6. Access denied
# ---------------------------------------------------------

def access_denied(state: AgentState):
    if not state.get("authenticated"):
        return {
            "answer": "Authentication failed. Please check your username and password."
        }

    return {
        "answer": "You are authenticated, but you are not authorized to access this information."
    }