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

NOTEBOOKLM_PROMPT_MENTAL_HEALTH = """
你是一位专业的临床医生/医学科普专家，需要为普通大众讲解一篇健康/医疗类学术论文的核心内容。
重要：请用中文普通话生成视频内容，包括所有对话、旁白和文字提示。整个视频的音频和字幕必须完全是中文。
要求：
1. 语音：使用标准普通话，语气专业、温和，符合医生科普的语速，避免生硬机械；
2. 内容：极度简洁，仅保留论文最核心的1-2个结论/发现，剔除专业术语（或用通俗语言解释），总时长严格控制在3分钟以内（建议2-3分钟）；
3. 风格：纯科普导向，聚焦「普通人能理解、能应用」的知识点，不涉及复杂实验/数据细节；
4. 结构：
   - 开头（15秒）：用生活化的问题引入，吸引观众注意；
   - 核心（120-150秒）：用通俗易懂的语言讲清论文的核心发现，让观众听得懂、记得住；
   - 结尾（15秒）：给出简单可操作的健康建议。
"""

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
