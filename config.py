"""Central configuration, loaded from environment variables / a local .env file.

Copy .env.example to .env and fill in real values for local development.
In production (EC2), set the same variables in the environment.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# --- AWS ---
S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket-name")

# --- Flask ---
# Fall back to a random key so the app still boots without config, but sessions
# won't survive a restart in that case.
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)

# --- CricAPI (only used by debug/call_api.py) ---
CRICAPI_KEY = os.environ.get("CRICAPI_KEY", "")
CRICAPI_SERIES_ID = os.environ.get("CRICAPI_SERIES_ID", "")

# --- MongoDB (only used by the leftover scripts in debug/) ---
MONGO_URI = os.environ.get("MONGO_URI", "")
