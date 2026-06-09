import os
import pickle
import random
from datetime import datetime, timezone
from obswebsocket import obsws, requests, exceptions
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- CONFIGURATION ---
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "abOvpgdpRBopj5fd"
BROWSER_SOURCE_NAME = "Ticker"  # Exact name of your browser source in OBS
CAMERA_SOURCE_NAME = "Camera"  # Exact name of your camera source in OBS
# YouTube API Setup Scope
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]




def get_youtube_service():
    """Authenticates the user and returns the YouTube API service object."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Requires client_secrets.json downloaded from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)


def create_youtube_broadcast(youtube, title, description):
    """
    Creates a live broadcast and a video stream on YouTube.
    Explicitly flags the stream as NOT made for kids.
    """
    print("📺 Configuring YouTube Live Broadcast settings...")

    # 1. Create the broadcast shell (Title, Kids status, Privacy)
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    broadcast_body = {
        "snippet": {
            "title": title,
            "description": description,
            "scheduledStartTime": current_time,
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": True,
            "monitorStream": {"enableMonitorStream": False},
        },
    }

    broadcast_res = (
        youtube.liveBroadcasts()
        .insert(part="snippet,status,contentDetails", body=broadcast_body)
        .execute()
    )
    broadcast_id = broadcast_res["id"]

    # 2. Create the live ingestion stream to fetch the Stream Key
    stream_body = {
        "snippet": {"title": title},
        "cdn": {
            "frameRate": "variable",
            "ingestionType": "rtmp",
            "resolution": "variable",
        },
    }

    stream_res = (
        youtube.liveStreams()
        .insert(part="snippet,cdn", body=stream_body)
        .execute()
    )
    stream_key = stream_res["cdn"]["ingestionInfo"]["streamName"]

    # 3. Bind them together
    youtube.liveBroadcasts().bind(
        id=broadcast_id, part="id", streamId=stream_res["id"]
    ).execute()

    print(f"✅ Created Broadcast: {title} (Made for Kids: False)")
    return stream_key, broadcast_id


def update_obs_and_stream(stream_key, ticker_url, camera_url):
    """Connects to OBS via WebSocket, updates browser source, and goes live."""
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)

    try:
        ws.connect()
        print("🔌 Connected to OBS WebSocket successfully.")

        # 1. Update the Browser Source URL
        # OBS WebSocket v5 uses 'SetInputSettings' for changing source properties
        print(f"🌐 Updating Browser Source '{BROWSER_SOURCE_NAME}' to {ticker_url}...")
        ws.call(
            requests.SetInputSettings(
                inputName=BROWSER_SOURCE_NAME, inputSettings={"url": ticker_url}
            )
        )
        print("✅ Browser source updated!")

        # Update the Camera Source Input
        print(f"📷 Updating Camera Source '{CAMERA_SOURCE_NAME}' to {camera_url}...")
        ws.call(
            requests.SetInputSettings(
                inputName=CAMERA_SOURCE_NAME, inputSettings={"input": camera_url}
            )
        )
        print("✅ Camera source updated!")

        # 2. Inject the YouTube Stream Key dynamically into OBS
        # This replaces the need to click "Manage Broadcast" inside the UI
        print("🔑 Injecting new stream key into OBS profile...")
        ws.call(
            requests.SetStreamServiceSettings(
                streamServiceType="rtmp_custom",  # or 'rtmp_common'
                streamServiceSettings={
                    "server": "rtmp://a.rtmp.youtube.com/live2",
                    "key": stream_key,
                },
            )
        )

        # 3. Start Streaming
        print("🚀 Sending Go-Live command to OBS...")
        ws.call(requests.StartStream())
        print("🎉 You are now LIVE!")

    except exceptions.ConnectionFailure:
        print("❌ Could not connect to OBS. Ensure OBS is running and WebSockets are enabled.")
    except Exception as e:
        print(f"❌ Error during OBS automation: {e}")
    finally:
        ws.disconnect()


if __name__ == "__main__":
    try:
        # Initialize YouTube API
        yt_service = get_youtube_service()

        # Get user input for stream details
        stream_title = input("Enter stream title: ")
        stream_description = input("Enter stream description: ")
        match_id = input("Enter match ID: ").strip()

        ticker_urls = [
            f"https://webticker.cricheroes.com/midnight-fire/{match_id}/",
            f"https://webticker.cricheroes.com/minimalist/{match_id}/",
            f"https://webticker.cricheroes.com/modern-edge/{match_id}/",
            f"https://webticker.cricheroes.com/bold-play/{match_id}/",
            f"https://webticker.cricheroes.com/crystal-view/{match_id}/",
            f"https://webticker.cricheroes.com/fresh-field/{match_id}/"
        ]
        ticker_url = random.choice(ticker_urls)
        print(f"🎲 Randomly selected Ticker URL: {ticker_url}")

        while True:
            ground_choice = input("Select Ground (1 for Ground 1, 2 for Ground 2): ").strip()
            if ground_choice == '1':
                camera_url = "rtsp://admin:Admin@1508@192.168.0.111/Streaming/Channels/101/"
                break
            elif ground_choice == '2':
                camera_url = "rtsp://admin:Admin@1508@192.168.0.110/Streaming/Channels/101/"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

        # Step 1 & 2: Define and create the broadcast on YouTube
        youtube_stream_key, broadcast_id = create_youtube_broadcast(
            yt_service, stream_title, stream_description
        )

        # Step 3 & 4: Change OBS settings and hit stream
        update_obs_and_stream(youtube_stream_key, ticker_url, camera_url)

    except Exception as error:
        print(f"💥 Script failed: {error}")