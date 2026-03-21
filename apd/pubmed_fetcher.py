"""
PubMed papers fetcher module.

Fetches health/medical papers from PubMed and downloads PDFs from PubMed Central.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    DOWNLOAD_DELAY_SECONDS,
)
from .db import get_paper, upsert_paper
from .utils import get_logger

logger = get_logger()

# PubMed API
PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_SEARCH_URL = PUBMED_API_URL + "esearch.fcgi"
PUBMED_FETCH_URL = PUBMED_API_URL + "efetch.fcgi"
PUBMED_LINK_URL = PUBMED_API_URL + "elink.fcgi"

# PubMed Central for PDFs
PMCID_TO_PDF_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf"

# Search for health-related papers
DEFAULT_HEALTH_QUERY = (
    "health[Title/Abstract] OR "
    "medicine[Title/Abstract] OR "
    "clinical[Title/Abstract] OR "
    "medical[Title/Abstract]"
)

# Fields to fetch from PubMed
PUBMED_FIELDS = "uid,title,authors,pubdate,journal,abstract,doi,pmcid"


def search_pubmed(
    query: str,
    max_results: int = 50,
    days_back: int = 7,
    datetype: str = "pdat",
    retmax: int = 500,
) -> list[str]:
    """
    Search PubMed for papers matching the query.
    
    Args:
        query: PubMed search query
        max_results: Maximum number of paper IDs to return
        days_back: Search papers from the last N days
        datetype: Type of date to search ('pdat' = publication date)
        retmax: Maximum IDs to request from API
        
    Returns:
        List of PubMed IDs (PMIDs)
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_query = f"AND ({start_date.strftime('%Y/%m/%d')}[{datetype}] : {end_date.strftime('%Y/%m/%d')}[{datetype}])"
    
    full_query = f"({query}) {date_query}"
    
    params = {
        "db": "pubmed",
        "term": full_query,
        "retmax": retmax,
        "retmode": "json",
        "sort": "date",
        "usehistory": "n",
    }
    
    logger.info(f"Searching PubMed: {query[:50]}... (last {days_back} days)")
    
    try:
        response = requests.get(
            PUBMED_SEARCH_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"PubMed search failed: {e}")
        return []
    
    idlist = data.get("esearchresult", {}).get("idlist", [])
    logger.info(f"Found {len(idlist)} papers in PubMed")
    
    return idlist[:max_results]


def fetch_paper_details(pmids: list[str]) -> list[dict]:
    """
    Fetch detailed information about papers from PubMed.
    
    Args:
        pmids: List of PubMed IDs
        
    Returns:
        List of paper dicts with metadata
    """
    if not pmids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    
    try:
        response = requests.get(
            PUBMED_FETCH_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"PubMed fetch failed: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "lxml")
    papers = []
    
    for article in soup.find_all("pubmedarticle"):
        try:
            pmid = article.find("pmid")
            if not pmid:
                continue
            pmid = pmid.get_text(strip=True)
            
            # Title
            title_elem = article.find("articletitle")
            title = title_elem.get_text(strip=True) if title_elem else f"Paper {pmid}"
            
            # Abstract
            abstract_parts = []
            abstract_elem = article.find("abstract")
            if abstract_elem:
                for text_elem in abstract_elem.find_all("abstracttext"):
                    label = text_elem.get("label", "")
                    text = text_elem.get_text(strip=True)
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = "\n".join(abstract_parts)
            
            # Journal
            journal_elem = article.find("journal")
            journal = ""
            if journal_elem:
                title_elem = journal_elem.find("title")
                if title_elem:
                    journal = title_elem.get_text(strip=True)
            
            # Publication date
            pubdate_elem = article.find("pubdate")
            pubdate = ""
            if pubdate_elem:
                year = pubdate_elem.find("year")
                month = pubdate_elem.find("month")
                day = pubdate_elem.find("day")
                parts = []
                if year:
                    parts.append(year.get_text(strip=True))
                if month:
                    m = month.get_text(strip=True)
                    # Convert month name to number
                    month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                 "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                 "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                    parts.append(month_map.get(m, m.zfill(2)))
                if day:
                    parts.append(day.get_text(strip=True).zfill(2))
                pubdate = "-".join(parts[:3])
            
            # DOI
            article_id_elem = article.find("articleid", {"idtype": "doi"})
            doi = article_id_elem.get_text(strip=True) if article_id_elem else ""
            
            # PMC ID (for PDF download)
            pmcid = None
            for id_elem in article.find_all("articleid"):
                if id_elem.get("idtype") == "pmc":
                    pmcid = id_elem.get_text(strip=True)
                    break
            
            # Authors
            authors = []
            for author in article.find_all("author"):
                lastname = author.find("lastname")
                initials = author.find("initials")
                if lastname:
                    name = lastname.get_text(strip=True)
                    if initials:
                        name += f" {initials.get_text(strip=True)}"
                    authors.append(name)
            
            # Build PDF URL if PMC ID available
            pdf_url = None
            if pmcid:
                pdf_url = PMCID_TO_PDF_URL.format(pmcid=pmcid)
            
            # Build PubMed URL
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            papers.append({
                "paper_id": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "pubdate": pubdate,
                "doi": doi,
                "pmcid": pmcid,
                "authors": authors,
                "pdf_url": pdf_url,
                "pubmed_url": pubmed_url,
                "source": "pubmed",
            })
            
            time.sleep(DOWNLOAD_DELAY_SECONDS)
            
        except Exception as e:
            logger.error(f"Error parsing paper: {e}")
            continue
    
    return papers


def fetch_pmc_pdf_link(pmcid: str) -> Optional[str]:
    """
    Get the direct PDF link from a PMC article page.
    
    Args:
        pmcid: PubMed Central ID (e.g., 'PMC1234567')
        
    Returns:
        Direct PDF URL or None
    """
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Look for PDF link
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "pdf" in href.lower() and href.endswith(".pdf"):
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.ncbi.nlm.nih.gov" + href
                return href
        
        # Try to find PDF in embedded viewer
        for link in soup.find_all("a", {"data-ga-action": "PDF"}):
            href = link.get("href", "")
            if href.endswith(".pdf"):
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.ncbi.nlm.nih.gov" + href
                return href
        
    except Exception as e:
        logger.error(f"Failed to get PMC PDF link for {pmcid}: {e}")
    
    return None


def fetch_health_papers(
    week_id: str,
    max_papers: Optional[int] = 50,
    query: Optional[str] = None,
    days_back: int = 7,
) -> list[dict]:
    """
    Fetch health/medical papers from PubMed and store in database.
    
    Args:
        week_id: Week identifier for storing papers (e.g., "2026-01")
        max_papers: Maximum papers to fetch
        query: Custom PubMed search query (uses default health query if None)
        days_back: Search papers from the last N days
        
    Returns:
        List of paper dicts that were fetched
    """
    search_query = query or DEFAULT_HEALTH_QUERY
    logger.info(f"Fetching health papers for {week_id}: {search_query[:50]}...")
    
    # Step 1: Search PubMed
    pmids = search_pubmed(search_query, max_results=max_papers, days_back=days_back)
    
    if not pmids:
        logger.warning("No papers found in PubMed")
        return []
    
    # Step 2: Fetch details
    papers = fetch_paper_details(pmids[:max_papers])
    
    if not papers:
        logger.warning("Failed to fetch paper details")
        return []
    
    # Step 3: Store in database
    stored_papers = []
    for paper in papers:
        pmid = paper["paper_id"]
        
        # Check if already exists
        existing = get_paper(pmid)
        if existing:
            logger.debug(f"Paper {pmid} already in database")
            stored_papers.append(paper)
            continue
        
        # Insert new paper
        upsert_paper(
            paper_id=pmid,
            week_id=week_id,
            title=paper["title"],
            hf_url=paper["pubmed_url"],
            pdf_url=paper["pdf_url"],
        )
        logger.info(f"Added paper: {pmid} - {paper['title'][:50]}...")
        stored_papers.append(paper)
    
    logger.info(f"Total health papers fetched for {week_id}: {len(stored_papers)}")
    return stored_papers


if __name__ == "__main__":
    # Test
    papers = fetch_health_papers("test", max_papers=3, days_back=7)
    for p in papers:
        print(f"{p['paper_id']}: {p['title'][:60]}...")
        print(f"  PDF: {p['pdf_url']}")
        print()
