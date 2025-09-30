# Requirements Document

## Introduction

This specification defines a focused modernization of the FinWiz codebase to address three core issues: overly complex classes, inconsistent testing with mocking, and deviations from CrewAI framework patterns.

The modernization will break down large classes, standardize on pytest-mock for all testing, and ensure CrewAI crews follow proper framework patterns. This will improve code readability and maintainability while preserving all existing functionality.

## Requirements

### Requirement 1: Break Down Large Classes

**User Story:** As a developer, I want large, complex classes to be broken into smaller pieces, so that code is easier to read and maintain.

#### Acceptance Criteria

1. WHEN classes exceed 200 lines THEN they SHALL be split into smaller, focused classes
2. WHEN classes do multiple things THEN they SHALL be split by responsibility
3. WHEN utility functions exist in classes THEN they SHALL be moved to separate modules
4. WHEN classes are refactored THEN each SHALL have a clear, single purpose
5. IF a class cannot be split THEN it SHALL be documented why

### Requirement 2: Follow CrewAI Patterns

**User Story:** As a CrewAI developer, I want all crews to use proper framework patterns, so that code is consistent and maintainable.

#### Acceptance Criteria

1. WHEN defining crews THEN they SHALL use @agent, @task, and @crew decorators
2. WHEN configuring crews THEN they SHALL use agents.yaml and tasks.yaml files
3. WHEN defining agents THEN they SHALL use YAML for roles, goals, and backstories
4. WHEN creating tasks THEN they SHALL have proper expected_output definitions
5. WHEN assigning tools THEN they SHALL use CrewAI's tool injection patterns

### Requirement 3: Use pytest-mock Consistently

**User Story:** As a developer, I want all tests to use pytest-mock, so that mocking is consistent and simple.

#### Acceptance Criteria

1. WHEN writing tests THEN they SHALL use pytest-mock, never unittest.mock
2. WHEN mocking external calls THEN they SHALL use the mocker fixture
3. WHEN testing async code THEN they SHALL use pytest-asyncio with async mocking
4. WHEN existing tests use unittest.mock THEN they SHALL be converted to pytest-mock
5. WHEN mocking APIs THEN they SHALL mock at the tool level, not HTTP level



