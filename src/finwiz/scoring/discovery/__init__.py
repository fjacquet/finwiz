"""
Discovery sub-package for newcomer investment candidate detection.

Provides the NewcomerDiscoveryPipeline and individual discovery components
(universe provider, screeners, scanner, scorer) built in Phase 2.
"""

from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

__all__ = [
    "NewcomerDiscoveryPipeline",
]
