from datetime import date

from app.models import YesNo
from app.services import aggregate_metrics


def test_aggregate_metrics_returns_store_performance():
    metrics = aggregate_metrics(
        [
            (1, "Ana", 10, "Loja Mauá", date(2026, 8, 27), YesNo.YES, YesNo.YES, YesNo.YES),
            (2, "Bruno", 10, "Loja Mauá", date(2026, 8, 27), YesNo.YES, YesNo.NO, YesNo.NO),
            (3, "Carla", 20, "Loja Centro Vale", date(2026, 8, 27), YesNo.NO, YesNo.NO, YesNo.NO),
        ]
    )

    stores = {item["store"]: item for item in metrics["store_performance"]}
    assert stores["Loja Mauá"]["passwords"] == 2
    assert stores["Loja Mauá"]["sales"] == 1
    assert stores["Loja Mauá"]["conversion"] == 100
    assert stores["Loja Centro Vale"]["conversion"] == 0
