"""Utility functions for time lag analysis and processing."""

import numpy as np


def adjust_range_for_eddypro(min_lag, max_lag, step=0.05):
    """
    Adjust detected range to account for EddyPro's discrete lag steps and boundary exclusion.

    EddyPro uses 0.05s discrete steps and excludes the specified boundaries.
    To ensure a detected range [0.10-1.00] is actually used, input to EddyPro
    must be [0.05-1.05] so that the 0.10 and 1.00 steps are included.

    Parameters
    ----------
    min_lag : float
        Detected minimum lag (seconds)
    max_lag : float
        Detected maximum lag (seconds)
    step : float
        EddyPro's lag step size (default 0.05s)

    Returns
    -------
    eddypro_min, eddypro_max : float
        Adjusted range for EddyPro input
    """
    eddypro_min = min_lag - step
    eddypro_max = max_lag + step
    return eddypro_min, eddypro_max


def detect_peak_range(histogram_results, peakbins, gradient_threshold=0.15):
    """
    Detect the narrow range around the peak using gradient-based edge detection.

    Finds inflection points where the histogram gradient changes significantly,
    indicating the edges of the peak.

    Parameters
    ----------
    histogram_results : pd.DataFrame
        Histogram results with 'BIN_START_INCL' and 'COUNTS' columns
    peakbins : array-like
        Peak bin values (peakbins[0] is the main peak)
    gradient_threshold : float
        Threshold for detecting significant slope changes (0-1, lower = stricter)

    Returns
    -------
    min_lag, max_lag : float
        Lag range boundaries around the peak
    """
    bins = histogram_results['BIN_START_INCL'].values
    counts = histogram_results['COUNTS'].values

    # Normalize counts for gradient calculation
    max_count = counts.max()
    normalized_counts = counts / max_count if max_count > 0 else counts

    # Calculate gradient (first derivative)
    gradient = np.gradient(normalized_counts)

    # Find the peak index
    peak_idx = np.argmin(np.abs(bins - peakbins[0]))

    # Search left for edge: where gradient magnitude drops below threshold
    left_idx = peak_idx
    for i in range(peak_idx - 1, -1, -1):
        if np.abs(gradient[i]) < gradient_threshold:
            left_idx = i
            break

    # Search right for edge: where gradient magnitude drops below threshold
    right_idx = peak_idx
    for i in range(peak_idx + 1, len(gradient)):
        if np.abs(gradient[i]) < gradient_threshold:
            right_idx = i
            break

    min_lag = bins[left_idx]
    max_lag = bins[right_idx]

    return min_lag, max_lag
