from collections import Counter
from datetime import datetime, timedelta
from fastapi import APIRouter

from .. import mock_data
from ..schemas import DashboardStats, SeverityCount, SpeciesCount, TrendPoint

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats():
    records = mock_data.all_records()
    today = datetime.now().date()
    total = len(records)
    today_count = sum(1 for r in records if r.created_at.date() == today)

    species_counter = Counter()
    severity_counter = Counter()
    confidences = []
    for r in records:
        severity_counter[r.severity] += 1
        confidences.append(r.avg_confidence)
        for p in r.pest_types:
            species_counter[p] += 1

    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    trend_map = {}
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).date()
        trend_map[day.isoformat()] = 0
    for r in records:
        key = r.created_at.date().isoformat()
        if key in trend_map:
            trend_map[key] += 1

    return DashboardStats(
        total_detections=total,
        today_detections=today_count,
        pest_species_count=len(species_counter),
        avg_confidence=avg_confidence,
        severity_distribution=[SeverityCount(level=k, count=v) for k, v in severity_counter.items()],
        species_distribution=[SpeciesCount(name=k, count=v) for k, v in species_counter.most_common()],
        trend=[TrendPoint(date=k, count=v) for k, v in trend_map.items()],
    )
