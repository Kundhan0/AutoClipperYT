"""YouTube Uploader module using official YouTube Data API v3 and your local Gateway for metadata."""
import os
import json
import requests
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000")
GATEWAY_MODEL = os.environ.get("GATEWAY_MODEL", "claude-sonnet-4-5")


def get_authenticated_service():
    """Authenticate and return the YouTube service object."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        else:
            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"client_secret.json not found at {CLIENT_SECRET_FILE}. Please place your downloaded OAuth JSON file there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def generate_metadata_with_gateway(clip_title: str, hook: str, transcript_snippet: str = "") -> dict:
    """Use your local gateway (Gemini/Claude) to generate high-CTR title, description, and tags."""
    system_prompt = (
        "You are an expert YouTube Shorts algorithm strategist. "
        "Create an ultra high-CTR, engaging YouTube Short title (max 60 chars, includes #Shorts), "
        "a compelling 2-3 line description with hashtags, and 8-12 search tags. "
        "Return STRICT JSON only, in this exact format:\n"
        '{"title": "Viral Hook Title #Shorts", "description": "Engaging description text\\n\\n#Shorts #Viral", "tags": ["tag1", "tag2", "tag3"]}'
    )
    user_prompt = f"Clip Topic: {clip_title}\nHook: {hook}\nTranscript Context: {transcript_snippet}"

    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": "local"},
            json={
                "model": GATEWAY_MODEL,
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        content_blocks = resp.json().get("content", [])
        raw_text = "".join(
            blk.get("text", "") for blk in content_blocks if isinstance(blk, dict) and blk.get("type") == "text"
        )
        start, end = raw_text.find("{"), raw_text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw_text[start : end + 1])
    except Exception as e:
        print(f"[METADATA FALLBACK] Gateway generation failed: {e}")

    # Fallback if gateway is unreachable
    clean_title = (hook or clip_title or "Must Watch Moment")[:50]
    return {
        "title": f"{clean_title} #Shorts",
        "description": f"{clip_title}\n\n#Shorts #Viral #Trending",
        "tags": ["Shorts", "Viral", "Trending", "Clips"]
    }


def upload_video_to_youtube(video_path: str, title: str, description: str, tags: list[str], privacy: str = "private") -> dict:
    """Uploads the video MP4 to YouTube Shorts and returns status & video ID."""
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": privacy,  # private, unlisted, or public
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=1024 * 1024 * 4, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response.get("id")
    return {
        "success": True,
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "title": title,
        "privacy": privacy
    }
