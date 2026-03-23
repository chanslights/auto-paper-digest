"""
Configuration module for Auto Paper Digest.

Centralizes all paths, URLs, and default settings.
"""

from pathlib import Path

# =============================================================================
# Directory Paths
# =============================================================================

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"

# Data subdirectories
PDF_DIR = DATA_DIR / "pdfs"
VIDEO_DIR = DATA_DIR / "videos"
SLIDES_DIR = DATA_DIR / "slides"
DIGEST_DIR = DATA_DIR / "digests"
PROFILE_DIR = DATA_DIR / "profiles"

# Database
DB_PATH = DATA_DIR / "apd.db"

# Default browser profile name
DEFAULT_PROFILE = "default"

# =============================================================================
# URLs
# =============================================================================

# Hugging Face papers page (date-based and week-based)
HF_PAPERS_URL = "https://huggingface.co/papers"
HF_PAPERS_DATE_URL = "https://huggingface.co/papers?date={date}"
HF_PAPERS_DATE_PAGE_URL = "https://huggingface.co/papers/date/{date}"  # e.g., /date/2026-01-08
HF_PAPERS_WEEK_URL = "https://huggingface.co/papers/week/{week}"  # e.g., /week/2026-W01

# arXiv PDF download template
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_PDF_URL = "https://export.arxiv.org/pdf/{paper_id}.pdf"

# NotebookLM
NOTEBOOKLM_URL = "https://notebooklm.google.com"

# =============================================================================
# NotebookLM Steering Prompts
# =============================================================================

NOTEBOOKLM_PROMPT_SLIDES_MENTAL_HEALTH = """请用中文制作演示文稿（Slides），风格要求：1. 每页布局简洁清晰，重点突出；2. 使用通俗易懂的语言，避免专业术语；3. 总共8-12页；4. 结构：封面（标题+作者）、研究背景（1页）、核心发现（3-5页）、结论与建议（2页）、参考文献。"""

# =============================================================================
# Prompt File Reader
# =============================================================================

def read_prompt_file(filename: str) -> str:
    """
    Read a prompt from a file in the prompts directory.
    
    Args:
        filename: e.g. "mental_health_slides.txt"
        
    Returns:
        The prompt content, or empty string if file not found
    """
    path = PROFILE_DIR.parent / "prompts" / filename
    if path.exists():
        return path.read_text().strip()
    return ""


NOTEBOOKLM_PROMPT_MENTAL_HEALTH = """请用中文普通话生成视频内容。语音：专业温和的医生风格。内容：极度简洁，保留论文最核心的1-2个发现，用通俗语言解释，不涉及专业术语。结构：开头吸引注意（15秒），核心讲清发现（2分钟），结尾给健康建议（15秒）。总时长3分钟以内。"""

# =============================================================================
# Defaults
# =============================================================================

# Maximum papers to fetch per week
DEFAULT_MAX_PAPERS = 50

# Maximum retry attempts for failed operations
MAX_RETRIES = 3

# Request timeout in seconds
REQUEST_TIMEOUT = 60

# Download chunk size
DOWNLOAD_CHUNK_SIZE = 8192

# Delay between downloads (seconds) to respect arXiv rate limits
DOWNLOAD_DELAY_SECONDS = 3

# Playwright timeouts (milliseconds)
PLAYWRIGHT_TIMEOUT = 60000  # 60 seconds for general operations
PLAYWRIGHT_NAVIGATION_TIMEOUT = 120000  # 120 seconds for page navigation
PLAYWRIGHT_VIDEO_TIMEOUT = 900000  # 15 minutes for video generation

# User agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# =============================================================================
# Status Constants
# =============================================================================

class Status:
    """Paper processing status values."""
    NEW = "NEW"
    PDF_OK = "PDF_OK"
    NBLM_OK = "NBLM_OK"  # Notebook created, PDF uploaded
    VIDEO_OK = "VIDEO_OK"
    ERROR = "ERROR"


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for directory in [PDF_DIR, VIDEO_DIR, SLIDES_DIR, DIGEST_DIR, PROFILE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
