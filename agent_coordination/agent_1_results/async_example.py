import asyncio
import time

import aiohttp


async def fetch_data(url, session):
    """Async function to fetch data from a URL"""
    try:
        async with session.get(url) as response:
            data = await response.text()
            return f"Fetched {len(data)} characters from {url}"
    except Exception as e:
        return f"Error fetching {url}: {e}"


async def process_data(data):
    """Simulate async data processing"""
    await asyncio.sleep(1)  # Simulate processing time
    return data.upper()


async def main():
    """Main async function demonstrating concurrent operations"""
    urls = [
        "https://httpbin.org/json",
        "https://httpbin.org/uuid",
        "https://httpbin.org/headers",
    ]

    start_time = time.time()

    # Create aiohttp session
    async with aiohttp.ClientSession() as session:
        # Fetch all URLs concurrently
        fetch_tasks = [fetch_data(url, session) for url in urls]
        results = await asyncio.gather(*fetch_tasks)

        # Process results concurrently
        process_tasks = [process_data(result) for result in results]
        processed_results = await asyncio.gather(*process_tasks)

        # Display results
        for result in processed_results:
            print(result)

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
