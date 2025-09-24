# Implementation Plan

- [x] 1. Manual Crew Configuration Audit
  - Review current crew implementations to identify missing CrewAI features and tool usage gaps
  - Document findings in a simple audit report for each crew
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 1.1 Audit Stock Crew Configuration
  - Check if Stock crew agents have all required tools (Quantitative Analysis, Enhanced SEC Analysis, Ticker Validation, RAG tools)
  - Verify task configurations use appropriate CrewAI features (async_execution, output specifications)
  - Document missing tools and CrewAI features in stock crew
  - _Requirements: 1.1_

- [x] 1.2 Audit ETF Crew Configuration  
  - Check if ETF crew agents have all required tools (Quantitative Analysis, Enhanced ETF Analysis, Ticker Validation, RAG tools)
  - Verify task configurations use appropriate CrewAI features (async_execution, output specifications)
  - Document missing tools and CrewAI features in ETF crew
  - _Requirements: 1.1_

- [x] 1.3 Audit Crypto Crew Configuration
  - Check if Crypto crew agents have all required tools (Quantitative Analysis, Enhanced Crypto Analysis, CoinMarketCap tools, RAG tools)
  - Verify task configurations use appropriate CrewAI features (async_execution, output specifications)
  - Document missing tools and CrewAI features in crypto crew
  - _Requirements: 1.1_

- [x] 1.4 Audit Portfolio Rebalancing Crew Configuration
  - Check if Portfolio Rebalancing crew agents have all required tools (Portfolio Rebalancing Tool, Quantitative Analysis, RAG tools)
  - Verify task configurations use appropriate CrewAI features
  - Document missing tools and CrewAI features in portfolio rebalancing crew
  - _Requirements: 1.1_

- [x] 1.5 Audit Report Crew Configuration
  - Verify Report crew follows tool restriction policy (investment reporter has no tools)
  - Check if Report crew uses existing ToolRestrictionValidator properly
  - Verify translation task implementation across all crews
  - Document tool restriction compliance and translation gaps
  - _Requirements: 4.1, 5.1_

- [x] 2. Fix Essential Tool Usage Gaps
  - Update crew configurations to include missing essential tools identified in audit
  - Ensure all crews use required analysis tools for their asset class
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 2.1 Update Stock Crew Tool Configuration
  - Add missing tools to Stock crew agent configurations (if any found in audit)
  - Ensure Quantitative Analysis Tool is properly configured with asset_class="stock"
  - Verify Enhanced SEC Analysis Tool integration for 10-K extraction
  - Update agent tool lists in stock_crew.py
  - _Requirements: 1.2_

- [x] 2.2 Update ETF Crew Tool Configuration
  - Add missing tools to ETF crew agent configurations (if any found in audit)
  - Ensure Enhanced ETF Analysis Tool is properly integrated for factsheet extraction
  - Verify Quantitative Analysis Tool configuration with asset_class="etf"
  - Update agent tool lists in etf_crew.py
  - _Requirements: 1.2_

- [x] 2.3 Update Crypto Crew Tool Configuration
  - Add missing tools to Crypto crew agent configurations (if any found in audit)
  - Ensure Enhanced Crypto Analysis Tool and CoinMarketCap tools are properly integrated
  - Verify Quantitative Analysis Tool configuration with asset_class="crypto"
  - Update agent tool lists in crypto_crew.py
  - _Requirements: 1.2_

- [x] 2.4 Update Portfolio Rebalancing Crew Tool Configuration
  - Add missing tools to Portfolio Rebalancing crew agent configurations (if any found in audit)
  - Ensure Portfolio Rebalancing Tool and Portfolio Price Service are properly integrated
  - Verify Quantitative Analysis Tool configuration for portfolio optimization
  - Update agent tool lists in portfolio_rebalancing_crew.py
  - _Requirements: 1.2_

- [x] 3. Implement CrewAI Output Validation Features
  - Update task configurations to use CrewAI's built-in output validation features
  - Integrate existing FinWiz Pydantic schemas with CrewAI output_pydantic feature
  - _Requirements: 2.2, 2.3_

- [x] 3.1 Add Output Pydantic Validation to Stock Crew Tasks
  - Update stock crew task YAML configurations to include output_pydantic specifications
  - Use existing FinWiz schemas (TenKInsight, MarketSentiment, RiskAssessmentStandardized)
  - Add output_json: true for tasks that should generate machine-readable appendices
  - Test that CrewAI properly validates outputs against schemas
  - _Requirements: 2.2_

- [x] 3.2 Add Output Pydantic Validation to ETF Crew Tasks
  - Update ETF crew task YAML configurations to include output_pydantic specifications
  - Use existing FinWiz schemas (ETFFactsheet, ETFTopHolding, RiskAssessmentStandardized)
  - Add output_json: true for tasks that should generate machine-readable appendices
  - Test that CrewAI properly validates outputs against schemas
  - _Requirements: 2.2_

- [x] 3.3 Add Output Pydantic Validation to Crypto Crew Tasks
  - Update crypto crew task YAML configurations to include output_pydantic specifications
  - Use existing FinWiz schemas (CryptoThesis, RiskAssessmentStandardized)
  - Add output_json: true for tasks that should generate machine-readable appendices
  - Test that CrewAI properly validates outputs against schemas
  - _Requirements: 2.2_

- [x] 3.4 Add Output Pydantic Validation to Portfolio Rebalancing Crew Tasks
  - Update portfolio rebalancing crew task YAML configurations to include output_pydantic specifications
  - Use existing FinWiz schemas (PortfolioReview, RiskAssessmentStandardized)
  - Add output_json: true for tasks that should generate machine-readable appendices
  - Test that CrewAI properly validates outputs against schemas
  - _Requirements: 2.2_

- [x] 4. Standardize Risk Assessment Implementation
  - Ensure all crews use consistent risk scoring methodology and generate standardized risk objects
  - Verify integration with existing Standardized Risk Scoring Tool
  - _Requirements: 3.2, 3.3_

- [x] 4.1 Implement Standardized Risk Assessment in Stock Crew
  - Verify Stock crew uses Standardized Risk Scoring Tool methodology
  - Ensure RiskAssessmentStandardized objects are generated with proper 0-5 scale scoring
  - Update task configurations to include risk assessment requirements
  - Test risk assessment output compliance with schema
  - _Requirements: 3.2_

- [x] 4.2 Implement Standardized Risk Assessment in ETF Crew
  - Verify ETF crew uses Standardized Risk Scoring Tool methodology
  - Ensure RiskAssessmentStandardized objects are generated with proper 0-5 scale scoring
  - Update task configurations to include risk assessment requirements
  - Test risk assessment output compliance with schema
  - _Requirements: 3.2_

- [x] 4.3 Implement Standardized Risk Assessment in Crypto Crew
  - Verify Crypto crew uses Standardized Risk Scoring Tool methodology
  - Ensure RiskAssessmentStandardized objects are generated with proper 0-5 scale scoring
  - Update task configurations to include risk assessment requirements
  - Test risk assessment output compliance with schema
  - _Requirements: 3.2_

- [ ] 5. Enforce Report Crew Tool Restrictions
  - Verify Report crew follows established tool restriction policy using existing validation systems
  - Ensure investment reporter agent has empty tools list
  - _Requirements: 4.2, 4.3_

- [x] 5.1 Validate Report Crew Tool Restrictions
  - Verify investment reporter agent in Report crew has empty tools list
  - Ensure ToolRestrictionValidator is properly integrated in Report crew initialization
  - Test that tool restriction violations are properly detected and prevented
  - Update Report crew configuration if violations are found
  - _Requirements: 4.2_

- [x] 5.2 Implement ReporterInputValidator Integration
  - Verify Report crew uses ReporterInputValidator for upstream context validation
  - Ensure proper integration with existing validation systems
  - Test that invalid reporter input is properly detected and handled
  - Update Report crew validation logic if needed
  - _Requirements: 4.3_

- [x] 6. Add Missing Translation Tasks
  - Ensure all crews have consistent translation task implementation
  - Verify translation agents follow established pattern (no tools, HTML preservation)
  - _Requirements: 5.2, 5.3_

- [x] 6.1 Audit Translation Task Implementation Across Crews
  - Check which crews are missing translation tasks
  - Verify existing translation tasks follow proper pattern (no tools, HTML structure preservation)
  - Document gaps in translation task implementation
  - _Requirements: 5.2_

- [x] 6.2 Add Missing Translation Tasks
  - Add translation tasks to crews that are missing them (if any found in audit)
  - Ensure translation agents have no tools and only consume upstream HTML context
  - Use existing translation task pattern from crews that already have it
  - Update crew task configurations and agent definitions
  - _Requirements: 5.3_

- [x] 7. Optimize CrewAI Performance Features
  - Enable appropriate CrewAI performance features like async_execution for I/O-bound tasks
  - Configure crew-level performance settings
  - _Requirements: Performance optimization_

- [x] 7.1 Enable Async Execution for I/O-Bound Tasks
  - Review current task configurations and identify I/O-bound tasks that can run in parallel
  - Add async_execution=True to appropriate tasks in all crew YAML configurations
  - Ensure final tasks in sequential workflows remain synchronous per CrewAI requirements
  - Test that async execution works properly and improves performance
  - _Requirements: Performance optimization_

- [x] 7.2 Configure Crew-Level Performance Settings
  - Review and optimize crew-level configuration settings (max_rpm, respect_context_window)
  - Ensure all crews use consistent performance configuration
  - Add any missing CrewAI performance features that would benefit FinWiz
  - Test that performance settings work as expected
  - _Requirements: Performance optimization_

- [x] 8. Testing and Validation
  - Test all configuration changes to ensure no regressions
  - Validate that crews properly use assigned tools and generate compliant outputs
  - _Requirements: All requirements validation_

- [x] 8.1 Test Crew Configuration Changes
  - Run existing FinWiz test suite to ensure no regressions from configuration changes
  - Test each crew individually to verify proper tool usage
  - Validate that CrewAI output validation features work correctly
  - Fix any issues found during testing
  - _Requirements: All requirements validation_

- [x] 8.2 Validate Output Schema Compliance
  - Test that all crews generate proper JSON appendices matching FinWiz schemas
  - Verify that CrewAI output_pydantic validation works as expected
  - Check that risk assessment objects follow standardized format across all crews
  - Document any remaining schema compliance issues
  - _Requirements: 2.3, 3.3_

- [x] 8.3 Performance Impact Assessment
  - Measure execution times before and after configuration changes
  - Verify that async execution improvements provide expected performance benefits
  - Ensure that additional validation doesn't significantly impact performance
  - Document performance impact and any optimization recommendations
  - _Requirements: Performance validation_

- [x] 9. Documentation and Cleanup
  - Update documentation to reflect proper CrewAI feature usage
  - Clean up any temporary files or configurations used during implementation
  - _Requirements: Documentation and maintenance_

- [x] 9.1 Update CrewAI Feature Usage Documentation
  - Document proper CrewAI feature usage patterns established during implementation
  - Update crew configuration documentation with examples of proper tool assignment
  - Document output validation patterns and schema integration
  - Create troubleshooting guide for common CrewAI configuration issues
  - _Requirements: Documentation_

- [x] 9.2 Create Feature Usage Compliance Checklist
  - Create simple checklist for future crew development to ensure proper feature usage
  - Document minimum required tools for each crew type
  - Provide examples of proper CrewAI task and agent configuration
  - Include validation steps to verify compliance
  - _Requirements: Maintenance procedures_