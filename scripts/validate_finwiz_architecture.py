#!/usr/bin/env python3
"""
FinWiz Architecture Validation Script

Validates compliance with all 13 requirements from the architectural consolidation.
Generates a comprehensive markdown report with pass/fail status and remediation steps.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    message: str
    requirement_refs: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    details: List[str] = field(default_factory=list)


class FinWizArchitectureValidator:
    """Validates FinWiz architecture against all requirements."""
    
    def __init__(self, project_root: Path = None):
        """Initialize validator with project root directory."""
        self.project_root = project_root or Path.cwd()
        self.results: List[ValidationResult] = []
        
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks and return results."""
        print("🔍 Starting FinWiz Architecture Validation...\n")
        
        # Phase 1: DeepAnalysisCrew validation
        print("📋 Phase 1: DeepAnalysisCrew Validation")
        self._validate_deep_analysis_crew_exists()
        self._validate_dynamic_tool_routing()
        self._validate_deep_analysis_result_schema()
        
        # Phase 2: Flow orchestration validation
        print("\n📋 Phase 2: Flow Orchestration Validation")
        self._validate_flow_sequence()
        self._validate_atomic_operations()
        self._validate_listener_dependencies()
        
        # Phase 3: Discovery crew task descriptions
        print("\n📋 Phase 3: Discovery Crew Task Descriptions")
        self._validate_discovery_task_descriptions()
        
        # Phase 4: Enum documentation
        print("\n📋 Phase 4: Enum Documentation")
        self._validate_enum_documentation()
        
        # Phase 5: Test framework
        print("\n📋 Phase 5: Test Framework Validation")
        self._validate_test_framework()
        
        # Phase 6: File size validation
        print("\n📋 Phase 6: File Size Validation")
        self._validate_file_sizes()
        
        # Phase 7: HTML generation
        print("\n📋 Phase 7: HTML Generation Validation")
        self._validate_html_generation()
        
        # Phase 8: ReportCrew tools
        print("\n📋 Phase 8: ReportCrew Tools Validation")
        self._validate_report_crew_tools()
        
        # Phase 9: Feature flags documentation
        print("\n📋 Phase 9: Feature Flags Documentation")
        self._validate_feature_flags_documentation()
        
        print("\n✅ Validation complete!\n")
        return self.results

    def _add_result(self, result: ValidationResult):
        """Add a validation result and print status."""
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  {status}: {result.check_name}")
        if not result.passed and result.details:
            for detail in result.details[:3]:  # Show first 3 details
                print(f"    - {detail}")
    
    # ========================================================================
    # DeepAnalysisCrew Validation (Requirements 1.1-1.5)
    # ========================================================================
    
    def _validate_deep_analysis_crew_exists(self):
        """Check that DeepAnalysisCrew exists at expected location."""
        crew_path = self.project_root / "src/finwiz/crews/deep_analysis"
        crew_file = crew_path / "deep_analysis.py"
        
        if crew_path.exists() and crew_file.exists():
            self._add_result(ValidationResult(
                check_name="DeepAnalysisCrew exists",
                passed=True,
                message=f"Found DeepAnalysisCrew at {crew_path}",
                requirement_refs=["1.1", "1.2", "1.3", "1.4"]
            ))
        else:
            self._add_result(ValidationResult(
                check_name="DeepAnalysisCrew exists",
                passed=False,
                message=f"DeepAnalysisCrew not found at {crew_path}",
                requirement_refs=["1.1", "1.2", "1.3", "1.4"],
                remediation="Create DeepAnalysisCrew at src/finwiz/crews/deep_analysis/",
                details=[f"Expected path: {crew_file}"]
            ))
    
    def _validate_dynamic_tool_routing(self):
        """Check that DeepAnalysisCrew implements dynamic tool routing."""
        crew_file = self.project_root / "src/finwiz/crews/deep_analysis/deep_analysis.py"
        
        if not crew_file.exists():
            self._add_result(ValidationResult(
                check_name="Dynamic tool routing",
                passed=False,
                message="Cannot validate - DeepAnalysisCrew file not found",
                requirement_refs=["1.2", "1.3", "1.4"],
                remediation="Create DeepAnalysisCrew first"
            ))
            return
        
        content = crew_file.read_text()
        
        # Check for get_tools_for_asset_class method
        has_method = "get_tools_for_asset_class" in content
        
        # Check for asset class routing (multiple patterns)
        has_stock_routing = ('asset_class.lower() == "stock"' in content or 
                           'asset_class == "stock"' in content or
                           'asset_class_lower == "stock"' in content)
        has_etf_routing = ('asset_class.lower() == "etf"' in content or 
                         'asset_class == "etf"' in content or
                         'asset_class_lower == "etf"' in content)
        has_crypto_routing = ('asset_class.lower() == "crypto"' in content or 
                            'asset_class == "crypto"' in content or
                            'asset_class_lower == "crypto"' in content)
        
        passed = has_method and has_stock_routing and has_etf_routing and has_crypto_routing
        
        details = []
        if not has_method:
            details.append("Missing get_tools_for_asset_class() method")
        if not has_stock_routing:
            details.append("Missing stock asset class routing")
        if not has_etf_routing:
            details.append("Missing ETF asset class routing")
        if not has_crypto_routing:
            details.append("Missing crypto asset class routing")
        
        self._add_result(ValidationResult(
            check_name="Dynamic tool routing",
            passed=passed,
            message="DeepAnalysisCrew implements dynamic tool routing" if passed else \
                   "DeepAnalysisCrew missing dynamic tool routing",
            requirement_refs=["1.2", "1.3", "1.4"],
            remediation="Implement get_tools_for_asset_class() with stock/etf/crypto routing" \
                       if not passed else None,
            details=details
        ))
    
    def _validate_deep_analysis_result_schema(self):
        """Check that DeepAnalysisResult schema has all required fields."""
        # Check in flow_state.py (actual location)
        schema_file = self.project_root / "src/finwiz/flow_state.py"
        
        if not schema_file.exists():
            self._add_result(ValidationResult(
                check_name="DeepAnalysisResult schema",
                passed=False,
                message="DeepAnalysisResult schema file not found",
                requirement_refs=["1.5"],
                remediation="Create DeepAnalysisResult schema in flow_state.py",
                details=[f"Expected path: {schema_file}"]
            ))
            return
        
        content = schema_file.read_text()
        
        # Required fields
        required_fields = [
            "ticker",
            "asset_class",
            "fundamental_score",
            "technical_score",
            "risk_score",
            "composite_score",
            "grade",
            "analysis_timestamp",
            "data_freshness_hours",
            "confidence_level",
            "warnings"
        ]
        
        # Check for extra='forbid' (multiple patterns)
        has_extra_forbid = ('extra="forbid"' in content or 
                          "extra='forbid'" in content or 
                          'extra: "forbid"' in content or 
                          "extra: 'forbid'" in content or
                          '"extra": "forbid"' in content or
                          "'extra': 'forbid'" in content)
        
        missing_fields = []
        for field in required_fields:
            if f"{field}:" not in content and f"{field} =" not in content:
                missing_fields.append(field)
        
        passed = len(missing_fields) == 0 and has_extra_forbid
        
        details = []
        if missing_fields:
            details.append(f"Missing fields: {', '.join(missing_fields)}")
        if not has_extra_forbid:
            details.append("Missing extra='forbid' in model_config")
        
        self._add_result(ValidationResult(
            check_name="DeepAnalysisResult schema",
            passed=passed,
            message="DeepAnalysisResult has all required fields" if passed else \
                   "DeepAnalysisResult missing required fields",
            requirement_refs=["1.5"],
            remediation="Add missing fields and extra='forbid' to DeepAnalysisResult" \
                       if not passed else None,
            details=details
        ))

    # ========================================================================
    # Flow Orchestration Validation (Requirements 2.1-2.10)
    # ========================================================================
    
    def _validate_flow_sequence(self):
        """Verify flow sequence matches business logic."""
        flow_file = self.project_root / "src/finwiz/flows/flow_orchestrator.py"
        
        if not flow_file.exists():
            self._add_result(ValidationResult(
                check_name="Flow sequence",
                passed=False,
                message="Flow orchestrator file not found",
                requirement_refs=["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"],
                remediation="Create flow orchestrator at src/finwiz/flows/flow_orchestrator.py"
            ))
            return
        
        content = flow_file.read_text()
        
        # Check for correct listener sequence
        checks = [
            ('@start()', 'validate_data_integration'),
            ('@listen("validate_data_integration")', 'check_portfolio'),
            ('@listen("check_portfolio")', 'analyze_and_update_portfolio'),
            ('@listen("analyze_and_update_portfolio")', 'check_stock'),
            ('@listen("analyze_and_update_portfolio")', 'check_etf'),
            ('@listen("analyze_and_update_portfolio")', 'check_crypto'),
            ('check_investment_discovery', 'discovery consolidation'),
            ('check_portfolio_rebalancing', 'rebalancing'),
            ('report', 'final report')
        ]
        
        passed = True
        details = []
        
        # Check for validate_data_integration as start
        if '@start()' in content and 'def validate_data_integration' in content:
            pass
        else:
            passed = False
            details.append("validate_data_integration not marked as @start()")
        
        # Check for check_portfolio listening to validate_data_integration
        if '@listen("validate_data_integration")' in content and \
           'def check_portfolio' in content:
            pass
        else:
            passed = False
            details.append("check_portfolio not listening to validate_data_integration")
        
        # Check for analyze_and_update_portfolio listening to check_portfolio
        if '@listen("check_portfolio")' in content and \
           'def analyze_and_update_portfolio' in content:
            pass
        else:
            passed = False
            details.append("analyze_and_update_portfolio not listening to check_portfolio")
        
        # Check for discovery crews listening to analyze_and_update_portfolio
        discovery_checks = [
            ('check_stock', '@listen("analyze_and_update_portfolio")'),
            ('check_etf', '@listen("analyze_and_update_portfolio")'),
            ('check_crypto', '@listen("analyze_and_update_portfolio")')
        ]
        
        for crew_method, listener in discovery_checks:
            if listener in content and f'def {crew_method}' in content:
                pass
            else:
                passed = False
                details.append(f"{crew_method} not listening to analyze_and_update_portfolio")
        
        self._add_result(ValidationResult(
            check_name="Flow sequence",
            passed=passed,
            message="Flow sequence matches business logic" if passed else \
                   "Flow sequence does not match expected order",
            requirement_refs=["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"],
            remediation="Update flow listeners to match: validate → portfolio → deep analysis → " \
                       "discovery → rebalancing → report" if not passed else None,
            details=details
        ))
    
    def _validate_atomic_operations(self):
        """Check that analyze_and_update_portfolio is atomic."""
        flow_file = self.project_root / "src/finwiz/flows/flow_orchestrator.py"
        
        if not flow_file.exists():
            self._add_result(ValidationResult(
                check_name="Atomic operations",
                passed=False,
                message="Flow orchestrator file not found",
                requirement_refs=["2.8"],
                remediation="Create flow orchestrator first"
            ))
            return
        
        content = flow_file.read_text()
        
        # Check for analyze_and_update_portfolio method
        has_method = 'def analyze_and_update_portfolio' in content
        
        # Check that it's a single method (not split into multiple)
        # Look for the method and check it contains deep analysis, alternatives, and update
        if has_method:
            # Extract method content
            method_start = content.find('def analyze_and_update_portfolio')
            if method_start != -1:
                # Find next method definition
                next_method = content.find('\n    def ', method_start + 1)
                if next_method == -1:
                    next_method = len(content)
                
                method_content = content[method_start:next_method]
                
                # Check for key operations
                has_deep_analysis = 'deep_analysis' in method_content.lower()
                has_alternatives = 'alternative' in method_content.lower()
                has_update = 'update' in method_content.lower() or \
                            'portfolio_review' in method_content.lower()
                
                passed = has_deep_analysis and has_alternatives and has_update
                
                details = []
                if not has_deep_analysis:
                    details.append("Missing deep analysis operation")
                if not has_alternatives:
                    details.append("Missing alternatives matching")
                if not has_update:
                    details.append("Missing portfolio update")
            else:
                passed = False
                details = ["Could not parse method content"]
        else:
            passed = False
            details = ["analyze_and_update_portfolio method not found"]
        
        self._add_result(ValidationResult(
            check_name="Atomic operations",
            passed=passed,
            message="analyze_and_update_portfolio is atomic" if passed else \
                   "analyze_and_update_portfolio is not atomic",
            requirement_refs=["2.8"],
            remediation="Consolidate deep analysis, alternatives, and update into single method" \
                       if not passed else None,
            details=details
        ))
    
    def _validate_listener_dependencies(self):
        """Verify listener dependencies are correct."""
        flow_file = self.project_root / "src/finwiz/flows/flow_orchestrator.py"
        
        if not flow_file.exists():
            self._add_result(ValidationResult(
                check_name="Listener dependencies",
                passed=False,
                message="Flow orchestrator file not found",
                requirement_refs=["2.9", "2.10"],
                remediation="Create flow orchestrator first"
            ))
            return
        
        content = flow_file.read_text()
        
        # Check that discovery crews listen to analyze_and_update_portfolio
        discovery_correct = (
            '@listen("analyze_and_update_portfolio")' in content and
            'def check_stock' in content and
            'def check_etf' in content and
            'def check_crypto' in content
        )
        
        # Check that rebalancing listens to check_investment_discovery
        rebalancing_correct = (
            'check_investment_discovery' in content and
            'check_portfolio_rebalancing' in content
        )
        
        passed = discovery_correct and rebalancing_correct
        
        details = []
        if not discovery_correct:
            details.append("Discovery crews not listening to analyze_and_update_portfolio")
        if not rebalancing_correct:
            details.append("Rebalancing not listening to check_investment_discovery")
        
        self._add_result(ValidationResult(
            check_name="Listener dependencies",
            passed=passed,
            message="Listener dependencies are correct" if passed else \
                   "Listener dependencies are incorrect",
            requirement_refs=["2.9", "2.10"],
            remediation="Update listeners: discovery after analyze_and_update_portfolio, " \
                       "rebalancing after check_investment_discovery" if not passed else None,
            details=details
        ))

    # ========================================================================
    # Discovery Crew Task Descriptions (Requirements 1.6, 1.7, 1.8)
    # ========================================================================
    
    def _validate_discovery_task_descriptions(self):
        """Verify discovery crew task descriptions mention 'top 10'."""
        crews = [
            ("stock_crew", "1.6"),
            ("etf_crew", "1.7"),
            ("crypto_crew", "1.8")
        ]
        
        for crew_name, req_ref in crews:
            tasks_file = self.project_root / f"src/finwiz/crews/{crew_name}/config/tasks.yaml"
            
            if not tasks_file.exists():
                self._add_result(ValidationResult(
                    check_name=f"{crew_name} task description",
                    passed=False,
                    message=f"{crew_name} tasks.yaml not found",
                    requirement_refs=[req_ref],
                    remediation=f"Create tasks.yaml for {crew_name}",
                    details=[f"Expected path: {tasks_file}"]
                ))
                continue
            
            content = tasks_file.read_text().lower()
            
            # Check for "top 10" or "screen and identify" language
            has_top_10 = "top 10" in content or "top10" in content or "top-10" in content
            has_screen = "screen" in content and "identify" in content
            
            passed = has_top_10 or has_screen
            
            details = []
            if not passed:
                details.append("Missing 'top 10' or 'screen and identify' language")
            
            self._add_result(ValidationResult(
                check_name=f"{crew_name} task description",
                passed=passed,
                message=f"{crew_name} has correct task description" if passed else \
                       f"{crew_name} missing 'top 10' language",
                requirement_refs=[req_ref],
                remediation=f"Add 'screen and identify top 10' to {crew_name} task descriptions" \
                           if not passed else None,
                details=details
            ))
    
    # ========================================================================
    # Enum Documentation (Requirement 4.18)
    # ========================================================================
    
    def _validate_enum_documentation(self):
        """Verify all tasks.yaml files have REQUIRED ENUM VALUES section."""
        crews_dir = self.project_root / "src/finwiz/crews"
        
        if not crews_dir.exists():
            self._add_result(ValidationResult(
                check_name="Enum documentation",
                passed=False,
                message="Crews directory not found",
                requirement_refs=["4.18"],
                remediation="Create crews directory structure"
            ))
            return
        
        # Find all tasks.yaml files
        tasks_files = list(crews_dir.rglob("config/tasks.yaml"))
        
        if not tasks_files:
            self._add_result(ValidationResult(
                check_name="Enum documentation",
                passed=False,
                message="No tasks.yaml files found",
                requirement_refs=["4.18"],
                remediation="Create tasks.yaml files for crews"
            ))
            return
        
        missing_enum_docs = []
        
        for tasks_file in tasks_files:
            content = tasks_file.read_text()
            
            # Check for REQUIRED ENUM VALUES section
            has_enum_section = "REQUIRED ENUM VALUES" in content or \
                              "Required Enum Values" in content or \
                              "required enum values" in content
            
            if not has_enum_section:
                crew_name = tasks_file.parent.parent.name
                missing_enum_docs.append(crew_name)
        
        passed = len(missing_enum_docs) == 0
        
        self._add_result(ValidationResult(
            check_name="Enum documentation",
            passed=passed,
            message=f"All {len(tasks_files)} tasks.yaml files have enum documentation" \
                   if passed else \
                   f"{len(missing_enum_docs)} tasks.yaml files missing enum documentation",
            requirement_refs=["4.18"],
            remediation="Add 'REQUIRED ENUM VALUES' section to all tasks.yaml files" \
                       if not passed else None,
            details=[f"Missing in: {crew}" for crew in missing_enum_docs]
        ))
    
    # ========================================================================
    # Test Framework (Requirements 6.7, 6.8, 6.9)
    # ========================================================================
    
    def _validate_test_framework(self):
        """Verify only pytest-mock is used, not unittest.mock."""
        tests_dir = self.project_root / "tests"
        
        if not tests_dir.exists():
            self._add_result(ValidationResult(
                check_name="Test framework",
                passed=False,
                message="Tests directory not found",
                requirement_refs=["6.7", "6.8", "6.9"],
                remediation="Create tests directory"
            ))
            return
        
        # Find all test files
        test_files = list(tests_dir.rglob("test_*.py"))
        
        if not test_files:
            self._add_result(ValidationResult(
                check_name="Test framework",
                passed=False,
                message="No test files found",
                requirement_refs=["6.7", "6.8", "6.9"],
                remediation="Create test files"
            ))
            return
        
        violations = []
        
        for test_file in test_files:
            content = test_file.read_text()
            
            # Check for unittest.mock imports
            if "unittest.mock" in content or "from unittest import mock" in content:
                # Find line numbers
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if "unittest.mock" in line or "from unittest import mock" in line:
                        rel_path = test_file.relative_to(self.project_root)
                        violations.append(f"{rel_path}:{i}")
        
        passed = len(violations) == 0
        
        self._add_result(ValidationResult(
            check_name="Test framework",
            passed=passed,
            message=f"All {len(test_files)} test files use pytest-mock" if passed else \
                   f"Found {len(violations)} unittest.mock violations",
            requirement_refs=["6.7", "6.8", "6.9"],
            remediation="Replace unittest.mock with pytest-mock (mocker fixture)" \
                       if not passed else None,
            details=violations[:10]  # Show first 10 violations
        ))

    # ========================================================================
    # File Size Validation (Requirements 6.10, 6.11)
    # ========================================================================
    
    def _validate_file_sizes(self):
        """Verify no Python files exceed 400 lines."""
        src_dir = self.project_root / "src/finwiz"
        
        if not src_dir.exists():
            self._add_result(ValidationResult(
                check_name="File sizes",
                passed=False,
                message="Source directory not found",
                requirement_refs=["6.10", "6.11"],
                remediation="Create src/finwiz directory"
            ))
            return
        
        # Find all Python files
        py_files = list(src_dir.rglob("*.py"))
        
        if not py_files:
            self._add_result(ValidationResult(
                check_name="File sizes",
                passed=False,
                message="No Python files found",
                requirement_refs=["6.10", "6.11"],
                remediation="Create Python source files"
            ))
            return
        
        oversized_files = []
        
        for py_file in py_files:
            # Skip __init__.py files
            if py_file.name == "__init__.py":
                continue
            
            lines = py_file.read_text().split('\n')
            line_count = len(lines)
            
            if line_count > 400:
                rel_path = py_file.relative_to(self.project_root)
                oversized_files.append(f"{rel_path} ({line_count} lines)")
        
        passed = len(oversized_files) == 0
        
        self._add_result(ValidationResult(
            check_name="File sizes",
            passed=passed,
            message=f"All {len(py_files)} Python files under 400 lines" if passed else \
                   f"Found {len(oversized_files)} files exceeding 400 lines",
            requirement_refs=["6.10", "6.11"],
            remediation="Refactor oversized files into smaller modules" if not passed else None,
            details=oversized_files[:10]  # Show first 10 oversized files
        ))
    
    # ========================================================================
    # HTML Generation (Requirements 6.12, 6.13)
    # ========================================================================
    
    def _validate_html_generation(self):
        """Verify HTML generation uses BeautifulSoup, not string concatenation."""
        src_dir = self.project_root / "src/finwiz"
        
        if not src_dir.exists():
            self._add_result(ValidationResult(
                check_name="HTML generation",
                passed=False,
                message="Source directory not found",
                requirement_refs=["6.12", "6.13"],
                remediation="Create src/finwiz directory"
            ))
            return
        
        # Find files that generate HTML
        py_files = list(src_dir.rglob("*.py"))
        
        html_generators = []
        string_concat_violations = []
        bs4_usage = []
        
        for py_file in py_files:
            content = py_file.read_text()
            
            # Check if file generates HTML (be specific to avoid false positives)
            # Look for actual HTML generation, not just imports or references
            generates_html = (
                ("<html" in content.lower() and ("f\"" in content or "f'" in content)) or
                ("<!doctype html>" in content.lower()) or
                ("<div" in content and ("f\"" in content or "f'" in content)) or
                ("<table" in content and ("f\"" in content or "f'" in content)) or
                ("<body" in content and ("f\"" in content or "f'" in content))
            )
            
            if generates_html:
                rel_path = py_file.relative_to(self.project_root)
                html_generators.append(str(rel_path))
                
                # Check for BeautifulSoup usage
                uses_bs4 = (
                    "from bs4 import" in content or
                    "import bs4" in content or
                    "BeautifulSoup" in content
                )
                
                if uses_bs4:
                    bs4_usage.append(str(rel_path))
                
                # Check for string concatenation patterns (anti-pattern)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Look for HTML string concatenation
                    if (('<' in line and '>' in line and '+' in line) or
                        ('f"<' in line or "f'<" in line) or
                        ('f"""<' in line or "f'''<" in line)):
                        # Exclude comments and docstrings
                        stripped = line.strip()
                        if not stripped.startswith('#') and not stripped.startswith('"""'):
                            string_concat_violations.append(f"{rel_path}:{i}")
        
        if not html_generators:
            self._add_result(ValidationResult(
                check_name="HTML generation",
                passed=True,
                message="No HTML generation code found",
                requirement_refs=["6.12", "6.13"]
            ))
            return
        
        # Check if all HTML generators use BeautifulSoup
        all_use_bs4 = len(bs4_usage) == len(html_generators)
        no_string_concat = len(string_concat_violations) == 0
        
        passed = all_use_bs4 and no_string_concat
        
        details = []
        if not all_use_bs4:
            missing_bs4 = set(html_generators) - set(bs4_usage)
            details.extend([f"Missing BeautifulSoup: {f}" for f in missing_bs4])
        if not no_string_concat:
            details.extend([f"String concatenation: {v}" for v in string_concat_violations[:5]])
        
        self._add_result(ValidationResult(
            check_name="HTML generation",
            passed=passed,
            message=f"All {len(html_generators)} HTML generators use BeautifulSoup" \
                   if passed else \
                   "Some HTML generators use string concatenation",
            requirement_refs=["6.12", "6.13"],
            remediation="Replace HTML string concatenation with BeautifulSoup" \
                       if not passed else None,
            details=details[:10]
        ))
    
    # ========================================================================
    # ReportCrew Tools (Requirements 6.3, 6.4, 6.5, 6.6)
    # ========================================================================
    
    def _validate_report_crew_tools(self):
        """Verify ReportCrew has empty tools list and @final_reporter decorator."""
        report_crew_file = self.project_root / "src/finwiz/crews/report_crew/report_crew.py"
        
        if not report_crew_file.exists():
            self._add_result(ValidationResult(
                check_name="ReportCrew tools",
                passed=False,
                message="ReportCrew file not found",
                requirement_refs=["6.3", "6.4", "6.5", "6.6"],
                remediation="Create ReportCrew at src/finwiz/crews/report_crew/report_crew.py",
                details=[f"Expected path: {report_crew_file}"]
            ))
            return
        
        content = report_crew_file.read_text()
        
        # Check for @final_reporter decorator
        has_final_reporter = "@final_reporter" in content
        
        # Check for empty tools list
        has_empty_tools = "tools=[]" in content or "tools = []" in content
        
        # Check that it doesn't make external API calls
        # Look for common API call patterns (be specific to avoid false positives)
        api_patterns = [
            "requests.get(",
            "requests.post(",
            "httpx.get(",
            "httpx.post(",
            "httpx.Client(",
            "httpx.AsyncClient(",
            "urllib.request",
            "http.client"
        ]
        
        makes_api_calls = any(pattern in content for pattern in api_patterns)
        
        passed = has_final_reporter and has_empty_tools and not makes_api_calls
        
        details = []
        if not has_final_reporter:
            details.append("Missing @final_reporter decorator")
        if not has_empty_tools:
            details.append("Tools list not empty")
        if makes_api_calls:
            details.append("ReportCrew appears to make external API calls")
        
        self._add_result(ValidationResult(
            check_name="ReportCrew tools",
            passed=passed,
            message="ReportCrew has empty tools and @final_reporter" if passed else \
                   "ReportCrew configuration incorrect",
            requirement_refs=["6.3", "6.4", "6.5", "6.6"],
            remediation="Add @final_reporter decorator and set tools=[]" if not passed else None,
            details=details
        ))

    # ========================================================================
    # Feature Flags Documentation (Requirements 7.4, 7.5)
    # ========================================================================
    
    def _validate_feature_flags_documentation(self):
        """Verify all feature flags are documented in .env.example."""
        env_example = self.project_root / ".env.example"
        
        if not env_example.exists():
            self._add_result(ValidationResult(
                check_name="Feature flags documentation",
                passed=False,
                message=".env.example file not found",
                requirement_refs=["7.4", "7.5"],
                remediation="Create .env.example file with all feature flags",
                details=["Expected path: .env.example"]
            ))
            return
        
        env_content = env_example.read_text()
        
        # Find all feature flags in code
        src_dir = self.project_root / "src/finwiz"
        
        if not src_dir.exists():
            self._add_result(ValidationResult(
                check_name="Feature flags documentation",
                passed=False,
                message="Source directory not found",
                requirement_refs=["7.4", "7.5"],
                remediation="Create src/finwiz directory"
            ))
            return
        
        # Common feature flag patterns
        feature_flags = set()
        
        py_files = list(src_dir.rglob("*.py"))
        
        for py_file in py_files:
            content = py_file.read_text()
            
            # Find os.getenv() calls
            getenv_pattern = r'os\.getenv\(["\']([A-Z_]+)["\']\)'
            matches = re.findall(getenv_pattern, content)
            feature_flags.update(matches)
            
            # Find os.environ.get() calls
            environ_pattern = r'os\.environ\.get\(["\']([A-Z_]+)["\']\)'
            matches = re.findall(environ_pattern, content)
            feature_flags.update(matches)
            
            # Find os.environ[] access
            environ_bracket_pattern = r'os\.environ\[["\']([A-Z_]+)["\']\]'
            matches = re.findall(environ_bracket_pattern, content)
            feature_flags.update(matches)
        
        # Filter to likely feature flags (not API keys)
        feature_flag_keywords = [
            "ENABLED", "ENABLE", "DISABLED", "DISABLE",
            "FEATURE", "FLAG", "MODE", "STRICT",
            "DEEP", "ALTERNATIVE", "VALIDATION",
            "CHECKPOINT", "RETRY", "TIMEOUT"
        ]
        
        likely_feature_flags = set()
        for flag in feature_flags:
            if any(keyword in flag for keyword in feature_flag_keywords):
                likely_feature_flags.add(flag)
        
        # Check which flags are documented
        undocumented_flags = []
        for flag in likely_feature_flags:
            if flag not in env_content:
                undocumented_flags.append(flag)
        
        passed = len(undocumented_flags) == 0
        
        self._add_result(ValidationResult(
            check_name="Feature flags documentation",
            passed=passed,
            message=f"All {len(likely_feature_flags)} feature flags documented" if passed else \
                   f"{len(undocumented_flags)} feature flags not documented",
            requirement_refs=["7.4", "7.5"],
            remediation="Add missing feature flags to .env.example with descriptions" \
                       if not passed else None,
            details=[f"Undocumented: {flag}" for flag in sorted(undocumented_flags)]
        ))
    
    # ========================================================================
    # Report Generation
    # ========================================================================
    
    def generate_report(self) -> str:
        """Generate markdown validation report."""
        # Calculate statistics
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.passed)
        failed_checks = total_checks - passed_checks
        compliance_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Generate report
        report = f"""# FinWiz Architecture Validation Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Overall Compliance Score**: {compliance_score:.1f}% ({passed_checks}/{total_checks} checks passed)
- **Status**: {"✅ COMPLIANT" if compliance_score == 100 else "⚠️ NEEDS ATTENTION"}

## Validation Results

"""
        
        # Group results by phase
        phases = {
            "DeepAnalysisCrew": [],
            "Flow Orchestration": [],
            "Discovery Crews": [],
            "Enum Documentation": [],
            "Test Framework": [],
            "File Sizes": [],
            "HTML Generation": [],
            "ReportCrew": [],
            "Feature Flags": []
        }
        
        for result in self.results:
            if "DeepAnalysis" in result.check_name:
                phases["DeepAnalysisCrew"].append(result)
            elif "Flow" in result.check_name or "Atomic" in result.check_name or \
                 "Listener" in result.check_name:
                phases["Flow Orchestration"].append(result)
            elif "crew task description" in result.check_name:
                phases["Discovery Crews"].append(result)
            elif "Enum" in result.check_name:
                phases["Enum Documentation"].append(result)
            elif "Test framework" in result.check_name:
                phases["Test Framework"].append(result)
            elif "File sizes" in result.check_name:
                phases["File Sizes"].append(result)
            elif "HTML" in result.check_name:
                phases["HTML Generation"].append(result)
            elif "ReportCrew" in result.check_name:
                phases["ReportCrew"].append(result)
            elif "Feature flags" in result.check_name:
                phases["Feature Flags"].append(result)
        
        # Write results by phase
        for phase_name, phase_results in phases.items():
            if not phase_results:
                continue
            
            report += f"\n### {phase_name}\n\n"
            
            for result in phase_results:
                status = "✅ PASS" if result.passed else "❌ FAIL"
                report += f"**{status}**: {result.check_name}\n\n"
                report += f"- **Message**: {result.message}\n"
                report += f"- **Requirements**: {', '.join(result.requirement_refs)}\n"
                
                if not result.passed and result.remediation:
                    report += f"- **Remediation**: {result.remediation}\n"
                
                if result.details:
                    report += f"- **Details**:\n"
                    for detail in result.details[:5]:  # Show first 5 details
                        report += f"  - {detail}\n"
                
                report += "\n"
        
        # Add remediation summary
        if failed_checks > 0:
            report += "\n## Remediation Summary\n\n"
            report += "The following actions are required to achieve 100% compliance:\n\n"
            
            for i, result in enumerate([r for r in self.results if not r.passed], 1):
                report += f"{i}. **{result.check_name}**\n"
                if result.remediation:
                    report += f"   - {result.remediation}\n"
                report += f"   - Requirements: {', '.join(result.requirement_refs)}\n\n"
        
        # Add compliance matrix
        report += "\n## Compliance Matrix\n\n"
        report += "| Requirement | Status | Check |\n"
        report += "|-------------|--------|-------|\n"
        
        for result in sorted(self.results, key=lambda r: r.requirement_refs[0] if r.requirement_refs else ""):
            status = "✅" if result.passed else "❌"
            req_refs = ", ".join(result.requirement_refs)
            report += f"| {req_refs} | {status} | {result.check_name} |\n"
        
        return report


def main():
    """Main entry point for validation script."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Create validator
    validator = FinWizArchitectureValidator(project_root)
    
    # Run validation
    results = validator.validate_all()
    
    # Generate report
    report = validator.generate_report()
    
    # Save report
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "architecture_validation_report.md"
    report_file.write_text(report)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    score = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Checks:  {total}")
    print(f"Passed:        {passed} ✅")
    print(f"Failed:        {failed} ❌")
    print(f"Compliance:    {score:.1f}%")
    print(f"{'='*60}\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
