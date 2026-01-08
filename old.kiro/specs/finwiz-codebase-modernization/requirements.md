# Requirements Document

## Introduction

This specification defines a comprehensive modernization of the **entire FinWiz codebase** to address four core issues: overly complex classes, inconsistent testing with mocking, deviations from CrewAI framework patterns, and inconsistent HTML generation practices.

The modernization will systematically refactor all existing code to break down large classes into focused modules under 400 lines (with a stretch goal of 300 lines for critical files), convert all tests to use pytest-mock exclusively, ensure all CrewAI crews follow proper framework patterns, and migrate all HTML generation to use bs4 (BeautifulSoup). This will improve code maintainability, test consistency, and security posture across the entire codebase while preserving all existing functionality.

**Scope:** This is a codebase-wide optimization effort that applies to all existing Python files, tests, crews, and HTML generation code in the FinWiz project.

## Requirements

### Requirement 1: Break Down Large Classes Across Entire Codebase

**User Story:** As a developer, I want all large, complex classes in the existing codebase to be broken into smaller pieces, so that code is easier to read and maintain.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all files exceeding 400 lines SHALL be identified and prioritized for refactoring
2. WHEN files exceed 500 lines THEN they SHALL be refactored with high priority
3. WHEN classes do multiple things THEN they SHALL be split by responsibility
4. WHEN utility functions exist in classes THEN they SHALL be moved to separate modules
5. WHEN classes are refactored THEN each SHALL have a clear, single purpose
6. IF a file cannot be reduced below 400 lines THEN it SHALL be documented why
7. WHEN refactoring is complete THEN no file in the codebase SHALL exceed 400 lines without documented justification (stretch goal: 300 lines for critical files)

### Requirement 2: Migrate All Crews to Follow CrewAI Patterns

**User Story:** As a CrewAI developer, I want all existing crews in the codebase to use proper framework patterns, so that code is consistent and maintainable.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all existing crews SHALL be identified and audited for pattern compliance
2. WHEN defining crews THEN they SHALL use @agent, @task, and @crew decorators
3. WHEN configuring crews THEN they SHALL use agents.yaml and tasks.yaml files
4. WHEN defining agents THEN they SHALL use YAML for roles, goals, and backstories
5. WHEN creating tasks THEN they SHALL have proper expected_output definitions
6. WHEN assigning tools THEN they SHALL use CrewAI's tool injection patterns
7. WHEN migration is complete THEN all crews in the codebase SHALL follow the standard CrewAI structure

### Requirement 3: Convert All Tests to Use pytest-mock

**User Story:** As a developer, I want all existing tests in the codebase to use pytest-mock exclusively, so that mocking is consistent and simple.

#### Acceptance Criteria

1. WHEN analyzing the test suite THEN all tests using unittest.mock SHALL be identified for conversion
2. WHEN writing or modifying tests THEN they SHALL use pytest-mock, never unittest.mock
3. WHEN mocking external calls THEN they SHALL use the mocker fixture
4. WHEN testing async code THEN they SHALL use pytest-asyncio with async mocking
5. WHEN conversion is complete THEN no test file SHALL contain unittest.mock imports or usage
6. WHEN mocking APIs THEN they SHALL mock at the tool level, not HTTP level

### Requirement 4: Migrate All HTML Generation to Use bs4

**User Story:** As a developer, I want all existing HTML generation code in the codebase to use the bs4 package, so that we avoid security risks and enhance code readability.

#### Acceptance Criteria

1. WHEN analyzing the codebase THEN all Python files generating HTML SHALL be identified for migration
2. WHEN generating HTML THEN BeautifulSoup or Tag objects from bs4 SHALL be used exclusively
3. WHEN creating complex HTML structures THEN manual string concatenation (f-strings, +, str.format()) SHALL NOT be used
4. WHEN generating HTML output THEN secure UTF-8 encoding SHALL be used (.prettify(formatter="html") or .encode("utf-8"))
5. WHEN outputting HTML THEN the structure SHALL be correctly indented and well-formed using bs4's formatting methods
6. IF user-supplied data is inserted into HTML THEN bs4's internal escaping mechanisms SHALL be used to prevent XSS vulnerabilities
7. WHEN migration is complete THEN beautifulsoup4 SHALL be declared as a core dependency in pyproject.toml
8. WHEN migration is complete THEN no Python file SHALL use string concatenation for HTML generation
9. WHEN establishing coding standards THEN documentation SHALL explicitly mandate bs4 for HTML generation
