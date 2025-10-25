"""
SEC Filing URL Generator for generating valid, working SEC filing URLs.

This module provides functionality to generate valid SEC EDGAR URLs for company filings,
with CIK lookup, URL verification, and proper fallback handling.

Uses sec-edgar-downloader for reliable filing downloads.
"""

import json
from pathlib import Path

import httpx
from pydantic import BaseModel, Field
from sec_edgar_downloader import Downloader

from finwiz.tools.logger import get_logger
from finwiz.utils.url_validator import get_url_validator

logger = get_logger(__name__)


class SECFilingURLGenerator:
    """
    Generate valid SEC filing URLs with verification and fallback handling.

    This class provides methods to:
    - Look up company CIK numbers
    - Generate direct filing URLs
    - Generate company browse page URLs as fallback
    - Verify URL accessibility
    """

    # SEC EDGAR base URLs
    SEC_EDGAR_BASE = "https://www.sec.gov"
    SEC_CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

    # Common filing types
    FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A", "S-1", "20-F"]

    def __init__(self, timeout: float = 10.0) -> None:
        """
        Initialize SEC Filing URL Generator.

        Args:
            timeout: Timeout in seconds for HTTP requests

        """
        self.timeout = timeout
        self._cik_cache: dict[str, str | None] = {}
        self._url_validator = get_url_validator()

    def get_cik(self, ticker: str) -> str | None:
        """
        Look up CIK number for a given ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            CIK number as string (zero-padded to 10 digits) or None if not found

        """
        ticker = ticker.upper().strip()

        # Check cache first
        if ticker in self._cik_cache:
            return self._cik_cache[ticker]

        try:
            # Use SEC company tickers JSON endpoint
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {"User-Agent": "FinWiz Financial Analysis Tool contact@finwiz.com", "Accept": "application/json"}

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                # Search for ticker in the data
                for entry in data.values():
                    if entry.get("ticker", "").upper() == ticker:
                        cik = str(entry.get("cik_str", "")).zfill(10)
                        self._cik_cache[ticker] = cik
                        logger.info(f"Found CIK {cik} for ticker {ticker}")
                        return cik

                # Ticker not found
                logger.warning(f"No CIK found for ticker {ticker}")
                self._cik_cache[ticker] = None
                return None

        except Exception as e:
            logger.error(f"Error looking up CIK for {ticker}: {str(e)}")
            return None

    def get_filing_url(self, ticker: str, filing_type: str = "10-K", verify: bool = False) -> str | None:
        """
        Get SEC filing URL for a ticker and filing type.

        This method attempts to generate a direct filing URL. If verification is enabled
        and the URL is not accessible, it returns None.

        Args:
            ticker: Stock ticker symbol
            filing_type: SEC filing type (e.g., '10-K', '10-Q')
            verify: Whether to verify URL accessibility

        Returns:
            Filing URL string or None if not available

        """
        ticker = ticker.upper().strip()
        filing_type = filing_type.upper().strip()

        # Get CIK for ticker
        cik = self.get_cik(ticker)
        if not cik:
            logger.warning(f"Cannot generate filing URL for {ticker}: CIK not found")
            return None

        # Generate browse URL (most reliable)
        browse_url = self.get_company_browse_url(cik, filing_type)

        # Validate URL format
        if not self._url_validator.is_valid_url(browse_url, f"SEC filing {ticker}"):
            logger.error(f"Generated invalid URL for {ticker}: {browse_url}")
            return None

        if verify and browse_url:
            if self.verify_url(browse_url):
                return browse_url
            else:
                logger.warning(f"Generated URL not accessible: {browse_url}")
                return None

        return browse_url

    def get_company_browse_url(self, cik: str, filing_type: str | None = None) -> str:
        """
        Get SEC company browse page URL.

        This generates a URL to the SEC EDGAR company filings page, which is
        more reliable than direct filing URLs and serves as a good fallback.

        Args:
            cik: Company CIK number
            filing_type: Optional filing type to filter by

        Returns:
            Company browse page URL

        """
        # Ensure CIK is zero-padded to 10 digits
        cik = str(cik).zfill(10)

        # Build browse URL
        url = f"{self.SEC_CIK_LOOKUP_URL}?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&count=100"

        # Add filing type filter if specified
        if filing_type:
            filing_type = filing_type.upper().strip()
            url = f"{self.SEC_CIK_LOOKUP_URL}?action=getcompany&CIK={cik}&type={filing_type}&dateb=&owner=exclude&count=100"

        logger.debug(f"Generated browse URL for CIK {cik}: {url}")
        return url

    def verify_url(self, url: str) -> bool:
        """
        Verify that a URL is accessible (returns 200 status).

        Args:
            url: URL to verify

        Returns:
            True if URL returns 200 status, False otherwise

        """
        try:
            headers = {
                "User-Agent": "FinWiz Financial Analysis Tool contact@finwiz.com",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            with httpx.Client(timeout=self.timeout) as client:
                response = client.head(url, headers=headers, follow_redirects=True)

                if response.status_code == 200:
                    logger.debug(f"URL verified successfully: {url}")
                    return True
                else:
                    logger.warning(f"URL returned status {response.status_code}: {url}")
                    return False

        except Exception as e:
            logger.error(f"Error verifying URL {url}: {str(e)}")
            return False

    def get_direct_filing_url(self, ticker: str, filing_type: str = "10-K") -> dict | None:
        """
        Get direct URL to actual filing document using SEC EDGAR API.
        
        Uses the official SEC API method as documented:
        1. Get CIK from ticker using company_tickers.json
        2. Get filing metadata from submissions/CIK{cik}.json
        3. Construct direct document URL from accessionNumber and primaryDocument
        
        Args:
            ticker: Stock ticker symbol
            filing_type: SEC filing type (e.g., '10-K', '10-Q')
        
        Returns:
            Dictionary with direct_url, browse_url, filing_date, etc. or None
        """
        ticker = ticker.upper().strip()
        filing_type = filing_type.upper().strip()
        
        cik = self.get_cik(ticker)
        if not cik:
            logger.warning(f"Cannot get direct filing URL for {ticker}: CIK not found")
            return None
        
        try:
            # Use SEC EDGAR API to get filing metadata
            # Format: https://data.sec.gov/submissions/CIK{cik}.json
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            
            # CRITICAL: SEC requires proper User-Agent with contact info
            # Format: CompanyName Name email@company.com
            headers = {
                "User-Agent": "FinWiz Financial Analysis Tool contact@finwiz.com",
                "Accept": "application/json"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # Find latest filing of requested type in recent filings
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            
            for i, form in enumerate(forms):
                if form == filing_type:
                    accession = filings["accessionNumber"][i]
                    primary_doc = filings["primaryDocument"][i]
                    filing_date = filings["filingDate"][i]
                    report_date = filings.get("reportDate", [None] * len(forms))[i]
                    
                    # Construct direct document URL
                    # Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_no_dash}/{primary_doc}
                    accession_no_dash = accession.replace("-", "")
                    cik_no_zeros = str(int(cik))  # Remove leading zeros
                    
                    direct_url = (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik_no_zeros}/{accession_no_dash}/{primary_doc}"
                    )
                    
                    # Also provide browse URL for user reference
                    browse_url = self.get_company_browse_url(cik, filing_type)
                    
                    logger.info(f"Found direct filing URL for {ticker} {filing_type}: {direct_url}")
                    
                    return {
                        "direct_url": direct_url,
                        "browse_url": browse_url,
                        "filing_date": filing_date,
                        "report_date": report_date,
                        "accession_number": accession,
                        "primary_document": primary_doc,
                        "cik": cik,
                        "ticker": ticker,
                        "filing_type": filing_type,
                        "available": True
                    }
            
            logger.warning(f"No {filing_type} filings found for {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get direct filing URL for {ticker}: {e}")
            return None

    def get_filing_metadata(self, ticker: str, filing_type: str = "10-K") -> dict | None:
        """
        Get filing metadata including URL, CIK, and filing type.
        
        Now uses get_direct_filing_url() to get actual document URLs.

        Args:
            ticker: Stock ticker symbol
            filing_type: SEC filing type

        Returns:
            Dictionary with filing metadata or None if not available

        """
        ticker = ticker.upper().strip()
        filing_type = filing_type.upper().strip()

        # Try to get direct filing URL first
        direct_filing = self.get_direct_filing_url(ticker, filing_type)
        
        if direct_filing:
            return {
                "ticker": ticker,
                "cik": direct_filing["cik"],
                "filing_type": filing_type,
                "filing_url": direct_filing["browse_url"],  # Browse URL for users
                "direct_url": direct_filing["direct_url"],  # Direct URL for parsing
                "browse_url": direct_filing["browse_url"],
                "filing_date": direct_filing["filing_date"],
                "available": True,
            }
        
        # Fallback to browse URL only
        cik = self.get_cik(ticker)
        if not cik:
            logger.warning(f"Cannot retrieve filing metadata for {ticker}: CIK not found")
            return None

        browse_url = self.get_company_browse_url(cik, filing_type)
        
        logger.warning(
            f"Could not get direct filing URL for {ticker} ({filing_type}), "
            f"returning browse URL only"
        )

        return {
            "ticker": ticker,
            "cik": cik,
            "filing_type": filing_type,
            "filing_url": browse_url,
            "browse_url": browse_url,
            "available": True,
        }

    def clear_cache(self) -> None:
        """Clear the CIK lookup cache."""
        self._cik_cache.clear()
        logger.debug("CIK cache cleared")


class SECFilingURLInput(BaseModel):
    """Input schema for SEC Filing URL generation."""

    ticker: str = Field(..., description="Stock ticker symbol")
    filing_type: str = Field(default="10-K", description="SEC filing type (e.g., '10-K', '10-Q')")
    verify: bool = Field(default=False, description="Whether to verify URL accessibility")


class SECFilingURLOutput(BaseModel):
    """Output schema for SEC Filing URL generation."""

    ticker: str = Field(..., description="Stock ticker symbol")
    cik: str | None = Field(None, description="Company CIK number")
    filing_type: str = Field(..., description="SEC filing type")
    filing_url: str | None = Field(None, description="Direct filing URL or browse URL")
    browse_url: str | None = Field(None, description="Company browse page URL")
    available: bool = Field(..., description="Whether filing URL is available")
    verified: bool = Field(default=False, description="Whether URL was verified")
    message: str | None = Field(None, description="Status message")
