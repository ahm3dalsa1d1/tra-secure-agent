from typing import TypedDict

from mcp.server.fastmcp import FastMCP

from company_api import find_company


mcp = FastMCP("Company Server")


class CompanyResult(TypedDict):
    found: bool
    name_en: str | None
    name_ar: str | None
    cr_number: str | None


@mcp.tool()
def get_company(search_term: str) -> CompanyResult:
    """
    Find a company using its CR number,
    English name, or Arabic name.
    """

    company = find_company(search_term)

    if company is None:
        return {
            "found": False,
            "name_en": None,
            "name_ar": None,
            "cr_number": None
        }

    return {
        "found": True,
        "name_en": company.get("CompanyNameEn"),
        "name_ar": company.get("CompanyNameAr"),
        "cr_number": str(company.get("crNo"))
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")