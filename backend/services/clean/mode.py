import statistics

from .central_measure import CentralMeasureSelector


class ModeSelector(CentralMeasureSelector):
    """Seleciona usuários acima da moda (calculada após remoção de outliers via IQR)."""

    def _compute_threshold(self, clean_counts: list[float]) -> float:
        return statistics.mode(clean_counts)
