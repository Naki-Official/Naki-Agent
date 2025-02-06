import numpy as np
import math
from typing import List, Optional

def safe_ratio(agent: dict, metric_key: str) -> Optional[float]:
    value = agent.get(metric_key, 0)
    if value > 0:
        return agent.get("marketCap", 0) / value
    return None

def compute_ratio_score(avg_ratio: Optional[float], agent_metric: float, market_cap: float) -> Optional[float]:
    if not (avg_ratio and agent_metric > 0 and market_cap > 0):
        return None
    agent_ratio = market_cap / agent_metric
    if agent_ratio <= 0:
        return None
    return avg_ratio / agent_ratio

def robust_normalize(value: float, values_list: List[float]) -> float:
    arr = np.array(values_list)
    min_val = arr.min()
    max_val = np.percentile(arr, 99)
    if max_val == min_val:
        return 0
    clipped = min(value, max_val)
    return (clipped - min_val) / (max_val - min_val)

def log_robust_normalize(value: float, values_list: List[float]) -> float:
    # Only use positive values for log
    log_values = [math.log(v) for v in values_list if v > 0]
    if not log_values:
        return 0
    log_value = math.log(value) if value > 0 else 0
    min_val = min(log_values)
    max_val = np.percentile(log_values, 99)
    if max_val == min_val:
        return 0
    clipped = min(log_value, max_val)
    return (clipped - min_val) / (max_val - min_val)
