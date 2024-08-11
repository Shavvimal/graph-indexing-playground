import asyncio
from typing import List
import asyncpg
import os
from datetime import datetime
# Utils & Modelspoetry ad
from utils.col import p
from models.news import Newsletter, NewsletterUpdateEmbedded
from models.rss import ContentUpdate
from dotenv import load_dotenv

load_dotenv()

class PGDatabase:
    """
    A class for interacting with a PostgreSQL database asynchronously.
    This class utilizes the asyncpg library to establish a connection

    Methods:
    - setup_pool: Asynchronously sets up a connection pool.
    - close_pool: Asynchronously closes the connection pool.
    - get_papers: Asynchronously fetches papers from the database
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PGDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._DB_CONN_INFO = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASS'),
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'port': os.getenv('DB_PORT', default=5432),
        }
        self.pool = None
        p.printh(f"PG Instance Created")

    async def setup_pool(self):
        self.pool = await asyncpg.create_pool(**self._DB_CONN_INFO)

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

    async def _select(self, sql_query):
        try:
            if self.pool is None:
                await self.setup_pool()
            async with self.pool.acquire() as connection:
                query = sql_query
                return await connection.fetch(query)
        except Exception as error:
            p.printf(f"Error fetching newsletters: {error}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    import pandas as pd
    import time
    # Load .env
    load_dotenv()

    async def collect_csv():
        pg = PGDatabase()
        sql_query = """
        SELECT uuid, title, content, date, resolved_link, src_uuid FROM public.updates
        WHERE src = 'newsletter' and relevance IS true
        LIMIT 20
        """
        res = await pg._select(sql_query)
        # Convert from records to list of Documents
        res = [{
            "id": str(row["uuid"]),
            "title": row["title"],
            "text": f'# {row["title"]} \n {row["content"]}'.strip(),
            # Format the python datetime as a string
            "date": row["date"].strftime("%Y-%m-%d %H:%M:%S"),
            "link": row["resolved_link"],
            "src_uuid": str(row["src_uuid"])
        } for row in res]

        # save as csv
        run_id = time.strftime("%Y%m%d-%H%M%S")
        df = pd.DataFrame(res, columns=["id", "title", "text", "date"])
        df.to_csv(f"../bin/data/newsletters-{run_id}.csv", index=False, encoding='utf-8')

    asyncio.run(collect_csv())