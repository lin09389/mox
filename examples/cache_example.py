"""缓存使用示例"""

import asyncio
from mox.core.cache import LLMCache, MemoryCache, DiskCache
from mox.core.llm import Message


async def main():
    cache = LLMCache(backend=MemoryCache(), default_ttl=3600)

    messages = [{"role": "user", "content": "Hello"}]
    cached = cache.get("gpt-4", messages)
    print(f"Cache hit: {cached is not None}")

    response_data = {
        "content": "Hello! How can I help you?",
        "model": "gpt-4",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }
    cache.set("gpt-4", messages, response_data)
    print("Cached response")

    cached = cache.get("gpt-4", messages)
    print(f"After cache set - hit: {cached is not None}")
    print(f"Response: {cached}")

    cache.clear()
    print("Cache cleared")


async def disk_cache_example():
    cache = LLMCache(backend=DiskCache(), default_ttl=7200)

    messages = [{"role": "user", "content": "Test"}]
    cache.set("gpt-4", messages, {"content": "Test response"})

    cached = cache.get("gpt-4", messages)
    print(f"Disk cache hit: {cached is not None}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(disk_cache_example())
