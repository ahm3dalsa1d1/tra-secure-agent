# mcp_client.py

import asyncio
import sys

from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _get_company_from_mcp(search_term: str) -> dict | None:

    server_path = Path(__file__).with_name("mcp_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(server_path.parent)
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # MCP handshake
            await session.initialize()

            # Call our MCP tool
            result = await session.call_tool(
                "get_company",
                arguments={
                    "search_term": search_term
                }
            )

            if result.isError:
                error_text = " ".join(
                    getattr(item, "text", "")
                    for item in result.content
                )

                raise RuntimeError(
                    error_text or "MCP tool failed."
                )

            data = result.structuredContent

            if data is None:
                return None

            return data


def get_company_from_mcp(search_term: str) -> dict | None:
    return asyncio.run(
        _get_company_from_mcp(search_term)
    )


# Temporary direct test
if __name__ == "__main__":
    search = input("CR number or company name: ")

    result = get_company_from_mcp(search)

    print(result)