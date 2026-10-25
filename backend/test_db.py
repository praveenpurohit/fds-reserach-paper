import asyncio
import asyncpg

async def test():
    # Try different connection methods
    for host in ["127.0.0.1", "localhost", "::1"]:
        try:
            conn = await asyncpg.connect(host=host, port=5432, user="research", database="research_db", password="research123")
            print(f"Connected via {host}!")
            await conn.close()
            return
        except Exception as e:
            print(f"{host}: {e}")

    # Try without password
    for host in ["127.0.0.1", "localhost"]:
        try:
            conn = await asyncpg.connect(host=host, port=5432, user="research", database="research_db")
            print(f"Connected (no pass) via {host}!")
            await conn.close()
            return
        except Exception as e:
            print(f"{host} (no pass): {e}")

asyncio.run(test())
