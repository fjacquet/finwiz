# Services Module

This directory contains business service classes that coordinate complex operations across multiple components.

## Directory Structure

```
services/
└── __init__.py
```

## Purpose

This module is reserved for business service classes that coordinate operations across multiple domain components. Services should orchestrate complex workflows but delegate business logic to domain modules.

## Service Design Principles

1. **Thin Orchestration**: Services coordinate, don't contain business logic
2. **Dependency Injection**: Accept dependencies via constructor
3. **Stateless**: Services should be stateless where possible
4. **Interface-Based**: Define clear interfaces for external dependencies

## Related Modules

- `finwiz.orchestrators` - Flow orchestration
- `finwiz.flows` - CrewAI flow definitions
- `finwiz.crews` - AI agent crews
