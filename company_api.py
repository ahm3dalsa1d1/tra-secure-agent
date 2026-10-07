import os
import requests

from dotenv import load_dotenv


load_dotenv()


TRA_API_URL = os.getenv("TRA_API_URL")


def fetch_companies() -> list[dict]:
    response = requests.get(
        TRA_API_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def find_company(search_term: str) -> dict | None:
    companies = fetch_companies()

    search_term = search_term.strip().casefold()

    # First try exact CR number
    for company in companies:
        cr_number = str(company.get("crNo", ""))

        if cr_number.casefold() == search_term:
            return company

    # Then try company name
    for company in companies:
        name_en = str(company.get("CompanyNameEn", ""))
        name_ar = str(company.get("CompanyNameAr", ""))

        if (
            search_term in name_en.casefold()
            or search_term in name_ar.casefold()
        ):
            return company

    return None