import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- General Settings ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "Social Media Forensic Analysis Tool (SMFAT)"
VERSION = "1.0.0"

# --- API Keys ---
# Use environment variables for sensitive keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # For simulated data collection via web search
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")  # For LLM-based analysis (sentiment, etc.)

# --- Forensic Data Storage ---
CASES_DIR = os.path.join(BASE_DIR, "cases") # Top-level directory for all cases
REPORTS_DIR = os.path.join(BASE_DIR, "reports") # Directory for generated forensic reports

# Subdirectories within each case (will be created dynamically)
CASE_DATA_DIR_NAME = "data"       # Raw and processed data
CASE_METADATA_DIR_NAME = "metadata" # Hashes, timestamps, logs
CASE_ANALYSIS_DIR_NAME = "analysis" # Analysis results (sentiment, network graphs)
CASE_EXPORTS_DIR_NAME = "exports"   # Exported data files

# Ensure top-level directories exist
os.makedirs(CASES_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- Data Preservation Settings ---
HASH_ALGORITHM = "sha256" # Algorithm for data integrity checks
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ" # ISO 8601 format for timestamps

# --- Supported Platforms ---
# Initial scope as per specification
SUPPORTED_PLATFORMS = ["X", "Facebook", "Instagram", "LinkedIn"]

# --- Web Search Settings (Simulated Data Collection) ---
MAX_SEARCH_RESULTS_PER_PLATFORM = 5 # Limit for simulated data collection per platform
SEARCH_TIMEOUT = 30 # Timeout in seconds for web search requests

# --- LLM Analysis Settings ---
LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
LLM_TEMPERATURE = 0.1 # Lower temperature for more deterministic forensic analysis
LLM_MAX_TOKENS = 2048

# --- Analysis Thresholds ---
SENTIMENT_THRESHOLD_NEGATIVE = -0.3
SENTIMENT_THRESHOLD_POSITIVE = 0.3

# --- Report Settings ---
REPORT_AUTHOR = os.getenv("USER", "Forensic Analyst") # Default report author to system user

# --- Compliance/Legal ---
# Placeholder for future compliance features
PRIVACY_POLICY_URL = "about:blank" # Link to privacy policy/guidelines

# --- Deprecated/Removed Settings ---
# Removed MONGO settings as we'll use file-based storage for simplicity
# Removed old DATA_DIR as it's replaced by CASES_DIR structure 