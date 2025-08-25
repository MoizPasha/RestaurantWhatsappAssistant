import asyncio
from fastmcp import Client

async def main():
    client = Client("main.py")

    async with client:
        # Check connectivity
        await client.ping()

        # List server capabilities
        tools = await client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            if hasattr(tool, 'inputSchema'):
                print(f"Parameters: {tool.inputSchema}")
            print("---")
        resources = await client.list_resources()
        for resource in resources:
            print(f"Resource: {resource.name}")
            print(f"Description: {resource.description}")
            print("---")
        result = await client.call_tool("get_full_menu", {})
        print(result)
if __name__ == "__main__":
    asyncio.run(main())
