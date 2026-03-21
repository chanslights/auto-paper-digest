"""
Health papers fetcher module.

Searches arXiv for health/medical related papers and downloads PDFs.
Uses the same arXiv PDF download mechanism as the original HF fetcher.
"""

import re
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import (
    ARXIV_API_URL,
    ARXIV_PDF_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
    DOWNLOAD_DELAY_SECONDS,
)
from .db import get_paper, upsert_paper
from .utils import get_logger, get_current_week_id

logger = get_logger()

# Health-related arXiv categories
HEALTH_CATEGORIES = [
    "q-bio",      # Quantitative Biology
    "q-bio.OT",  # Quantitative Biology - Other
    "q-bio.GN",  # Quantitative Biology - Genomics
    "q-bio.BM",  # Quantitative Biology - Biomolecules
    "cs.HC",     # Human-Computer Interaction (health applications)
    "cs.CY",     # Computers and Society (health/medical topics)
    "cs.AI",     # AI (for AI in healthcare papers)
]

# Health-related search terms
HEALTH_KEYWORDS = [
    "health", "medical", "medicine", "clinical", "healthcare",
    "hospital", "patient", "diagnosis", "treatment", "therapy",
    "disease", "cancer", "diabetes", "cardiovascular", "mental",
    "vaccine", "drug", "pharmaceutical", "biomarker", "genomics",
    "proteomics", "bioinformatics", "public health", "epidemic",
    "rehabilitation", "surgery", "imaging", "diagnostic"
]


def search_arxiv_health(
    max_results: int = 50,
    days_back: int = 7,
    categories: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None
) -> list[dict]:
    """
    Search arXiv for health-related papers.
    
    Args:
        max_results: Maximum papers to fetch
        days_back: Search papers from last N days
        categories: arXiv categories to search (uses default if None)
        keywords: Keywords to search (uses default if None)
        
    Returns:
        List of paper dicts
    """
    cats = categories or HEALTH_CATEGORIES
    kws = keywords or HEALTH_KEYWORDS
    
    # Build category query
    cat_query = "+OR+".join([f"cat:{c}" for c in cats])
    
    # Build keyword query
    kw_query = "+OR+".join([f"all:{k}" for k in kws])
    
    # Combine
    query = f"({cat_query})+AND+({kw_query})"
    
    # Calculate date range
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"
    
    full_query = f"{query}+AND+{date_query}"
    
    url = f"{ARXIV_API_URL}?search_query={full_query}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    logger.info(f"Searching arXiv for health papers: {url[:100]}...")
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "xml")
    papers = []
    
    for entry in soup.find_all("entry"):
        try:
            # Paper ID (extract from arXiv URL)
            id_elem = entry.find("id")
            if not id_elem:
                continue
            
            arxiv_url = id_elem.text.strip()
            # Extract ID like "2603.19093v1"
            match = re.search(r'(\d{4}\.\d{4,5})v?\d*', arxiv_url)
            if not match:
                continue
            paper_id = match.group(1)
            
            # Title
            title_elem = entry.find("title")
            title = title_elem.text.strip().replace("\n", " ") if title_elem else f"Paper {paper_id}"
            
            # Abstract
            summary_elem = entry.find("summary")
            abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem else ""
            
            # Authors
            authors = []
            for author in entry.find_all("author"):
                name_elem = author.find("name")
                if name_elem:
                    authors.append(name_elem.text.strip())
            
            # Published date
            published_elem = entry.find("published")
            published = published_elem.text.strip() if published_elem else ""
            
            # PDF URL
            pdf_link = entry.find("link", {"title": "pdf"})
            pdf_url = pdf_link.get("href", "") if pdf_link else ARXIV_PDF_URL.format(paper_id=paper_id)
            
            # arXiv URL
            arxiv_link = entry.find("link", {"rel": "alternate", "type": "text/html"})
            arxiv_url = arxiv_link.get("href", "") if arxiv_link else f"https://arxiv.org/abs/{paper_id}"
            
            # Categories
            cats_list = []
            for cat in entry.find_all("category"):
                term = cat.get("term", "")
                if term:
                    cats_list.append(term)
            
            papers.append({
                "paper_id": paper_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published,
                "pdf_url": pdf_url,
                "hf_url": arxiv_url,  # Using arXiv URL as the main URL
                "categories": cats_list,
                "source": "arxiv-health",
            })
            
            time.sleep(DOWNLOAD_DELAY_SECONDS)
            
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            continue
    
    logger.info(f"Found {len(papers)} health papers in arXiv")
    return papers


def fetch_health_papers(
    week_id: Optional[str] = None,
    max_papers: int = 50,
    days_back: int = 7,
    categories: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
) -> list[dict]:
    """
    Fetch health papers from arXiv and store in database.
    
    Args:
        week_id: Week identifier (e.g., "2026-01"). Defaults to current week.
        max_papers: Maximum papers to fetch
        days_back: Search papers from the last N days
        categories: Specific arXiv categories to search
        keywords: Specific keywords to search
        
    Returns:
        List of paper dicts that were fetched
    """
    # Initialize DB
    from .db import init_db
    init_db()
    
    wid = week_id or get_current_week_id()
    logger.info(f"Fetching health papers for {wid}")
    
    papers = search_arxiv_health(
        max_results=max_papers,
        days_back=days_back,
        categories=categories,
        keywords=keywords
    )
    
    stored = []
    for paper in papers:
        pmid = paper["paper_id"]
        
        existing = get_paper(pmid)
        if existing:
            logger.debug(f"Paper {pmid} already in database")
            stored.append(paper)
            continue
        
        upsert_paper(
            paper_id=pmid,
            week_id=wid,
            title=paper["title"],
            hf_url=paper["hf_url"],
            pdf_url=paper["pdf_url"],
        )
        logger.info(f"Added paper: {pmid} - {paper['title'][:50]}...")
        stored.append(paper)
    
    logger.info(f"Total health papers stored for {wid}: {len(stored)}")
    return stored


if __name__ == "__main__":
    # Test
    papers = fetch_health_papers(max_papers=5, days_back=14)
    print(f"\nFetched {len(papers)} health papers:")
    for p in papers:
        print(f"  {p['paper_id']}: {p['title'][:60]}...")
        print(f"    PDF: {p['pdf_url']}")
