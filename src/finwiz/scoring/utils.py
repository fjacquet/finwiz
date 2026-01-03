"""
Scoring utility functions for threshold-based calculations.

Provides reusable utilities for common scoring patterns across different scorers.
"""

from __future__ import annotations


def calculate_threshold_score(
    value: float,
    thresholds: list[tuple[float, float]],
    reverse: bool = False,
) -> float:
    """
    Calculate score based on threshold ranges.

    This utility function eliminates duplicate threshold-based scoring logic
    across ROE, debt, growth, expense ratio, and other metrics.

    Args:
        value: The value to score
        thresholds: List of (threshold, score) tuples, sorted ascending by threshold
                   Example: [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]
        reverse: If True, lower values get higher scores (for metrics like debt)

    Returns:
        Score between 0.0 and 1.0

    Examples:
        >>> # ROE scoring (higher is better)
        >>> roe_thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]
        >>> calculate_threshold_score(0.18, roe_thresholds)
        0.8

        >>> # Debt scoring (lower is better)
        >>> debt_thresholds = [(0.2, 1.0), (0.5, 0.8), (1.0, 0.6), (2.0, 0.4)]
        >>> calculate_threshold_score(0.3, debt_thresholds, reverse=True)
        0.9

    """
    if not thresholds:
        return 0.5  # Default neutral score if no thresholds provided

    # For reverse scoring (lower is better), invert the value comparison
    if reverse:
        # Find the appropriate score by checking thresholds in reverse order
        for i in range(len(thresholds) - 1, -1, -1):
            threshold, score = thresholds[i]
            if value >= threshold:
                # Value is at or above this threshold, return this score
                return score
        # Value is below all thresholds, return the highest score
        return thresholds[0][1]
    else:
        # Normal scoring (higher is better)
        # Find the appropriate score by checking thresholds in order
        for threshold, score in thresholds:
            if value >= threshold:
                # Continue to find the highest applicable threshold
                continue
            else:
                # Value is below this threshold, return previous score
                # Find the previous threshold's score
                prev_idx = thresholds.index((threshold, score)) - 1
                if prev_idx >= 0:
                    return thresholds[prev_idx][1]
                else:
                    # Value is below the first threshold
                    return 0.0

        # Value is at or above all thresholds, return the highest score
        return thresholds[-1][1]


def interpolate_threshold_score(
    value: float,
    thresholds: list[tuple[float, float]],
    reverse: bool = False,
) -> float:
    """
    Calculate score with linear interpolation between thresholds.

    Provides smoother scoring by interpolating between threshold points
    rather than using step functions.

    Args:
        value: The value to score
        thresholds: List of (threshold, score) tuples, sorted ascending
        reverse: If True, lower values get higher scores

    Returns:
        Score between 0.0 and 1.0 with interpolation

    Examples:
        >>> thresholds = [(0.10, 0.6), (0.20, 1.0)]
        >>> interpolate_threshold_score(0.15, thresholds)
        0.8  # Interpolated between 0.6 and 1.0

    """
    if not thresholds:
        return 0.5

    # Sort thresholds to ensure correct order
    sorted_thresholds = sorted(thresholds, key=lambda x: x[0])

    # Handle reverse scoring
    if reverse:
        value = -value
        sorted_thresholds = [(-t, s) for t, s in sorted_thresholds]
        sorted_thresholds.sort(key=lambda x: x[0])

    # Check if value is below first threshold
    if value < sorted_thresholds[0][0]:
        return 0.0

    # Check if value is above last threshold
    if value > sorted_thresholds[-1][0]:
        return sorted_thresholds[-1][1]

    # Find the two thresholds to interpolate between
    for i in range(len(sorted_thresholds) - 1):
        lower_threshold, lower_score = sorted_thresholds[i]
        upper_threshold, upper_score = sorted_thresholds[i + 1]

        if lower_threshold <= value <= upper_threshold:
            # Linear interpolation
            if upper_threshold == lower_threshold:
                return lower_score

            ratio = (value - lower_threshold) / (upper_threshold - lower_threshold)
            interpolated_score = lower_score + ratio * (upper_score - lower_score)
            return interpolated_score

    # Fallback (should not reach here)
    return 0.5
