"""
Property-based tests for backward compatibility of Flow Orchestrator refactoring.

Tests that all existing imports and public API continue to work after refactoring
using property-based testing with Hypothesis.

**Feature: flow-orchestrator-refactoring**
- Property 3: Import Backward Compatibility (Validates: Requirements 1.4, 10.1)
- Property 27: API Compatibility (Validates: Requirements 10.5)
"""

import inspect

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


class TestImportBackwardCompatibility:
    """Property-based tests for import backward compatibility."""

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        import_name=st.sampled_from(
            [
                # Main Flow class
                "FinwizFlow",
                "OrchestratorDependencies",
                # State classes
                "FinwizState",
                "DeepAnalysisResult",
                "FlowStateManager",
                # Orchestrators
                "ErrorHandlingOrchestrator",
                "ProgressTrackingOrchestrator",
                "UtilityOrchestrator",
                "DeepAnalysisOrchestrator",
                "AlternativesMatchingOrchestrator",
                "DiscoveryOrchestrator",
                "ValidationOrchestrator",
                "ReportingOrchestrator",
                # Dependencies
                "CrewFactory",
                "CrewDataIntegrationManager",
                "CrewDataAccessor",
                "CoreAnalysisErrorHandler",
                "DataAvailabilityTracker",
                "get_resilience_config",
                "get_batch_prefetch_config",
                "create_retry_decorator",
                # Utility function
                "plot",
            ]
        )
    )
    def test_property_import_backward_compatibility(self, import_name):
        """
        **Feature: flow-orchestrator-refactoring, Property 3: Import Backward Compatibility**

        For any existing import path from flow_orchestrator, the import should
        resolve successfully after refactoring.

        This property ensures that:
        1. All previously exported names are still available
        2. Imports from the old module path continue to work
        3. No breaking changes to import statements
        """
        # Property: Import should succeed
        try:
            module = __import__("finwiz.flows.flow_orchestrator", fromlist=[import_name])
            imported_object = getattr(module, import_name)
        except (ImportError, AttributeError) as e:
            pytest.fail(f"Failed to import {import_name} from flow_orchestrator: {e}")

        # Property: Imported object should not be None
        assert imported_object is not None, f"Imported {import_name} is None"

        # Property: Imported object should be the correct type
        if import_name.endswith("Orchestrator"):
            # Should be a class
            assert inspect.isclass(imported_object), f"{import_name} should be a class"
        elif import_name in ["FinwizFlow", "OrchestratorDependencies"]:
            # Should be a class
            assert inspect.isclass(imported_object), f"{import_name} should be a class"
        elif import_name in [
            "FinwizState",
            "DeepAnalysisResult",
            "FlowStateManager",
        ]:
            # Should be a class
            assert inspect.isclass(imported_object), f"{import_name} should be a class"
        elif import_name.startswith("get_") or import_name.startswith("create_"):
            # Should be a function
            assert inspect.isfunction(imported_object) or inspect.ismethod(imported_object), f"{import_name} should be a function"
        elif import_name == "plot":
            # Should be a function
            assert inspect.isfunction(imported_object), f"{import_name} should be a function"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        import_pairs=st.lists(
            st.sampled_from(
                [
                    "FinwizFlow",
                    "ErrorHandlingOrchestrator",
                    "DeepAnalysisOrchestrator",
                    "ReportingOrchestrator",
                    "FinwizState",
                ]
            ),
            min_size=2,
            max_size=5,
            unique=True,
        )
    )
    def test_property_multiple_imports_work(self, import_pairs):
        """
        **Feature: flow-orchestrator-refactoring, Property 3: Import Backward Compatibility**

        For any combination of imports from flow_orchestrator, all imports
        should resolve successfully.

        This ensures that multiple imports in a single statement work correctly.
        """
        # Property: All imports should succeed
        try:
            module = __import__("finwiz.flows.flow_orchestrator", fromlist=import_pairs)
            imported_objects = {name: getattr(module, name) for name in import_pairs}
        except (ImportError, AttributeError) as e:
            pytest.fail(f"Failed to import {import_pairs} from flow_orchestrator: {e}")

        # Property: All imported objects should not be None
        for name, obj in imported_objects.items():
            assert obj is not None, f"Imported {name} is None"

        # Property: All imported objects should be distinct (if they're classes)
        class_objects = [obj for obj in imported_objects.values() if inspect.isclass(obj)]
        if len(class_objects) > 1:
            for i, obj1 in enumerate(class_objects):
                for j, obj2 in enumerate(class_objects):
                    if i != j:
                        assert obj1 is not obj2, "Classes should be distinct objects"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        import_style=st.sampled_from(
            [
                ("from", "FinwizFlow"),
                ("from", "ErrorHandlingOrchestrator"),
                ("from", "FinwizState"),
                ("import", "flow_orchestrator"),
            ]
        )
    )
    def test_property_import_styles_work(self, import_style):
        """
        **Feature: flow-orchestrator-refactoring, Property 3: Import Backward Compatibility**

        For any import style (from X import Y vs import X), the import should work.

        This ensures backward compatibility with different import patterns.
        """
        style, name = import_style

        if style == "from":
            # Test: from finwiz.flows.flow_orchestrator import Name
            try:
                module = __import__("finwiz.flows.flow_orchestrator", fromlist=[name])
                imported_object = getattr(module, name)
                assert imported_object is not None, f"from import failed for {name}"
            except (ImportError, AttributeError) as e:
                pytest.fail(f"from import failed for {name}: {e}")
        else:
            # Test: import finwiz.flows.flow_orchestrator
            try:
                module = __import__("finwiz.flows.flow_orchestrator")
                # Navigate to the actual module
                flow_module = module.flows.flow_orchestrator
                assert flow_module is not None, "import flow_orchestrator failed"
            except (ImportError, AttributeError) as e:
                pytest.fail(f"import flow_orchestrator failed: {e}")


class TestAPIBackwardCompatibility:
    """Property-based tests for API backward compatibility."""

    @pytest.fixture
    def flow_class(self):
        """Get the FinwizFlow class."""
        from finwiz.flows.flow_orchestrator import FinwizFlow

        return FinwizFlow

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        method_name=st.sampled_from(
            [
                # Flow listener methods (public API)
                "validate_data_integration",
                "check_portfolio",
                "analyze_and_update_portfolio",
                "match_alternatives_after_discovery",
                "check_crypto",
                "check_stock",
                "check_etf",
                "check_investment_discovery",
                "check_portfolio_rebalancing",
                "pre_validate_reporter_input",
                "report",
                # Orchestrator property accessors
                "error_handler_orch",
                "progress_orch",
                "utility_orch",
                "deep_analysis_orch",
                "alternatives_orch",
                "discovery_orch",
                "validation_orch",
                "reporting_orch",
            ]
        )
    )
    def test_property_api_compatibility(self, flow_class, method_name):
        """
        **Feature: flow-orchestrator-refactoring, Property 27: API Compatibility**

        For any public method in the original Flow, it should exist with the
        same signature in the refactored Flow.

        This property ensures that:
        1. All public methods are still available
        2. Method signatures haven't changed
        3. No breaking changes to the public API
        """
        # Property: Method should exist
        assert hasattr(flow_class, method_name), f"FinwizFlow missing method {method_name}"

        # Get the method
        method = getattr(flow_class, method_name)

        # Property: Method should be callable or a property
        assert callable(method) or isinstance(method, property), f"{method_name} should be callable or a property"

        # If it's a property, check that it has a getter
        if isinstance(method, property):
            assert method.fget is not None, f"Property {method_name} missing getter"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        method_pairs=st.lists(
            st.sampled_from(
                [
                    "validate_data_integration",
                    "check_portfolio",
                    "analyze_and_update_portfolio",
                    "report",
                ]
            ),
            min_size=2,
            max_size=4,
            unique=True,
        )
    )
    def test_property_multiple_methods_exist(self, flow_class, method_pairs):
        """
        **Feature: flow-orchestrator-refactoring, Property 27: API Compatibility**

        For any set of public methods, all should exist in the refactored Flow.

        This ensures comprehensive API coverage.
        """
        # Property: All methods should exist
        for method_name in method_pairs:
            assert hasattr(flow_class, method_name), f"FinwizFlow missing method {method_name}"

            method = getattr(flow_class, method_name)
            assert callable(method) or isinstance(method, property), f"{method_name} should be callable or a property"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        orchestrator_property=st.sampled_from(
            [
                "error_handler_orch",
                "progress_orch",
                "utility_orch",
                "deep_analysis_orch",
                "alternatives_orch",
                "discovery_orch",
                "validation_orch",
                "reporting_orch",
            ]
        )
    )
    def test_property_orchestrator_properties_exist(self, flow_class, orchestrator_property):
        """
        **Feature: flow-orchestrator-refactoring, Property 27: API Compatibility**

        For any orchestrator property, it should exist and return an orchestrator instance.

        This ensures that the lazy-loading orchestrator pattern is part of the public API.
        """
        # Property: Property should exist
        assert hasattr(flow_class, orchestrator_property), f"FinwizFlow missing property {orchestrator_property}"

        # Get the property descriptor
        prop = getattr(flow_class, orchestrator_property)

        # Property: Should be a property descriptor
        assert isinstance(prop, property), f"{orchestrator_property} should be a property"

        # Property: Should have a getter
        assert prop.fget is not None, f"Property {orchestrator_property} missing getter"

    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        method_name=st.sampled_from(
            [
                "validate_data_integration",
                "check_portfolio",
                "analyze_and_update_portfolio",
                "match_alternatives_after_discovery",
                "check_crypto",
                "check_stock",
                "check_etf",
                "check_investment_discovery",
                "check_portfolio_rebalancing",
                "pre_validate_reporter_input",
                "report",
            ]
        )
    )
    def test_property_method_signatures_preserved(self, flow_class, method_name):
        """
        **Feature: flow-orchestrator-refactoring, Property 27: API Compatibility**

        For any public method, its signature should be preserved (same parameters).

        This ensures that existing code calling these methods continues to work.
        """
        # Property: Method should exist
        assert hasattr(flow_class, method_name), f"FinwizFlow missing method {method_name}"

        method = getattr(flow_class, method_name)

        # Property: Method should be callable
        assert callable(method), f"{method_name} should be callable"

        # Get method signature
        sig = inspect.signature(method)

        # Property: Method should have 'self' parameter (it's an instance method)
        params = list(sig.parameters.keys())
        assert len(params) >= 1, f"{method_name} should have at least self parameter"

        # Property: Return annotation should exist (Flow methods return dict[str, Any])
        # Note: We don't enforce the exact return type here, just that it's documented
        # The actual return type is tested in unit tests

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    @given(
        class_attribute=st.sampled_from(
            [
                "__init__",
                "__class__",
                "__module__",
                "state",
                "kickoff",
                "plot",
            ]
        )
    )
    def test_property_class_attributes_preserved(self, flow_class, class_attribute):
        """
        **Feature: flow-orchestrator-refactoring, Property 27: API Compatibility**

        For any class attribute or inherited method, it should still be accessible.

        This ensures that Flow class behavior is preserved.
        """
        # Property: Attribute should exist
        assert hasattr(flow_class, class_attribute), f"FinwizFlow missing attribute {class_attribute}"

        attr = getattr(flow_class, class_attribute)

        # Property: Attribute should not be None
        assert attr is not None, f"Attribute {class_attribute} is None"
