#!/usr/bin/env python3
"""
High-performance Metrics Calculation with Multiprocessing
Optimized for large datasets and real-time analytics
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .multiprocess_executor import get_process_pool

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Container for calculated metrics"""

    count: int
    sum: float
    mean: float
    median: float
    mode: Optional[float]
    std_dev: float
    variance: float
    min: float
    max: float
    range: float
    percentiles: Dict[int, float] = field(default_factory=dict)
    histogram: Optional[Dict[str, int]] = None
    outliers: List[float] = field(default_factory=list)


@dataclass
class TimeSeriesMetrics:
    """Metrics for time series data"""

    trend: str  # 'increasing', 'decreasing', 'stable'
    seasonality: bool
    autocorrelation: float
    moving_average: List[float]
    exponential_smoothing: List[float]
    forecast: Optional[List[float]] = None


class MetricsProcessor:
    """High-performance metrics processor using multiprocessing"""

    def __init__(self, use_multiprocessing: bool = True, use_numpy: bool = True):
        self.use_multiprocessing = use_multiprocessing
        self.use_numpy = use_numpy and self._check_numpy()
        self.pool = None

    def _check_numpy(self) -> bool:
        """Check if numpy is available"""
        try:
            import numpy

            return True
        except ImportError:
            logger.warning("NumPy not available, using pure Python calculations")
            return False

    async def __aenter__(self):
        if self.use_multiprocessing:
            self.pool = await get_process_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Pool is managed globally
        pass

    async def calculate_basic_metrics(
        self, data: List[float], percentiles: List[int] = None
    ) -> MetricResult:
        """Calculate basic statistical metrics"""
        if not data:
            return MetricResult(
                count=0,
                sum=0,
                mean=0,
                median=0,
                mode=None,
                std_dev=0,
                variance=0,
                min=0,
                max=0,
                range=0,
            )

        if percentiles is None:
            percentiles = [25, 50, 75, 90, 95, 99]

        # Use NumPy for faster calculations if available
        if self.use_numpy:
            return await self._calculate_numpy_metrics(data, percentiles)

        # Pure Python implementation
        return await self._calculate_python_metrics(data, percentiles)

    async def _calculate_numpy_metrics(
        self, data: List[float], percentiles: List[int]
    ) -> MetricResult:
        """Calculate metrics using NumPy"""
        arr = np.array(data)

        # Basic metrics
        count = len(arr)
        total = np.sum(arr)
        mean = np.mean(arr)
        median = np.median(arr)
        std_dev = np.std(arr)
        variance = np.var(arr)
        min_val = np.min(arr)
        max_val = np.max(arr)
        range_val = max_val - min_val

        # Mode (most frequent value)
        try:
            mode = float(statistics.mode(data))
        except statistics.StatisticsError:
            mode = None

        # Percentiles
        percentile_values = {}
        for p in percentiles:
            percentile_values[p] = float(np.percentile(arr, p))

        # Detect outliers using IQR method
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = arr[(arr < lower_bound) | (arr > upper_bound)].tolist()

        return MetricResult(
            count=count,
            sum=float(total),
            mean=float(mean),
            median=float(median),
            mode=mode,
            std_dev=float(std_dev),
            variance=float(variance),
            min=float(min_val),
            max=float(max_val),
            range=float(range_val),
            percentiles=percentile_values,
            outliers=outliers,
        )

    async def _calculate_python_metrics(
        self, data: List[float], percentiles: List[int]
    ) -> MetricResult:
        """Calculate metrics using pure Python"""
        sorted_data = sorted(data)
        count = len(data)
        total = sum(data)
        mean = statistics.mean(data)
        median = statistics.median(data)

        # Mode
        try:
            mode = statistics.mode(data)
        except statistics.StatisticsError:
            mode = None

        # Standard deviation and variance
        if count > 1:
            std_dev = statistics.stdev(data)
            variance = statistics.variance(data)
        else:
            std_dev = 0
            variance = 0

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        # Calculate percentiles
        percentile_values = {}
        for p in percentiles:
            idx = int(count * p / 100)
            if idx >= count:
                idx = count - 1
            percentile_values[p] = sorted_data[idx]

        # Detect outliers
        q1_idx = count // 4
        q3_idx = 3 * count // 4
        q1 = sorted_data[q1_idx]
        q3 = sorted_data[q3_idx]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = [x for x in data if x < lower_bound or x > upper_bound]

        return MetricResult(
            count=count,
            sum=total,
            mean=mean,
            median=median,
            mode=mode,
            std_dev=std_dev,
            variance=variance,
            min=min_val,
            max=max_val,
            range=range_val,
            percentiles=percentile_values,
            outliers=outliers,
        )

    async def calculate_batch_metrics(
        self, datasets: List[List[float]], percentiles: List[int] = None
    ) -> List[MetricResult]:
        """Calculate metrics for multiple datasets using multiprocessing"""
        if not datasets:
            return []

        # Use multiprocessing for large batches
        if self.use_multiprocessing and self.pool and len(datasets) > 10:
            # Process in parallel
            raw_results = await self.pool.calculate_metrics(datasets)

            # Convert to MetricResult objects
            results = []
            for data, raw in zip(datasets, raw_results):
                if not raw:
                    results.append(
                        MetricResult(
                            count=0,
                            sum=0,
                            mean=0,
                            median=0,
                            mode=None,
                            std_dev=0,
                            variance=0,
                            min=0,
                            max=0,
                            range=0,
                        )
                    )
                else:
                    # Calculate additional metrics
                    result = await self.calculate_basic_metrics(data, percentiles)
                    results.append(result)

            return results

        # Process sequentially for small batches
        tasks = [self.calculate_basic_metrics(data, percentiles) for data in datasets]
        return await asyncio.gather(*tasks)

    async def calculate_histogram(
        self, data: List[float], bins: Union[int, List[float]] = 10
    ) -> Dict[str, Any]:
        """Calculate histogram for data distribution"""
        if not data:
            return {"bins": [], "counts": [], "edges": []}

        if self.use_numpy:
            arr = np.array(data)
            counts, edges = np.histogram(arr, bins=bins)

            # Create bin labels
            bin_labels = []
            for i in range(len(edges) - 1):
                label = f"{edges[i]:.2f}-{edges[i+1]:.2f}"
                bin_labels.append(label)

            return {
                "bins": bin_labels,
                "counts": counts.tolist(),
                "edges": edges.tolist(),
            }

        # Pure Python histogram
        min_val = min(data)
        max_val = max(data)

        if isinstance(bins, int):
            # Create uniform bins
            bin_width = (max_val - min_val) / bins
            edges = [min_val + i * bin_width for i in range(bins + 1)]
        else:
            edges = bins

        # Count values in each bin
        counts = [0] * (len(edges) - 1)
        for value in data:
            for i in range(len(edges) - 1):
                if edges[i] <= value < edges[i + 1]:
                    counts[i] += 1
                    break
            else:
                # Handle max value
                if value == edges[-1]:
                    counts[-1] += 1

        # Create bin labels
        bin_labels = []
        for i in range(len(edges) - 1):
            label = f"{edges[i]:.2f}-{edges[i+1]:.2f}"
            bin_labels.append(label)

        return {"bins": bin_labels, "counts": counts, "edges": edges}

    async def calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        if self.use_numpy:
            return float(np.corrcoef(x, y)[0, 1])

        # Pure Python implementation
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi**2 for xi in x)
        sum_y2 = sum(yi**2 for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    async def calculate_moving_average(
        self, data: List[float], window_size: int
    ) -> List[float]:
        """Calculate simple moving average"""
        if len(data) < window_size:
            return []

        if self.use_numpy:
            arr = np.array(data)
            weights = np.ones(window_size) / window_size
            return np.convolve(arr, weights, mode="valid").tolist()

        # Pure Python implementation
        moving_avg = []
        for i in range(len(data) - window_size + 1):
            window = data[i : i + window_size]
            avg = sum(window) / window_size
            moving_avg.append(avg)

        return moving_avg

    async def calculate_exponential_smoothing(
        self, data: List[float], alpha: float = 0.3
    ) -> List[float]:
        """Calculate exponential smoothing"""
        if not data:
            return []

        smoothed = [data[0]]
        for i in range(1, len(data)):
            s = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)

        return smoothed

    async def detect_anomalies(
        self, data: List[float], method: str = "zscore", threshold: float = 3.0
    ) -> List[Tuple[int, float]]:
        """Detect anomalies in data"""
        if not data or len(data) < 2:
            return []

        anomalies = []

        if method == "zscore":
            # Z-score method
            mean = statistics.mean(data)
            std_dev = statistics.stdev(data)

            if std_dev == 0:
                return []

            for i, value in enumerate(data):
                z_score = abs((value - mean) / std_dev)
                if z_score > threshold:
                    anomalies.append((i, value))

        elif method == "iqr":
            # Interquartile range method
            sorted_data = sorted(data)
            q1 = sorted_data[len(sorted_data) // 4]
            q3 = sorted_data[3 * len(sorted_data) // 4]
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for i, value in enumerate(data):
                if value < lower_bound or value > upper_bound:
                    anomalies.append((i, value))

        elif method == "mad":
            # Median Absolute Deviation method
            median = statistics.median(data)
            mad = statistics.median([abs(x - median) for x in data])

            if mad == 0:
                return []

            for i, value in enumerate(data):
                deviation = abs((value - median) / mad)
                if deviation > threshold:
                    anomalies.append((i, value))

        return anomalies

    async def calculate_time_series_metrics(
        self,
        data: List[float],
        timestamps: Optional[List[datetime]] = None,
        window_size: int = 5,
    ) -> TimeSeriesMetrics:
        """Calculate time series specific metrics"""
        if len(data) < 3:
            return TimeSeriesMetrics(
                trend="stable",
                seasonality=False,
                autocorrelation=0.0,
                moving_average=[],
                exponential_smoothing=[],
            )

        # Detect trend
        first_third = statistics.mean(data[: len(data) // 3])
        last_third = statistics.mean(data[-len(data) // 3 :])

        if last_third > first_third * 1.1:
            trend = "increasing"
        elif last_third < first_third * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        # Calculate autocorrelation (lag 1)
        autocorr = await self.calculate_correlation(data[:-1], data[1:])

        # Detect seasonality (simple check)
        seasonality = False
        if len(data) >= window_size * 2:
            # Check if pattern repeats
            pattern_size = window_size
            matches = 0
            for i in range(len(data) - pattern_size * 2):
                pattern1 = data[i : i + pattern_size]
                pattern2 = data[i + pattern_size : i + pattern_size * 2]
                corr = await self.calculate_correlation(pattern1, pattern2)
                if corr > 0.7:
                    matches += 1

            if matches > len(data) // (pattern_size * 3):
                seasonality = True

        # Calculate moving average
        moving_avg = await self.calculate_moving_average(data, window_size)

        # Calculate exponential smoothing
        exp_smooth = await self.calculate_exponential_smoothing(data)

        return TimeSeriesMetrics(
            trend=trend,
            seasonality=seasonality,
            autocorrelation=autocorr,
            moving_average=moving_avg,
            exponential_smoothing=exp_smooth,
        )

    async def aggregate_metrics(self, metrics_list: List[MetricResult]) -> MetricResult:
        """Aggregate multiple metric results"""
        if not metrics_list:
            return MetricResult(
                count=0,
                sum=0,
                mean=0,
                median=0,
                mode=None,
                std_dev=0,
                variance=0,
                min=0,
                max=0,
                range=0,
            )

        # Combine all data points
        all_counts = [m.count for m in metrics_list]
        all_sums = [m.sum for m in metrics_list]
        all_means = [m.mean for m in metrics_list if m.count > 0]
        all_mins = [m.min for m in metrics_list if m.count > 0]
        all_maxs = [m.max for m in metrics_list if m.count > 0]

        total_count = sum(all_counts)
        total_sum = sum(all_sums)

        if total_count == 0:
            return MetricResult(
                count=0,
                sum=0,
                mean=0,
                median=0,
                mode=None,
                std_dev=0,
                variance=0,
                min=0,
                max=0,
                range=0,
            )

        # Calculate aggregated metrics
        overall_mean = total_sum / total_count
        overall_min = min(all_mins) if all_mins else 0
        overall_max = max(all_maxs) if all_maxs else 0
        overall_range = overall_max - overall_min

        # Approximate median and std dev from means
        median_of_means = statistics.median(all_means) if all_means else 0
        std_of_means = statistics.stdev(all_means) if len(all_means) > 1 else 0

        return MetricResult(
            count=total_count,
            sum=total_sum,
            mean=overall_mean,
            median=median_of_means,
            mode=None,
            std_dev=std_of_means,
            variance=std_of_means**2,
            min=overall_min,
            max=overall_max,
            range=overall_range,
        )


# Global instance
_global_processor: Optional[MetricsProcessor] = None


async def get_metrics_processor() -> MetricsProcessor:
    """Get or create global metrics processor"""
    global _global_processor
    if _global_processor is None:
        _global_processor = MetricsProcessor()
    return _global_processor
