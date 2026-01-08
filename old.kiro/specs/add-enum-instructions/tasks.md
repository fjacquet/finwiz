# Implementation Plan: Add Enum Instructions to Task Configurations

## Overview

This implementation plan provides a series of discrete, manageable tasks for adding comprehensive enum value instructions to all CrewAI task configuration files in FinWiz. Each task builds incrementally and focuses on specific files and enum fields.

## Task List

- [x] 1. Add enum instructions to ETF crew task configuration
  - Add schema references and enum instructions for ETF market trends task
  - Add enum instructions for ETF screening task
  - Add enum instructions for ETF technical detail task
  - Add enum instructions for ETF risk assessment task
  - Add enum instructions for ETF investment strategy task
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 1.1 Add enum instructions to etf_market_trends_task
  - Add schema reference: "FIRST: Read the schema files docs/schemas/ETFMarketTrend.schema.json"
  - Add REQUIRED ENUM VALUES section with market_sentiment enum
  - Document: "market_sentiment: MUST be one of: 'bullish', 'bearish', 'neutral', 'mixed' (lowercase)"
  - Place enum instructions after main description and before OUTPUT section
  - _Requirements: 1.1, 4.1, 4.2, 4.3, 4.4, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 1.2 Add enum instructions to etf_technical_detail_task
  - Add schema references for ETFTechnicalAnalysis and ETFFactsheet schemas
  - Add REQUIRED ENUM VALUES section with replication_method enum
  - Document: "replication_method: MUST be one of: 'physical', 'synthetic', 'optimized', 'other' (lowercase)"
  - Place enum instructions in dedicated section
  - _Requirements: 1.3, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 1.3 Add enum instructions to etf_risk_assessment_task
  - Add REQUIRED ENUM VALUES section with risk assessment enums
  - Document: "risk_assessment.scale: MUST be one of: '0_5', 'L_M_H', 'L_M_H_VH' (use '0_5' for 0-5 scale)"
  - Document: "risk_assessment.level: MUST be one of: 'Low', 'Medium', 'High', 'Very High' (capitalized)"
  - Use field path notation for nested fields
  - _Requirements: 1.4, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.4, 6.5_

- [x] 2. Add enum instructions to portfolio rebalancing crew task configuration
  - Add enum instructions for analyze holding task
  - Add enum instructions for find alternatives task
  - Add enum instructions for portfolio analysis task
  - Add enum instructions for rebalancing optimization task
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2.1 Add enum instructions to analyze_holding_task
  - Add schema reference for HoldingDecision schema
  - Add REQUIRED ENUM VALUES section with decision, asset_class, grade, and data_freshness enums
  - Document: "decision: MUST be one of: 'KEEP', 'SELL' (uppercase)"
  - Document: "asset_class: MUST be one of: 'stock', 'etf', 'crypto' (lowercase)"
  - Document: "grade: MUST be one of: 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F' (exact format)"
  - Document: "data_freshness: MUST be one of: 'fresh', 'recent', 'stale' (lowercase)"
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 2.2 Add enum instructions to find_alternatives_task
  - Add schema reference for Alternative schema
  - Add REQUIRED ENUM VALUES section with swap_timing enum
  - Document: "swap_timing: MUST be one of: 'immediate', 'gradual', 'tax_optimized' (lowercase with underscore)"
  - Place enum instructions prominently in task description
  - _Requirements: 2.5, 4.1, 4.2, 4.3, 4.4, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 2.3 Add enum instructions to portfolio_analysis_task
  - Add schema reference for PortfolioAnalysis schema
  - Add REQUIRED ENUM VALUES section with sizing_action enum
  - Document: "sizing_action: MUST be one of: 'add', 'trim', 'hold', 'exit' (lowercase)"
  - Ensure consistency with other portfolio tasks
  - _Requirements: 2.6, 4.1, 4.2, 4.3, 4.4, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 2.4 Add enum instructions to rebalancing_optimization_task
  - Add REQUIRED ENUM VALUES section with risk assessment enums
  - Document: "risk_assessment.scale: MUST be '0_5' (for 0-5 scale)"
  - Document: "risk_assessment.level: MUST be one of: 'Low', 'Medium', 'High', 'Very High' (capitalized)"
  - Use consistent format with other crews
  - _Requirements: 2.7, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.4, 6.5_

- [x] 3. Add enum instructions to investment discovery crew task configuration
  - Add enum instructions for ETF discovery task
  - Add enum instructions for stock discovery task
  - Add enum instructions for crypto discovery task
  - Add enum instructions for optimization task
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 3.1 Add enum instructions to etf_discovery_task
  - Add schema reference for APlusDiscoveryResult schema
  - Add REQUIRED ENUM VALUES section with asset_type and grade enums
  - Document: "asset_type: MUST be 'etf' (lowercase)"
  - Document: "grade: MUST be one of: 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F' (exact format, target A+)"
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 3.2 Add enum instructions to stock_discovery_task
  - Add schema reference for APlusDiscoveryResult and MarketRegime schemas
  - Add REQUIRED ENUM VALUES section with market regime enums
  - Document: "regime_type: MUST be one of: 'bull', 'bear', 'sideways', 'volatile' (lowercase)"
  - Document: "interest_rate_trend: MUST be one of: 'rising', 'falling', 'stable' (lowercase)"
  - Document: "market_stress_level: MUST be one of: 'low', 'medium', 'high' (lowercase)"
  - Document: "asset_type: MUST be 'stock' (lowercase)"
  - _Requirements: 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 3.3 Add enum instructions to crypto_discovery_task
  - Add schema reference for APlusDiscoveryResult and PortfolioImprovement schemas
  - Add REQUIRED ENUM VALUES section with improvement and priority enums
  - Document: "improvement_type: MUST be one of: 'replacement', 'addition', 'rebalancing' (lowercase)"
  - Document: "implementation_priority: MUST be one of: 'high', 'medium', 'low' (lowercase)"
  - Document: "asset_type: MUST be 'crypto' (lowercase)"
  - _Requirements: 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4, 6.1, 6.4, 6.5_

- [x] 3.4 Add enum instructions to optimization_task
  - Add REQUIRED ENUM VALUES section with risk assessment enums
  - Document: "risk_assessment.scale: MUST be '0_5' (for 0-5 scale)"
  - Document: "risk_assessment.level: MUST be one of: 'Low', 'Medium', 'High', 'Very High' (capitalized)"
  - Ensure consistency with other crews
  - _Requirements: 3.8, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.4, 6.5_

- [x] 4. Verify enum instruction completeness and consistency
  - Verify all Literal fields from schemas are documented
  - Check format consistency across all task files
  - Verify case sensitivity requirements match schema definitions
  - Verify schema file path references are correct
  - Run manual verification checklist
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 4.1 Verify ETF crew enum completeness
  - Check all enum fields in ETFMarketTrend schema are documented
  - Check all enum fields in ETFFactsheet schema are documented
  - Check all enum fields in ETFTechnicalAnalysis schema are documented
  - Check all enum fields in RiskAssessmentStandardized schema are documented
  - Verify no enum fields are missing
  - _Requirements: 6.1, 6.2_

- [x] 4.2 Verify portfolio rebalancing crew enum completeness
  - Check all enum fields in HoldingDecision schema are documented
  - Check all enum fields in Alternative schema are documented
  - Check all enum fields in PositionSizing schema are documented
  - Check all enum fields in RiskAssessmentStandardized schema are documented
  - Verify no enum fields are missing
  - _Requirements: 6.1, 6.2_

- [x] 4.3 Verify investment discovery crew enum completeness
  - Check all enum fields in APlusDiscoveryResult schema are documented
  - Check all enum fields in MarketRegime schema are documented
  - Check all enum fields in PortfolioImprovement schema are documented
  - Check all enum fields in RiskAssessmentStandardized schema are documented
  - Verify no enum fields are missing
  - _Requirements: 6.1, 6.2_

- [x] 4.4 Verify format consistency across all crews
  - Check all enum instructions use "REQUIRED ENUM VALUES" section header
  - Check all enum instructions use "MUST be one of:" format
  - Check all enum instructions specify case requirements
  - Check all enum instructions are placed after main description
  - Verify consistent formatting across all files
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.5 Verify schema references are correct
  - Check all schema file paths are correct and files exist
  - Check all example file paths are correct and files exist
  - Verify schema references use consistent format
  - Verify schema references are placed at beginning of descriptions
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

---

**Version**: 1.0  
**Created**: 2025-05-10  
**Status**: Draft
