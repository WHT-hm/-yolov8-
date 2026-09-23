"""内存数据仓库：应用启动时生成模拟历史数据，运行期间的新增/删除也保存在内存中"""
import random
from datetime import datetime, timedelta
from itertools import count
from typing import List, Optional

from .schemas import BoundingBox, DetectionRecord

PEST_CROP_MAP = {
    "稻飞虱": "水稻",
    "稻纵卷叶螟": "水稻",
    "玉米螟": "玉米",
    "粘虫": "玉米",
    "蚜虫": "小麦",
    "蝗虫": "小麦",
    "红蜘蛛": "棉花",
    "棉铃虫": "棉花",
    "菜青虫": "蔬菜",
    "小菜蛾": "蔬菜",
}
PEST_TYPES = list(PEST_CROP_MAP.keys())
CROP_TYPES = sorted(set(PEST_CROP_MAP.values()))
SEVERITY_LEVELS = ["低", "中", "高"]
PLACEHOLDER_IMAGE = "/static/placeholder.svg"

_id_counter = count(1)
_records: List[DetectionRecord] = []


def _severity_from_confidence(confidence: float) -> str:
    if confidence >= 0.85:
        return "高"
    if confidence >= 0.6:
        return "中"
    return "低"


def _random_boxes(pest_names: List[str]) -> List[BoundingBox]:
    boxes = []
    for name in pest_names:
        confidence = round(random.uniform(0.55, 0.98), 2)
        w = round(random.uniform(0.12, 0.32), 2)
        h = round(random.uniform(0.12, 0.32), 2)
        x = round(random.uniform(0, 1 - w), 2)
        y = round(random.uniform(0, 1 - h), 2)
        boxes.append(BoundingBox(pest_name=name, confidence=confidence, x=x, y=y, width=w, height=h))
    return boxes


def create_mock_detection(crop_type: Optional[str], image_url: str) -> DetectionRecord:
    """生成一条模拟检测结果（后续可替换为真实 YOLOv8 推理逻辑）"""
    candidates = [p for p, c in PEST_CROP_MAP.items() if crop_type in (None, c)] or PEST_TYPES
    pest_count = random.randint(1, min(3, len(candidates)))
    pest_names = random.sample(candidates, pest_count)
    boxes = _random_boxes(pest_names)
    avg_confidence = round(sum(b.confidence for b in boxes) / len(boxes), 2)
    record = DetectionRecord(
        id=next(_id_counter),
        image_url=image_url,
        thumbnail_url=image_url,
        crop_type=crop_type or PEST_CROP_MAP[pest_names[0]],
        pest_types=pest_names,
        severity=_severity_from_confidence(avg_confidence),
        avg_confidence=avg_confidence,
        boxes=boxes,
        created_at=datetime.now(),
    )
    _records.insert(0, record)
    return record


def _seed_history(n: int = 28):
    now = datetime.now()
    for _ in range(n):
        crop = random.choice(CROP_TYPES)
        candidates = [p for p, c in PEST_CROP_MAP.items() if c == crop]
        pest_names = random.sample(candidates, random.randint(1, min(2, len(candidates))))
        boxes = _random_boxes(pest_names)
        avg_confidence = round(sum(b.confidence for b in boxes) / len(boxes), 2)
        days_ago = random.randint(0, 29)
        hours_ago = random.randint(0, 23)
        record = DetectionRecord(
            id=next(_id_counter),
            image_url=PLACEHOLDER_IMAGE,
            thumbnail_url=PLACEHOLDER_IMAGE,
            crop_type=crop,
            pest_types=pest_names,
            severity=_severity_from_confidence(avg_confidence),
            avg_confidence=avg_confidence,
            boxes=boxes,
            created_at=now - timedelta(days=days_ago, hours=hours_ago),
        )
        _records.append(record)
    _records.sort(key=lambda r: r.created_at, reverse=True)


def list_detections(page: int, page_size: int, pest_type: Optional[str] = None,
                     severity: Optional[str] = None, keyword: Optional[str] = None):
    items = _records
    if pest_type:
        items = [r for r in items if pest_type in r.pest_types]
    if severity:
        items = [r for r in items if r.severity == severity]
    if keyword:
        items = [r for r in items if keyword in r.crop_type or any(keyword in p for p in r.pest_types)]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total


def get_detection(detection_id: int) -> Optional[DetectionRecord]:
    return next((r for r in _records if r.id == detection_id), None)


def delete_detection(detection_id: int) -> bool:
    global _records
    before = len(_records)
    _records = [r for r in _records if r.id != detection_id]
    return len(_records) != before


def all_records() -> List[DetectionRecord]:
    return _records


_seed_history()
