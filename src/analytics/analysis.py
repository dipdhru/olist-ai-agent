import yaml
from typing import Dict, Any, Optional

class MetricLayer:
    """
    Handles semantic business metrics.
    """
    def __init__(self, metrics_path: str = "data/metrics.yaml"):
        self.metrics_path = metrics_path
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        try:
            with open(self.metrics_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def get_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:
        return self.metrics.get(metric_name)

    def get_all_metrics(self) -> Dict[str, Any]:
        return self.metrics
