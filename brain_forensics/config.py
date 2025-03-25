import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys (using environment variables for security)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Data storage settings
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# Ensure directories exist
for directory in [DATA_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Analysis settings
SENTIMENT_THRESHOLD_NEGATIVE = -0.3
SENTIMENT_THRESHOLD_POSITIVE = 0.3

# List of platforms to analyze
PLATFORMS = ["twitter", "facebook", "instagram", "linkedin"]

# NLP settings
NLTK_DATA_PATH = os.path.join(DATA_DIR, "nltk_data")

# MongoDB settings (for storing analysis results)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = "social_media_forensics"
MONGO_COLLECTION = "analysis_results"

# Web search settings
MAX_SEARCH_RESULTS = 10
SEARCH_TIMEOUT = 30  # seconds 