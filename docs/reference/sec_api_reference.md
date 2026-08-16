# SEC API Documentation

> **FinWiz Integration Status**: This documentation is provided as **reference material only**.
>
> **Current Implementation**: FinWiz does not actively use the SEC API service. Instead, we:
>
> - Generate SEC filing URLs using `SECFilingURLGenerator`
> - Download HTML directly from SEC.gov (free)
> - Parse content with BeautifulSoup and split it with a local `chunk_text()` helper (not the `unstructured` library — `unstructured`, `faiss`, and `OpenAIEmbeddings` appear nowhere in `src/` or `pyproject.toml`)
> - Extract insights using simple keyword-based text matching (not vector similarity search or embeddings — see `EnhancedSECAnalysisTool._extract_section_insights()`, which has an inline comment stating this explicitly)
>
> **API Key**: No API key is required. `SEC_API_API_KEY` is not read by any code — the optional `sec_api` integration was removed as part of a dependency trim, and `EnhancedSECAnalysisTool._get_filing_date_from_api()` always returns `None`. The variable name only survives in the log sanitizer's redaction list as a defensive precaution.
>
> **Future Integration**: This documentation could be useful if we decide to integrate the paid SEC API service for enhanced section extraction capabilities.

## Extractor API

10-K/10-Q/8-K Extractor API
Content section extracted from 10-K filing
The Extractor API extracts any text section from 10-Q, 10-K and 8-K SEC filings, and returns the extracted content in cleaned and standardized text or HTML format. Send the URL of the filing, the section name (e.g. Item 1A) and the return data type (e.g. raw text) to the Extractor API and the extracted content is returned.

You can programmatically extract one or multiple text sections from any 10-Q, 10-K and 8-K filing. The extracted section item is returned as clear-text without HTML tags or standardized HTML. There is no need to develop your own item extraction algorithm anymore. Amended filings, such as 10-Q/A, 10-K/A and 8-K/A as well as all 10-K form variants, such as 10-KT, 10KSB, are also supported.

Dataset size:
All sections of all 10-K, 10-Q and 8-K filings including their variants filed since 1994 to present.
Data update frequency:
Extracted sections from new filings are available within 300 milliseconds after their publication on EDGAR.
Survivorship bias free:
Yes. The Extractor API provides sections of all 10-K, 10-Q and 8-K filings filed since 1994 to present, from filer entities that are still active and those that are no longer active.
Supported 10-K Section Items
The Extractor API supports extracting all section items from Form 10-K filings as listed below:

1 - Business
1A - Risk Factors
1B - Unresolved Staff Comments
1C - Cybersecurity
2 - Properties
3 - Legal Proceedings
4 - Mine Safety Disclosures
5 - Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities
6 - Selected Financial Data (prior to February 2021)
7 - Management’s Discussion and Analysis of Financial Condition and Results of Operations
7A - Quantitative and Qualitative Disclosures about Market Risk
8 - Financial Statements and Supplementary Data
9 - Changes in and Disagreements with Accountants on Accounting and Financial Disclosure
9A - Controls and Procedures
9B - Other Information
10 - Directors, Executive Officers and Corporate Governance
11 - Executive Compensation
12 - Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters
13 - Certain Relationships and Related Transactions, and Director Independence
14 - Principal Accountant Fees and Services
15 - Exhibits and Financial Statement Schedules
The item extractor supports all 10-K form types including old fashioned TXT versions filed prior to 2003. Supported types include:
10-K/A, 10-KT/A, 10KSB, 10KSB/A, 10KT405, 10KT405/A, 10KSB40, 10KSB40/A, 10-K405, 10-K405/A, 10KSB, 10KSB

Supported 10-Q Section Items
The Extractor API supports extracting all section items from Form 10-Q filings as listed below:

Part 1:
1 - Financial Statements
2 - Management’s Discussion and Analysis of Financial Condition and Results of Operations
3 - Quantitative and Qualitative Disclosures About Market Risk
4 - Controls and Procedures
Part 2:
1 - Legal Proceedings
1A - Risk Factors
2 -Unregistered Sales of Equity Securities and Use of Proceeds
3 - Defaults Upon Senior Securities
4 - Mine Safety Disclosures
5 - Other Information
6 - Exhibits
Supported 8-K Section Items
The Extractor API supports extracting all section items for each triggering event from Form 8-K filings as listed below:

1.01: Entry into a Material Definitive Agreement
1.02: Termination of a Material Definitive Agreement
1.03: Bankruptcy or Receivership
1.04: Mine Safety - Reporting of Shutdowns and Patterns of Violations
1.05: Material Cybersecurity Incidents (introduced in 2023)
2.01: Completion of Acquisition or Disposition of Assets
2.02: Results of Operations and Financial Condition
2.03: Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant
2.04: Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement
2.05: Cost Associated with Exit or Disposal Activities
2.06: Material Impairments
3.01: Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing
3.02: Unregistered Sales of Equity Securities
3.03: Material Modifications to Rights of Security Holders
4.01: Changes in Registrant's Certifying Accountant
4.02: Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review
5.01: Changes in Control of Registrant
5.02: Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers: Compensatory Arrangements of Certain Officers
5.03: Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year
5.04: Temporary Suspension of Trading Under Registrant's Employee Benefit Plans
5.05: Amendments to the Registrant's Code of Ethics, or Waiver of a Provision of the Code of Ethics
5.06: Change in Shell Company Status
5.07: Submission of Matters to a Vote of Security Holders
5.08: Shareholder Nominations Pursuant to Exchange Act Rule 14a-11
6.01: ABS Informational and Computational Material
6.02: Change of Servicer or Trustee
6.03: Change in Credit Enhancement or Other External Support
6.04: Failure to Make a Required Distribution
6.05: Securities Act Updating Disclosure
6.06: Static Pool
6.10: Alternative Filings of Asset-Backed Issuers
7.01: Regulation FD Disclosure
8.01: Other Events
9.01: Financial Statements and Exhibits
Signature
In very rare cases (~1 in 1,000 filings) a filing contains multiple sections merged into one section. Those cases are not covered by the extractor API.

API Endpoint
Extracted sections from 10-K, 10-Q and 8-K filings are obtained by sending a HTTP GET request with the URL of the filing, the item ID of the section and the return data type (HTML or text) to the following endpoint:

<https://api.sec-api.io/extractor>
Supported HTTP method: GET

Response content type: text or HTML. The type depends on the return type parameter in the request. For example, set type=text to return the extracted section as plain text. Set type=html to return the extracted section as HTML.

Request Parameters
url (required) - URL of the 10-K, 10-Q or 8-K filing. For example, the URL of Tesla's 10-K filing for the fiscal year ended December 31, 2020 is <https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm>
The URL can represent the .txt or .htm version of the filing.
item (required) - The item to be extracted, e.g. 1A. One item per API call is supported.
10-K supported item codes: 1, 1A, 1B, 1C, 2, 3, 4, 5, 6, 7, 7A, 8, 9, 9A, 9B, 10, 11, 12, 13, 14, 15
10-Q supported item codes: part1item1, part1item2, part1item3, part1item4, part2item1, part2item1a, part2item2, part2item3, part2item4, part2item5, part2item6
8-K supported item codes: 1-1, 1-2, 1-3, 1-4, 1-5, 2-1, 2-2, 2-3, 2-4, 2-5, 2-6, 3-1, 3-2, 3-3, 4-1, 4-2, 5-1, 5-2, 5-3, 5-4, 5-5, 5-6, 5-7, 5-8, 6-1, 6-2, 6-3, 6-4, 6-5, 6-6, 6-10, 7-1, 8-1, 9-1, signature
type (optional) - The return type of the item can be text or html. text returns clear, formatted text without any XBRL, XML or HTML tags. For text, HTML character entities such as &#160; are not removed and the start and end of tables are marked with ##TABLE_START and ##TABLE_END respectively. The text return type is commonly used for NLP tasks. html returns the orignal, cleaned HTML version of the item including tables. Default: text
token (required) - Your API key.

Important: If you send a 10-Q filing URL to the Extractor API while providing an item code not supported by 10-Q filings, you will encounter a request error. For example, the 10-K item code 1A (risk factor section) is not included in 10-Q filings. Therefore, item 1A cannot be extracted from 10-Q filings. The correct 10-Q item code is part2item1a.
Request Examples
Get item 1A (Risk Factors) in clear text from Tesla's recent 10-K filing:

<https://api.sec-api.io/extractor>?
url=<https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm&>
item=1A&
type=text&
token=YOUR_API_KEY

Get item 8 (Financial Statements and Supplementary Data) as HTML from Apple's recent 10-K filing:

<https://api.sec-api.io/extractor>?
url=<https://www.sec.gov/Archives/edgar/data/320193/000032019321000056/aapl-20210327.htm&>
item=8&
type=html&
token=YOUR_API_KEY

Get item 1A in part 2 (Risk Factors) as HTML from Microsoft's recent 10-Q filing:

<https://api.sec-api.io/extractor>?
url=<https://www.sec.gov/Archives/edgar/data/789019/000156459022015675/msft-10q_20220331.htm&>
item=part2item1a&
type=html&
token=YOUR_API_KEY

Response Format
The Extractor API returns the extracted item section in clear text or HTML format. The following are examples of the extracted Item 1A (Risk Factors) section from a 10-K filing in clear text and HTML format.

Text Example of Item 1A:
Text
You should carefully consider the risks described below together with the other information set forth in this report, which could materially affect our business, financial condition and future results. The risks described below are not the only risks facing our company. Risks and uncertainties not currently known to us or that we currently deem to be immaterial also may materially adversely affect our business, financial condition and operating results.
Risks Related to Our Ability to Grow Our Business
We may be impacted by macroeconomic conditions resulting from the global COVID-19 pandemic.
Since the first quarter of 2020, there has been a worldwide impact from the COVID-19 pandemic. Government regulations and shifting social behaviors have limited or closed non-essential transportation, government functions, business activities and person-to-person interactions. In some cases, the relaxation of such trends has recently been followed by actual or contemplated returns to stringent restrictions on gatherings or commerce, including in parts of the U.S. and a number of areas in Europe.
We temporarily suspended operations at each of our manufacturing facilities worldwide for a part of the first half of 2020. Some of our suppliers and partners also experienced temporary suspensions ...
... (truncated)
HTML Example of Item 1A:
HTML
<p>RISK FACTORS</p>
<p>
  You should carefully consider the risks described below together with the
  other information set forth in this report, which could materially affect our
  business, financial condition and future results. The risks described below
  are not the only risks facing our company. Risks and uncertainties not
  currently known to us or that we currently deem to be immaterial also may
  materially adversely affect our business, financial condition and operating
  results.
</p>
<p>Risks Related to Our Ability to Grow Our Business</p>
<p>
  We may be impacted by macroeconomic conditions resulting from the global
  COVID-19 pandemic.
</p>
<p>
  Since the first quarter of 2020, there has been a worldwide impact from the
  COVID-19 pandemic. Government regulations and shifting social behaviors have
  limited or closed non-essential transportation, government functions, business
  activities and person-to-person interactions.
  <span>In some cases, the relaxation of such trends has recently been followed by
    actual or contemplated returns to stringent restrictions on gatherings or
    commerce, including in parts of the U.S. and a number of areas in
    Europe.</span

  >
</p>
<p>
  We temporarily suspended operations at each of our manufacturing facilities
  worldwide for a part of the first half of 2020. Some of our suppliers and
  partners also experienced temporary suspensions ...
</p>
... (truncated)
Frequently Asked Questions
API Processing Response
The "processing" response status occurs when:

A recent filing has been submitted and our system is extracting the sections. This usually resolves quickly as the system finishes its processing. Waiting for 500 to 1000 milliseconds before retrying usually results in successfully obtaining the extracted section.
You've requested a section from a filing that may not exist, often in 8-K filings which don't always include all sections. Our system will try to extract the section, causing the "processing" status. For 8-Ks, verify section existence using our Query API, which provides a metadata object with an items property listing the sections contained in the filing.
Should the "processing" response persist after three retries, each delayed by 500 to 1000 milliseconds, it is likely that the section is non-extractable, possibly due to its absence or other reasons detailed below.

Empty Sections and Unparseble Filings
Filings prior to the Sarbanes-Oxley Act (SOX) in 2002, such as 10-K and 10-Q reports, may not have a well standardized structure, which can affect the extractability of sections, particularly for older documents. To collate and download sections from 10-K, 10-Q and 8-K filings, use our Query API to compile a list of metadata objects for all such form types. This includes the accession numbers, filing URLs, publication dates, CIKs, ticker symbols, and referenced entities.

Before building this dataset, understanding the difference between filing ID, accession number, CIK and their interrelationships is crucial:

The id property from the Query API uniquely identifies a metadata object in our database.
The accessionNo property uniquely identifies a filing within the EDGAR database.
The cik property uniquly identifies a filer within the EDGAR database.
When collecting filing metadata, it's possible to encounter multiple metadata objects linked to the same filing. Each object will have a unique id but share the same accessionNo. The differences between these objects are found in the id, cik,ticker, and companyName properties. This occurs because the EDGAR index includes a record for each entity referenced in a filing. For example, Entergy's 10-Q filing references seven entities, resulting in seven metadata objects and filing URLs. However, all these point to one filing identified by a single accession number. For accurate dataset compilation, it's essential to remove duplicates based on the accessionNo, ensuring each accession number is unique within your dataset, rather than relying on the id.

intel-10-k-referencing-one-entity
Figure: Intel's 10-K filing referencing one entity
entergy-10-k-referencing-seven-entities
Figure: Entergy's 10-Q filing referencing seven entities
Before extracting sections with your metadata dataset, it's important to refine it to exclude filings of entities that do not provide standard filing sections. Trusts and REITs, for instance, file 10-Ks and 10-Qs but may lack sections like Management Discussion and Analysis (MD&A). Use our Mapping API to correlate the CIKs with SIC codes (sic) and security types (category) and exclude irrelevant entities. Common exclusions are:

Security type (category) that fall into ETD, ETF, UNIT, CEF categories.
SIC code (sic) corresponding to 6189 (asset-backed securities) and 6798 (Real Estate Investment Trusts).
Our Extractor API may not cover some sections of 10-K, 10-Q and 8-K filings, particularly those from trusts with non-standard structures or empty sections. Here are examples of such filings:

STRATS Trust's 10-K has an empty MD&A section. View Filing
CorTS Trust's 10-K also lacks an MD&A section. View Filing
Sabine Royalty Trust's 10-K includes a section titled "Trustee's Discussion and Analysis". View Filing
North European Oil Royalty Trust's 10-Q does not follow a standardized filing structure and omits the MD&A section. View Filing
Non-standard filings that don't follow the SEC's proposed filing structure can also impede extraction. For instance:

Citigroup's 10-K has a scattered Item 7 MD&A, making it difficult to parse as it is distributed across various parts of the document. View Filing
GE's 10-K presents an overlapping structure where Item 1 spans multiple, non-sequential pages and intersects with other items, complicating extraction. View Filing
Intel's 10-K, similar to GE's filing, spreads the business section in Item 1 across various non-sequential pages, making the reliable extraction of Item 1 unfeasible. View Filing
For tasks like backtesting trading strategies that rely on data from extracted filing sections, it's recommended to focus on filings post-2004. This recommendation is due to the significant changes in the SEC's filing requirements, disclosure activity, and the number of active entities on EDGAR after the SOX regulations took effect. The adoption of Form 8-K and Form 4 filings became more prevalent after this period. This shift is highlighted by two figures:

annually-active-edgar-entities-and-annual-filing-volume
Figure: Annual number of active EDGAR entities and volume of filings from 1994 to 2022.
annual-filing-volume-of-top-20-most-common-form-types
Figure: Annual number of filings for top 20 most commonly filed forms from 1994 to 2022.

## FinWiz Implementation Notes

### Current SEC Analysis Approach

FinWiz implements SEC filing analysis without using the paid SEC API service:

**1. Filing URL Generation**

- Uses `SECFilingURLGenerator` to create valid SEC.gov URLs
- Generates company browse pages for manual filing access
- Validates URLs before including in reports

**2. Direct HTML Parsing**

- Downloads HTML content directly from SEC.gov (free)
- Uses proper User-Agent headers as required by SEC.gov
- Implements rate limiting and error handling

**3. Content Processing** (corrected — see note at top of this document)

- Parses HTML using BeautifulSoup (`from bs4 import BeautifulSoup`, `src/finwiz/tools/enhanced_sec_tool.py:508`), not the `unstructured` library
- Splits content into manageable chunks with the local `chunk_text()` helper (`src/finwiz/tools/_text_chunking.py`), which explicitly replaces `langchain_text_splitters.CharacterTextSplitter` per its own docstring
- No vector embeddings of any kind are created

**4. Insight Extraction** (corrected)

- Uses simple keyword-based text matching — scores each chunk by counting section-specific keyword hits (`src/finwiz/tools/enhanced_sec_tool.py:241`, inline comment: "Use simple keyword-based text matching instead of vector search"), not FAISS or any vector similarity search
- Extracts section-specific insights (Item 1, 1A, 7, etc.)
- Provides proper SEC citations and filing references

**5. Risk Assessment**

- Analyzes Item 1A (Risk Factors) content
- Calculates standardized risk scores (0-5 scale)
- Maps to risk levels (Low, Medium, High, Very High)

### Integration Points

**SEC API Usage**: None. The `sec_api` integration was removed as part of a dependency trim.

- `EnhancedSECAnalysisTool._get_filing_date_from_api()` always returns `None`; it is kept only as a patch point for tests and any future provider
- Callers fall back to the current timestamp for `filed_at`
- No `SEC_API_API_KEY` is read by any code; it needs no configuration

**Code Location**:

- Main implementation: `src/finwiz/tools/enhanced_sec_tool.py`
- URL generation: `src/finwiz/tools/sec_filing_url_generator.py`
- Integration tests: `tests/unit/tools/test_enhanced_sec_tool.py`

### Benefits of Current Approach

- **Cost-effective**: Uses free SEC.gov resources
- **Reliable**: Direct access to official SEC data
- **Flexible**: Custom parsing and analysis logic
- **Testable**: No external API dependencies for core functionality
- **Compliant**: Follows SEC.gov access guidelines

### Future Enhancement Options

If enhanced section extraction is needed, the SEC API could be integrated for:

- More precise section boundaries
- Better handling of complex filing structures
- Faster processing of large filing volumes
- Access to historical filings with consistent formatting

References
For more information about Form 10-K, 10-Q and 8-K filings visit the SEC websites here:
