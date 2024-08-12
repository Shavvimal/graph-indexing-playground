from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from models.transcript import Transcript
from typing import List, Dict
from googleapiclient.discovery import build
from youtube_transcript_api._errors import TranscriptsDisabled
import re
import time

def get_transcript_text_single(video_id: str):
    trans = YouTubeTranscriptApi.get_transcript(video_id)
    # returns a list of dictionaries with keys "text", "start", "duration"
    # Collect all "text"
    # Join all text
    raw_text = [chunk["text"] for chunk in trans]
    # Join the list of strings
    raw_text = " ".join(raw_text)
    return raw_text


def extract_video_id_from_error(error_message: str) -> str:
    # Extract video ID using regular expression
    match = re.search(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)", error_message)
    if match:
        return match.group(1)
    return None


def get_transcript_texts(api_key:str, video_ids: list,  max_retries: int = 3) -> List[Transcript]:
    transcripts = []
    retry_video_ids = video_ids.copy()
    retries = 0

    while retry_video_ids:
        try:
            trans, _ = YouTubeTranscriptApi.get_transcripts(retry_video_ids, languages=['en'])
            raw_texts = {}
            for video_id in retry_video_ids:
                if video_id in trans:
                    raw_texts[video_id] = " ".join([chunk["text"] for chunk in trans[video_id]])

            video_info = get_video_info(api_key, retry_video_ids)

            batch_transcripts = [
                Transcript(
                    video_id=video_id,
                    content=content,
                    date=video_info[video_id]["date"],
                    title=video_info[video_id]["title"],
                    description=video_info[video_id]["description"],
                    tags=video_info[video_id].get("tags", [])
                )
                for video_id, content in raw_texts.items()
            ]


            transcripts.extend(batch_transcripts)
            break  # Exit loop if successful

        except TranscriptsDisabled as e:
            print(e)
            # Extract the video_id from the error message
            video_id = extract_video_id_from_error(str(e))
            if video_id:
                print(f"Removing video_id {video_id} from the retry list.")
                retry_video_ids.remove(video_id)
            else:
                print("Could not extract video_id from the error message. Exiting loop.")
                break  # If we can't extract the video_id, stop retrying

        except Exception as e:
            print(f"ParseError encountered: {e}. Retrying in 10 seconds...")
            retries += 1
            if retries > max_retries:
                print("Maximum retries reached. Exiting.")
                break
            time.sleep(10)  # Wait 10 seconds before retrying
            # Retry without removing the video_id from the retry list

    return transcripts


def get_video_ids_from_html(_file_path: str) -> List[str]:
    with open(_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <a> tags where the href attribute starts with "/watch"
    video_links = soup.find_all("a", href=True)

    # Extract video IDs from the href attributes
    video_ids = []
    for link in video_links:
        href = link['href']
        if "/watch?v=" in href:
            video_id = href.split("/watch?v=")[-1]
            if "&" in video_id:  # Sometimes YouTube adds extra params, so strip them off
                video_id = video_id.split("&")[0]
            if video_id not in video_ids:
                video_ids.append(video_id)

    return video_ids


def get_youtube_service(api_key: str):
    # Function to initialize the YouTube API client
    return build('youtube', 'v3', developerKey=api_key)


def get_video_info(api_key: str, video_ids: List[str]) -> Dict[str, Dict[str, str]]:
    youtube = get_youtube_service(api_key)
    video_info = {}

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()

        for item in response['items']:
            video_id = item['id']
            video_info[video_id] = {
                "date": item['snippet']['publishedAt'],
                "title": item['snippet']['title'],
                "description": item['snippet']['description'],
                "tags": item['snippet'].get('tags', [])
            }

    return video_info

if __name__ == "__main__":
    from pprint import pprint
    import asyncio
    from mongo import MongoDatabase
    import os
    from dotenv import load_dotenv

    # Load .env
    load_dotenv()
    # To do this, Name the file with the Channel name, without the @
    # And provide the path to the file
    file_path = "../data/MyFirstMillionPod.html"

    async def generate_transcripts_from_channel_html(_file_path: str, batch_size: int = 49):
        mongo_uri = os.getenv("MONGO_URI")
        yt_api = os.getenv("YT_API")

        name = os.path.basename(_file_path).split(".")[0]

        mongo = MongoDatabase(mongo_uri)
        video_ids = get_video_ids_from_html(file_path)
        print(f"Found `{len(video_ids)}` video IDs in the HTML file for {name}.")
        video_ids_existing = await mongo.get_all_video_ids(name)
        video_ids = [video_id for video_id in video_ids if video_id not in video_ids_existing]
        blacklist = ["UnMGuZUPCxg", "DAVw-yQRUjE", "wdpiD1_kaUo", "OLA5FaLOH0I", "techmgGVOhk", "lZGGMRYdil8", "TTHvgFAzEX0", "3UD9poByGJk", "fCPkg_QH_KA"]
        video_ids = [video_id for video_id in video_ids if video_id not in blacklist]
        print(f"Found `{len(video_ids)}` new video IDs to process.")

        # Batch into 49 video IDs per request to avoid hitting the API limits
        video_ids = [video_ids[i:i + batch_size] for i in range(0, len(video_ids), batch_size)]

        for batch in video_ids:
            transcripts = get_transcript_texts(yt_api, batch)
            # save in Mongo DB
            await mongo.insert_list_transcripts(name, transcripts)

    asyncio.run(generate_transcripts_from_channel_html(file_path))

    async def update_meta_mongo(_file_path: str, batch_size: int = 49):
        mongo_uri = os.getenv("MONGO_URI")
        mongo = MongoDatabase(mongo_uri)
        yt_api = os.getenv("YT_API")

        name = os.path.basename(_file_path).split(".")[0]
        video_ids_existing = await mongo.get_all_video_ids(name)

        batches = [video_ids_existing[i:i + batch_size] for i in range(0, len(video_ids_existing), batch_size)]

        for batch in batches:
            video_info = get_video_info(yt_api, batch)
            for video_id, meta in video_info.items():
                await mongo.update_transcript_meta(name, video_id, meta)

    # asyncio.run(update_meta_mongo(file_path))

