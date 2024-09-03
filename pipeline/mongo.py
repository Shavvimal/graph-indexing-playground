import asyncio
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import os
# Utils & Models
from utils.col import p
from models.transcript import Transcript
from models.scraper import Article
from datetime import datetime


class MongoDatabase:
    """
    A class for interacting with a MongoDB database asynchronously.
    This class utilizes the motor library to establish a connection.
    """
    _instance = None

    def __new__(cls, _uri: str, _db: str):
        if cls._instance is None:
            cls._instance = super(MongoDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self, _uri: str, _db: str = "antler"):
        self._MONGO_URI = _uri
        self._DB_NAME = _db
        self.client = None
        self.db = None
        p.printh(f"Mongo Instance Created")

    async def setup_client(self):
        self.client = AsyncIOMotorClient(self._MONGO_URI)
        self.db = self.client[self._DB_NAME]

    async def close_client(self):
        if self.client:
            self.client.close()

    async def insert_list_transcripts(self, collection: str, transcripts: List[Transcript]):
        """
        Inserts a list of transcripts into the database.
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            transcripts = [transcript.dict() for transcript in transcripts]
            await collection.insert_many(transcripts)
            p.printh(f"Inserted `{len(transcripts)}` Transcripts into the database.")
        except Exception as error:
            p.printf(f"Error inserting transcripts: {error}")

    async def insert_single_transcript(self, collection: str, transcript: Transcript):
        """
        Inserts a single transcript into the database.
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            transcript_dict = transcript.dict()
            await collection.insert_one(transcript_dict)
            p.printh(f"Inserted `{transcript.subject}` Transcripts into the database.")
        except Exception as error:
            p.printf(f"Error inserting transcript: {error}")

    async def delete_older_than_transcripts(self, collection: str, date: datetime):
        """
        Delete all transcripts older than a certain date.
        :param date:
        :return:
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            await collection.delete_many({"date": {"$lt": date}})
        except Exception as error:
            p.printf(f"Error deleting transcripts: {error}")

    async def get_all_video_ids(self, collection: str):
        """
        Returns a list of video_ids in the collection.
        :param collection:
        :return:
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            video_ids = await collection.distinct("video_id")
            return video_ids
        except Exception as error:
            p.printf(f"Error getting video_ids: {error}")
            return []

    async def update_transcript_meta(self, collection: str, video_id: str, meta: dict):
        """
        Updates the metadata of a transcript.
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            await collection.update_one({"video_id": video_id}, {"$set": meta})
            p.printh(f"Updated metadata for video_id `{video_id}` in the `{collection}` collection.")
        except Exception as error:
            p.printf(f"Error updating transcript metadata: {error}")

    async def collect_all_articles(self, collection: str):
        """
        Collects all transcripts from a collection.
        """
        try:
            if self.client is None:
                await self.setup_client()
            collection = self.db[collection]
            articles = await collection.find().to_list(length=None)
            for article in articles:
                article['id'] = str(article['_id'])
                article["date"] = article["date"].strftime("%Y-%m-%d %H:%M:%S")
            return [Article(**article) for article in articles]
        except Exception as error:
            p.printf(f"Error fetching transcripts: {error}")
            return []


if __name__ == '__main__':
    from dotenv import load_dotenv
    import pandas as pd
    import asyncio
    import time
    # Load .env
    load_dotenv()


    async def main():
        uri = os.getenv("MONGO_URI")
        db = "antler"
        collection = "antler-academy-scrape"
        mongo = MongoDatabase(uri, db)
        articles = await mongo.collect_all_articles(collection)
        # Convert to CSV
        run_id = time.strftime("%Y%m%d-%H%M%S")
        df = pd.DataFrame([article.dict() for article in articles])
        df.to_csv(f"../bin/data/articles-{run_id}.csv", index=False, encoding='utf-8')

    asyncio.run(main())
