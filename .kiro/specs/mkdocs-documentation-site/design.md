─────┤
│  Material Theme + Extensions                                │
│  ├── Search (lunr.js)                                      │
│  ├── Navigation (auto-generated)                           │
│  ├── Code Highlighting (Pygments)                          │
│  └── Schema Rendering (custom plugin)                      │
├─────────────────────────────────────────────────────────────┤
│  Content Organization (Diátaxis Framework)                 │
│  ├── docs/tutorials/     (Learning-oriented)               │
│  ├── docs/how-to/        (Problem-solving)                 │
│  ├── docs/reference/     (Information-oriented)            │
│  └── docs/explanations/  (Understanding-oriented)          │
├─────────────────────────────────────────────────────────────┤
│  Build System                                              │
│  ├── Makefile Integration                                  │
│  ├── Content Migration Scripts                             │
│  ├── Link Validation                                       │
│  └── Schema Integration                                    │
├─────────────────────────────────────────────────────────────┤
│  Source Content                                            │
│  ├── Existing docs/ directory                              │
│  ├── .kiro/steering/ files                                 │
│  └── Spec documentation                                    │
└─────────────────────────────────────────────────────────────┘

```

### Technology Stack

- **MkDocs**: Static site generator (v1.5+)
- **Material Theme**: Modern responsive theme with advanced features
- **Extensions**: 
  - `pymdownx.superfences` - Enhanced code blocks
  - `pymdownx.tabbed` - Tabbed content
  - `pymdownx.details` - Collapsible sections
  - `mkdocs-mermaid2-plugin` - Diagram support
  - `mkdocs-awesome-pages-plugin` - Custom navigation
- **Build Tools**: Python, Make, uv package manager

## Components and Interfaces

### 1. MkDocs Configuration (`mkdocs.yml`)

**Purpose**: Central configuration for site structure, theme, and plugins

**Key Configuration Sections**:
```yaml
site_name: FinWiz Documentation
site_description: AI-powered financial analysis platform documentation
site_url: https://finwiz-docs.example.com

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.path
    - toc.follow
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - awesome-pages
  - mermaid2
  - schema-docs  # Custom plugin for JSON schema rendering

markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
  - admonition
  - toc:
      permalink: true
```

### 2. Content Migration System

**Purpose**: Automated migration of existing documentation to new structure

**Components**:

#### Migration Script (`scripts/migrate_docs.py`)

```python
class DocumentationMigrator:
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.migration_rules = self._load_migration_rules()
    
    def migrate_all(self) -> MigrationReport:
        """Migrate all documentation following Diátaxis classification"""
        
    def classify_document(self, doc_path: Path) -> DiátaxisCategory:
        """Classify document into Diátaxis category"""
        
    def transform_content(self, content: str, target_category: DiátaxisCategory) -> str:
        """Transform content to match target category standards"""
```

#### Content Classification Rules

```yaml
# migration_rules.yml
classification_rules:
  tutorials:
    patterns:
      - "**/USER_GUIDE.md"
      - "**/getting_started.md"
      - "**/tutorial*.md"
    keywords: ["getting started", "tutorial", "walkthrough", "step by step"]
    
  how_to:
    patterns:
      - "**/BATCH_PROCESSING.md"
      - "**/PERFORMANCE_*.md"
      - "**/how-to/**"
    keywords: ["how to", "guide", "setup", "configure", "optimize"]
    
  reference:
    patterns:
      - "**/API_REFERENCE.md"
      - "**/schemas/**"
      - "**/reference/**"
    keywords: ["api", "reference", "schema", "specification"]
    
  explanations:
    patterns:
      - "**/ARCHITECTURE.md"
      - "**/explanations/**"
    keywords: ["architecture", "concept", "design", "principle"]
```

### 3. Schema Documentation Integration

**Purpose**: Render JSON schemas as interactive documentation

**Custom Plugin Structure**:

```python
class SchemaDocsPlugin(BasePlugin):
    def on_page_markdown(self, markdown: str, page: Page, **kwargs) -> str:
        """Process schema references in markdown"""
        return self._process_schema_blocks(markdown)
    
    def _process_schema_blocks(self, content: str) -> str:
        """Convert schema blocks to interactive documentation"""
        # Transform: ```schema:TenKInsight```
        # Into: Interactive schema documentation with examples
```

**Schema Block Syntax**:

```markdown
```schema:TenKInsight
{
  "description": "Stock analysis insight from 10-K filing",
  "example": {
    "ticker": "AAPL",
    "recommendation": "BUY",
    "confidence": 0.85
  }
}
```

### 4. Navigation System

**Purpose**: Hierarchical navigation following Diátaxis structure

**Navigation Configuration** (`.pages` files):

```yaml
# docs/.pages
nav:
  - index.md
  - Tutorials: tutorials/
  - How-to Guides: how-to/
  - Reference: reference/
  - Explanations: explanations/

# docs/tutorials/.pages
nav:
  - Getting Started: getting_started.md
  - User Guide: user_guide.md
  - Portfolio Analysis: portfolio_analysis_tutorial.md
```

### 5. Build System Integration

**Purpose**: Seamless integration with existing Makefile workflow

**Makefile Targets**:

```makefile
# Documentation targets
docs-install:
 uv add --group docs mkdocs-material mkdocs-awesome-pages-plugin

docs-migrate:
 python scripts/migrate_docs.py --source docs --target docs_new

docs-serve:
 mkdocs serve --dev-addr 127.0.0.1:8000

docs-build:
 mkdocs build --clean

docs-deploy:
 mkdocs gh-deploy --force

docs-validate:
 python scripts/validate_docs.py
 mkdocs build --strict

docs-clean:
 rm -rf site/ docs_new/
```

## Data Models

### Migration Report Model

```python
from pydantic import BaseModel
from typing import List, Dict
from enum import Enum

class DiátaxisCategory(str, Enum):
    TUTORIALS = "tutorials"
    HOW_TO = "how-to"
    REFERENCE = "reference"
    EXPLANATIONS = "explanations"
    ARCHIVE = "archive"  # For deprecated content

class DocumentMigration(BaseModel):
    source_path: str
    target_path: str
    category: DiátaxisCategory
    transformations_applied: List[str]
    validation_status: str
    issues: List[str] = []

class MigrationReport(BaseModel):
    total_documents: int
    migrated_documents: List[DocumentMigration]
    failed_migrations: List[DocumentMigration]
    summary: Dict[DiátaxisCategory, int]
    validation_errors: List[str]
```

### Site Configuration Model

```python
class SiteConfig(BaseModel):
    site_name: str = "FinWiz Documentation"
    site_description: str
    base_url: str
    theme_config: Dict[str, Any]
    navigation_structure: Dict[str, List[str]]
    enabled_plugins: List[str]
    markdown_extensions: List[str]
```

## Content Reorganization Plan

### Current State Analysis

**Existing Structure Issues**:

1. **Scattered Content**: Documentation spread across multiple directories
2. **Mixed Categories**: Files don't follow Diátaxis classification
3. **Duplicate Content**: Similar information in multiple places
4. **Inconsistent Formatting**: Various markdown styles and structures
5. **Broken Links**: Internal references may be outdated
6. **Archive Bloat**: Large archive directory with outdated content

### Target Structure

```
docs/
├── index.md                          # Site homepage
├── tutorials/                        # Learning-oriented
│   ├── getting_started.md           # From USER_GUIDE.md
│   ├── first_analysis.md            # New comprehensive tutorial
│   └── portfolio_analysis.md        # From portfolio_holdings_analysis_user_guide.md
├── how-to/                          # Problem-solving
│   ├── setup_environment.md         # New setup guide
│   ├── batch_processing.md          # From BATCH_PROCESSING.md
│   ├── performance_optimization.md  # From PERFORMANCE_OPTIMIZATION_GUIDE.md
│   ├── memory_management.md         # From MEMORY_MANAGEMENT.md
│   └── template_configuration.md    # From JINJA2_TEMPLATES.md
├── reference/                       # Information-oriented
│   ├── api/                         # API documentation
│   │   ├── crews.md                 # CrewAI crews reference
│   │   ├── tools.md                 # Tools reference
│   │   └── schemas.md               # Schema reference
│   ├── cli_commands.md              # Command line reference
│   ├── configuration.md             # Configuration options
│   └── schemas/                     # JSON schemas with examples
│       ├── index.md                 # Schema overview
│       ├── analysis_schemas.md      # TenKInsight, MarketSentiment, etc.
│       ├── portfolio_schemas.md     # PortfolioReview, HoldingDecision, etc.
│       └── discovery_schemas.md     # APlusDiscoveryResult, etc.
├── explanations/                    # Understanding-oriented
│   ├── architecture.md              # From ARCHITECTURE.md
│   ├── data_flow.md                 # From DATA_QUALITY_AND_FLOW_GUIDE.md
│   ├── deep_analysis.md             # From DEEP_ANALYSIS_INTEGRATION.md
│   ├── report_generation.md         # From REPORT_AGGREGATION_DEVELOPER_GUIDE.md
│   └── design_principles.md         # New conceptual overview
└── archive/                         # Deprecated content (not in navigation)
    └── [existing archive content]
```

### Migration Strategy

#### Phase 1: Content Classification and Migration

1. **Analyze existing content** using automated classification
2. **Migrate core documentation** to new structure
3. **Transform content** to match Diátaxis standards
4. **Validate links** and fix broken references

#### Phase 2: Content Enhancement

1. **Standardize formatting** across all documents
2. **Add missing sections** (prerequisites, next steps, etc.)
3. **Enhance code examples** with proper syntax highlighting
4. **Create new content** to fill gaps

#### Phase 3: Integration and Optimization

1. **Integrate schema documentation** with interactive examples
2. **Optimize navigation** and search functionality
3. **Add cross-references** between related content
4. **Performance optimization** for fast loading

## Error Handling

### Migration Error Handling

```python
class MigrationError(Exception):
    """Base exception for migration errors"""
    pass

class ContentClassificationError(MigrationError):
    """Raised when content cannot be classified"""
    pass

class LinkValidationError(MigrationError):
    """Raised when links cannot be validated or fixed"""
    pass

# Error recovery strategies
def handle_migration_error(error: MigrationError, document: Path) -> None:
    """Handle migration errors with fallback strategies"""
    if isinstance(error, ContentClassificationError):
        # Move to manual review queue
        move_to_manual_review(document)
    elif isinstance(error, LinkValidationError):
        # Log broken links for manual fixing
        log_broken_links(document, error.broken_links)
```

### Build Error Handling

- **Strict mode validation** during CI/CD
- **Graceful degradation** for missing content
- **Detailed error reporting** with file locations
- **Rollback capability** for failed deployments

## Testing Strategy

### Content Validation Tests

```python
def test_diátaxis_compliance():
    """Test that all content follows Diátaxis framework"""
    
def test_link_integrity():
    """Test that all internal links are valid"""
    
def test_schema_examples():
    """Test that all schema examples are valid"""
    
def test_code_examples():
    """Test that code examples are syntactically correct"""
```

### Build System Tests

```python
def test_mkdocs_build():
    """Test that MkDocs builds without errors"""
    
def test_navigation_structure():
    """Test that navigation matches expected structure"""
    
def test_search_functionality():
    """Test that search returns expected results"""
```

### Performance Tests

- **Page load time** < 2 seconds
- **Search response time** < 500ms
- **Build time** < 30 seconds for full site
- **Mobile responsiveness** validation

## Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Set up MkDocs with Material theme
- [ ] Create basic configuration and structure
- [ ] Implement migration scripts
- [ ] Migrate core documentation

### Phase 2: Content Organization (Week 2)

- [ ] Complete content migration and classification
- [ ] Implement schema documentation integration
- [ ] Set up navigation and search
- [ ] Validate and fix all links

### Phase 3: Enhancement (Week 3)

- [ ] Add interactive features and examples
- [ ] Optimize performance and mobile experience
- [ ] Integrate with CI/CD pipeline
- [ ] Comprehensive testing and validation

### Phase 4: Deployment (Week 4)

- [ ] Production deployment setup
- [ ] Documentation for maintenance
- [ ] Training for content creators
- [ ] Monitoring and analytics setup

This design provides a comprehensive approach to reorganizing and optimizing FinWiz documentation while maintaining the existing content and improving accessibility, searchability, and maintainability.
