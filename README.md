# OBS Cricket Stream Automation

This project contains a Python script (`obs.py`) that completely automates the setup and execution of live cricket broadcasts on YouTube using OBS Studio. 

## Features
- **Dynamic Title Generation:** Automatically scrapes and fetches the match title and tournament name from CricHeroes based on a provided Match ID.
- **Smart Descriptions:** Auto-generates the YouTube stream description with a random selection of 5-10 popular cricket hashtags.
- **Ticker Customization:** Automatically assigns a random Web Ticker theme from CricHeroes to the OBS Browser Source.
- **Multi-Ground Support:** Prompts the user to select between Ground 1 and Ground 2, dynamically routing the correct RTSP camera feed into OBS.
- **YouTube API Integration:** Creates a scheduled YouTube live broadcast and retrieves a secure stream key automatically.
- **OBS WebSocket Control:** Connects to OBS to update camera URLs, ticker URLs, inject the stream key, and start the stream without manual GUI clicks.

## Prerequisites
- **Python 3.7+**
- **OBS Studio** with WebSocket server enabled (Port `4455`).
- **Google Cloud Console App:** You need a `client_secrets.json` file with YouTube Data API v3 permissions placed in the root directory to authenticate broadcasts.

## Installation

Install the required Python packages using pip:

```bash
pip install obs-websocket-py google-api-python-client google-auth-oauthlib google-auth-httplib2 beautifulsoup4 requests
```

## Setup & Configuration
Before running the script, ensure that your OBS Studio has:
1. A Browser Source named exactly `Ticker` (or update `BROWSER_SOURCE_NAME`).
2. A Media Source named exactly `Camera` (or update `CAMERA_SOURCE_NAME`).
3. Update `OBS_PASSWORD` in `obs.py` with your OBS WebSocket password.

## Usage
Start OBS Studio, then run the automation script:

```bash
python obs.py
```
Follow the terminal prompts to enter your Match ID, confirm your title, and select your ground. The script will handle the rest and put you LIVE!