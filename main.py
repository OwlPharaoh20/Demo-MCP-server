# Import the necessary libraries
from mcp.server.fastmcp import FastMCP  # Import the FastMCP class from the mcp library
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv library
import httpx  # Import the httpx library for making HTTP requests
import json  # Import the json library for working with JSON data
import os  # Import the os library for working with environment variables
from bs4 import BeautifulSoup  # Import the BeautifulSoup library for parsing HTML

# Load environment variables from a .env file
load_dotenv()

# Create an instance of the FastMCP class, passing in the name of the tool
mcp = FastMCP("docs")

# Define a constant for the user agent string
USER_AGENT = "docs-app/1.0"

# Define a constant for the URL of the search API
SERPER_URL = "https://google.serper.dev/search"

# Define a dictionary that maps library names to their corresponding documentation URLs
docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

# Define an asynchronous function that searches the web for a given query
async def search_web(query: str) -> dict | None:
    # Create a JSON payload with the query and the number of results to return
    payload = json.dumps({"q": query, "num": 2})

    # Define headers for the HTTP request, including the API key and content type
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),  # Get the API key from an environment variable
        "Content-Type": "application/json",
    }

    # Create an asynchronous HTTP client
    async with httpx.AsyncClient() as client:
        try:
            # Make a POST request to the search API with the payload and headers
            response = await client.post(SERPER_URL, headers=headers, data=payload, timeout=30.0)
            # Raise an exception if the response was not successful
            response.raise_for_status()
            # Return the JSON response
            return response.json()
        except httpx.TimeoutException:
            # Return an empty list if the request timed out
            return {"organic": []}

# Define an asynchronous function that fetches the content of a URL
async def fetch_url(url: str):
    # Create an asynchronous HTTP client
    async with httpx.AsyncClient() as client:
        try:
            # Make a GET request to the URL with a timeout
            response = await client.get(url, timeout=30.0)
            # Parse the HTML response using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            # Get the text content of the HTML
            text = soup.get_text()
            # Return the text content
            return text
        except httpx.TimeoutException:
            # Return an error message if the request timed out
            return "Timeout error"

# Define a tool function that searches the documentation for a given query and library
@mcp.tool()
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.
    Supports langchain, openai, and llama-index.

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
    """
    # Check if the library is supported
    if library not in docs_urls:
        raise ValueError(f"Library {library} not supported by this tool")

    # Construct a query that searches the documentation for the given library
    query = f"site:{docs_urls[library]} {query}"
    # Search the web for the query
    results = await search_web(query)
    # Check if any results were found
    if len(results["organic"]) == 0:
        return "No results found"

    # Initialize an empty string to store the text content
    text = ""
    # Iterate over the search results
    for result in results["organic"]:
        # Fetch the content of the result URL
        text += await fetch_url(result["link"])
    # Return the text content
    return text

# Run the MCP server if this script is executed directly
if __name__ == "__main__":
    mcp.run(transport="stdio")