"""Funções estatísticas compartilhadas pelos seletores de volume."""

import statistics


def remove_outliers_iqr(values: list[float]) -> list[float]:
    """Remove outliers via IQR — apenas para cálculo do threshold,
    não para excluir usuários do resultado final."""
    if len(values) < 4:
        return values
    q1 = statistics.quantiles(values, n=4)[0]
    q3 = statistics.quantiles(values, n=4)[2]
    iqr = q3 - q1
    return [v for v in values if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]


def compute_central_measures(
    user_counts: dict[str, int],
) -> dict[str, float]:
    """Calcula média, moda, mediana e limites IQR."""
    counts = list(user_counts.values())
    if not counts:
        return {
            "mean": 0.0,
            "mode": 0.0,
            "median": 0.0,
            "iqr_lower": 0.0,
            "iqr_upper": 0.0,
        }

    clean = remove_outliers_iqr([float(c) for c in counts])

    if len(counts) >= 4:
        q1 = statistics.quantiles(counts, n=4)[0]
        q3 = statistics.quantiles(counts, n=4)[2]
    else:
        q1 = float(min(counts))
        q3 = float(max(counts))

    return {
        "mean": round(statistics.mean(clean), 2),
        "mode": float(statistics.mode(clean)),
        "median": round(statistics.median(clean), 2),
        "iqr_lower": round(q1, 2),
        "iqr_upper": round(q3, 2),
    }
