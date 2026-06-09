import os
import pickle
import random
import requests as http_requests
from bs4 import BeautifulSoup
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

CRICKET_MASTER_HASHTAGS = [
    "CricketLive", "LiveCricket", "MatchDay", "LiveMatch", "CricketMatch",
    "GameOn", "LiveScore", "CricketUpdates", "BallByBall", "InningsBreak",
    "LiveStreaming", "MatchFixtures", "CricketAction", "OnTheField", "LiveNow",
    "CricketGround", "CricketStadium", "StadiumVibes", "AtTheGround", "PitchReport",
    "GreenTop", "UnderTheLights", "StadiumLights", "MatchAtmosphere", "HomeGround",
    "CricketField", "Outfield", "BoundaryRope", "StandsAreFull", "CrowdRoar",
    "Howzat", "ClassicCatch", "CleanBowled", "Maximum6", "SuperOver",
    "HatTrick", "Powerplay", "DeathOvers", "Centurion", "FiveFor",
    "FreeHit", "DirectHit", "Stumping", "UmpireDecision", "DRSReview",
    "CricketFever", "CricketFans", "CricketMerch", "BarmyArmy", "CricketFamily",
    "BleedBlue", "FanZone", "12thMan", "CricketLife", "LoveCricket",
    "CricketCrazy", "CricketJunkie", "SupportYourTeam", "CricketNation",
    "T20Cricket", "ODI", "TestCricket", "GullyCricket", "LocalCricket",
    "ClubCricket", "BoxCricket", "TournamentDay", "ChampionshipMatch", "KnockoutStage",
    "GrandFinale", "LeagueCricket", "SundayCricket", "WeekendMatch", "CricketSeries",
    "Cricket", "CricLife", "CricketGram", "CricHeroes", "CricketLovers",
    "CricketVideo", "CricketReels", "CricketShorts", "CricketWorld", "InstaCricket",
    "CricketPhotography", "CricketLove", "CricketMeme", "GentlemansGame", "CricketIsLife",
    "CricketNews", "BattingMasterclass", "FastBowling", "SpinWizard", "FieldingDrills",
    "Captaincy", "AllRounder", "CoverDrive", "Yorker", "HelicopterShot", "ManOfTheMatch"
]


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


def fetch_stream_title(match_id):
    """Fetches match title and tournament name to generate the stream title."""
    try:
        # 1. Fetch match_title using BeautifulSoup
        url1 = f"https://cricheroes.com/scorecard/{match_id}/abc/abc/summary"
        web_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response1 = http_requests.get(url1, headers=web_headers)
        response1.raise_for_status()
        soup = BeautifulSoup(response1.text, 'html.parser')
        og_title_meta = soup.find('meta', property='og:title')
        match_title = og_title_meta['content'] if og_title_meta else f"Match {match_id}"
        if "Match" in match_title:
            match_title = match_title.split("Match")[0]
        
        # 2. Fetch tournament_name from API
        url2 = f"https://api.cricheroes.in/api/v1/scorecard/get-match-detailed-info/{match_id}"
        headers = {
            "api-key": "cr!CkH3r0s",
            "device-type": "Chrome: 148.0.0.0",
            "udid": "Test"
        }
        response2 = http_requests.get(url2, headers=headers)
        response2.raise_for_status()
        api_data = response2.json()
        tournament_name = api_data.get("data", {}).get("tournament_name", "Unknown Tournament")

        return f"{match_title} ( {tournament_name})"
    except Exception as e:
        print(f"⚠️ Could not fetch title details: {e}")
        return f"Live Match {match_id}"


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

        match_id = input("Enter match ID: ").strip()

        # Generate stream title dynamically
        print(f"🔍 Fetching details for match ID {match_id}...")
        stream_title = fetch_stream_title(match_id)
        print(f"✅ Generated Stream Title: {stream_title}")

        # Allow user to edit the generated title
        user_title = input(f"Press Enter to keep this title, or type a new one:\n[{stream_title}] > ").strip()
        if user_title:
            stream_title = user_title
        print(f"📝 Final Stream Title: {stream_title}")

        # Generate stream description automatically with 5-10 hashtags
        num_hashtags = random.randint(5, 10)
        selected_hashtags = random.sample(CRICKET_MASTER_HASHTAGS, num_hashtags)
        stream_description = "Live cricket match broadcast!\n\n" + " ".join([f"#{tag}" for tag in selected_hashtags])
        print(f"📝 Generated Stream Description:\n{stream_description}\n")

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

        youtube_url = f"https://www.youtube.com/watch?v={broadcast_id}"
        print(f"\n▶️ Watch your live stream here: {youtube_url}\n")

    except Exception as error:
        print(f"💥 Script failed: {error}")