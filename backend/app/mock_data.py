"""内存数据仓库：应用启动时生成模拟历史数据，运行期间的新增/删除也保存在内存中"""
import random
from collections import Counter
from datetime import datetime, timedelta
from itertools import count
from typing import List, Optional

from .schemas import BoundingBox, DetectionRecord, PestDamageStat, PlantPartStat, RiskAlert

PEST_CROP_MAP = {
    # 原有10种
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
    # 新增20种
    "桃小食心虫": "果树",
    "斜纹夜蛾": "果树",
    "介壳虫": "果树",
    "梨小食心虫": "果树",
    "豆荚螟": "大豆",
    "豆秆蝇": "大豆",
    "豆天蛾": "大豆",
    "烟青虫": "烟草",
    "烟草天蛾": "烟草",
    "烟蚜": "烟草",
    "茶毛虫": "茶树",
    "茶尺蠖": "茶树",
    "茶叶蝉": "茶树",
    "螟虫综合体": "水稻",
    "稻飞虱若虫": "水稻",
    "小麦吸浆虫": "小麦",
    "小麦纹枯病虫": "小麦",
    "棉盲蝽": "棉花",
    "棉蚜": "棉花",
    "棉叶蝉": "棉花",
}
PEST_TYPES = list(PEST_CROP_MAP.keys())
CROP_TYPES = sorted(set(PEST_CROP_MAP.values()))
SEVERITY_LEVELS = ["低", "中", "高"]
PLACEHOLDER_IMAGE = "/static/placeholder.svg"

PLANT_PARTS = ["叶片", "茎秆", "根部", "其他"]
PLANT_PART_WEIGHTS = [0.5, 0.25, 0.15, 0.10]
SEVERITY_WEIGHT = {"低": 1, "中": 2, "高": 3}
RISK_WINDOW_DAYS = 7
RISK_THRESHOLDS = (5, 15)  # <5 低, 5~15 中, >15 高

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
        damage_ratio = round(random.uniform(5, 95), 1)
        plant_part = random.choices(PLANT_PARTS, weights=PLANT_PART_WEIGHTS)[0]
        boxes.append(BoundingBox(
            pest_name=name, confidence=confidence, x=x, y=y, width=w, height=h,
            damage_ratio=damage_ratio, plant_part=plant_part,
        ))
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


def get_damage_ranking() -> List[PestDamageStat]:
    """按害虫种类汇总平均受害占比，用于比较哪种害虫造成的损害更大"""
    sums: Counter = Counter()
    counts: Counter = Counter()
    for r in _records:
        for box in r.boxes:
            sums[box.pest_name] += box.damage_ratio
            counts[box.pest_name] += 1
    ranking = [
        PestDamageStat(
            pest_name=name,
            avg_damage_ratio=round(sums[name] / counts[name], 1),
            detection_count=counts[name],
        )
        for name in counts
    ]
    ranking.sort(key=lambda s: s.avg_damage_ratio, reverse=True)
    return ranking


def get_part_distribution() -> List[PlantPartStat]:
    """统计受害部位分布"""
    counter: Counter = Counter()
    for r in _records:
        for box in r.boxes:
            counter[box.plant_part] += 1
    total = sum(counter.values())
    return [
        PlantPartStat(
            part=part,
            count=counter[part],
            percentage=round(counter[part] / total * 100, 1) if total else 0.0,
        )
        for part in PLANT_PARTS
        if counter[part] > 0
    ]


def get_risk_alert() -> RiskAlert:
    """基于近期（模拟）检测数据的启发式环境风险预警，非真实气象数据"""
    cutoff = datetime.now() - timedelta(days=RISK_WINDOW_DAYS)
    recent = [r for r in _records if r.created_at >= cutoff]

    if not recent:
        return RiskAlert(
            level="低",
            message="暂无异常趋势，近期未发现明显病虫害风险",
            basis=f"近 {RISK_WINDOW_DAYS} 天内无检测记录",
            generated_at=datetime.now(),
        )

    pest_scores: Counter = Counter()
    for r in recent:
        avg_damage = sum(b.damage_ratio for b in r.boxes) / len(r.boxes) if r.boxes else 0
        score = SEVERITY_WEIGHT.get(r.severity, 1) * (avg_damage / 100)
        for pest in r.pest_types:
            pest_scores[pest] += score

    total_score = sum(pest_scores.values())
    top_pest, top_score = pest_scores.most_common(1)[0]
    crop = PEST_CROP_MAP.get(top_pest)

    low, high = RISK_THRESHOLDS
    if total_score < low:
        level = "低"
    elif total_score <= high:
        level = "中"
    else:
        level = "高"

    message = f"近 {RISK_WINDOW_DAYS} 天内 {top_pest} 相关高危害检测占比上升"
    if crop:
        message += f"，建议加强 {crop} 田间巡查，提前采取防治措施"
    basis = f"近 {RISK_WINDOW_DAYS} 天风险得分 {round(total_score, 1)}（{top_pest} 贡献 {round(top_score, 1)}）"

    return RiskAlert(
        level=level,
        pest_name=top_pest,
        crop_type=crop,
        message=message,
        basis=basis,
        generated_at=datetime.now(),
    )


_seed_history()
