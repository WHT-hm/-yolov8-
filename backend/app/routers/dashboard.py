import json
from collections import Counter
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models
from ..database import get_db
from ..schemas import DashboardStats, RiskAlert, SeverityCount, SpeciesCount, TrendPoint

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# 常量定义
PLANT_PARTS = ["叶片", "茎秆", "根部", "其他"]
SEVERITY_WEIGHT = {"低": 1, "中": 2, "高": 3}
RISK_WINDOW_DAYS = 7
RISK_THRESHOLDS = (5, 15)  # <5 低, 5~15 中, >15 高


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """获取仪表板统计数据，超级管理员看全部，普通管理员只看自己机构"""
    # 权限过滤：构建查询
    query = db.query(models.Detection)
    if current_user.role != "super_admin":
        query = query.filter(models.Detection.org_id == current_user.org_id)

    records = query.all()
    today = datetime.now().date()
    total = len(records)
    today_count = sum(1 for r in records if r.created_at.date() == today)

    species_counter = Counter()
    severity_counter = Counter()
    confidences = []
    damage_sum = {}  # 害虫名 -> (总受害占比, 出现次数)
    plant_part_counter = Counter()

    for r in records:
        severity_counter[r.severity] += 1
        confidences.append(r.avg_confidence)

        # 解析 pest_types JSON
        try:
            pest_types = json.loads(r.pest_types) if isinstance(r.pest_types, str) else r.pest_types
        except:
            pest_types = []

        for p in pest_types:
            species_counter[p] += 1

        # 解析 boxes JSON 计算受害占比和部位分布
        try:
            boxes = json.loads(r.boxes) if isinstance(r.boxes, str) else r.boxes
        except:
            boxes = []

        for box in boxes:
            pest_name = box.get("pest_name", "未知")
            damage_ratio = box.get("damage_ratio", 0)
            plant_part = box.get("plant_part", "其他")

            if pest_name not in damage_sum:
                damage_sum[pest_name] = (0, 0)
            prev_sum, count = damage_sum[pest_name]
            damage_sum[pest_name] = (prev_sum + damage_ratio, count + 1)

            plant_part_counter[plant_part] += 1

    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    # 趋势（近7天）
    trend_map = {}
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).date()
        trend_map[day.isoformat()] = 0
    for r in records:
        key = r.created_at.date().isoformat()
        if key in trend_map:
            trend_map[key] += 1

    # 受害程度排行
    damage_ranking = []
    for pest_name, (total_damage, count) in sorted(damage_sum.items(), key=lambda x: x[1][0] / x[1][1] if x[1][1] > 0 else 0, reverse=True):
        if count > 0:
            from ..schemas import PestDamageStat
            damage_ranking.append(PestDamageStat(
                pest_name=pest_name,
                avg_damage_ratio=round(total_damage / count, 1),
                detection_count=count,
            ))

    # 受害部位分布
    total_parts = sum(plant_part_counter.values())
    from ..schemas import PlantPartStat
    part_distribution = []
    for part in PLANT_PARTS:
        if plant_part_counter[part] > 0:
            part_distribution.append(PlantPartStat(
                part=part,
                count=plant_part_counter[part],
                percentage=round(plant_part_counter[part] / total_parts * 100, 1) if total_parts else 0.0,
            ))

    return DashboardStats(
        total_detections=total,
        today_detections=today_count,
        pest_species_count=len(species_counter),
        avg_confidence=avg_confidence,
        severity_distribution=[SeverityCount(level=k, count=v) for k, v in severity_counter.items()],
        species_distribution=[SpeciesCount(name=k, count=v) for k, v in species_counter.most_common()],
        trend=[TrendPoint(date=k, count=v) for k, v in trend_map.items()],
        damage_ranking=damage_ranking,
        part_distribution=part_distribution,
    )


@router.get("/risk-alert", response_model=RiskAlert)
def get_risk_alert(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """获取风险预警，超级管理员看全部，普通管理员只看自己机构"""
    # 权限过滤
    query = db.query(models.Detection)
    if current_user.role != "super_admin":
        query = query.filter(models.Detection.org_id == current_user.org_id)

    cutoff = datetime.now() - timedelta(days=RISK_WINDOW_DAYS)
    recent = [r for r in query.all() if r.created_at >= cutoff]

    if not recent:
        return RiskAlert(
            level="低",
            message="暂无异常趋势，近期未发现明显病虫害风险",
            basis=f"近 {RISK_WINDOW_DAYS} 天内无检测记录",
            generated_at=datetime.now(),
        )

    # 计算风险评分
    pest_scores: Counter = Counter()
    for r in recent:
        try:
            boxes = json.loads(r.boxes) if isinstance(r.boxes, str) else r.boxes
        except:
            boxes = []

        avg_damage = sum(b.get("damage_ratio", 0) for b in boxes) / len(boxes) if boxes else 0
        score = SEVERITY_WEIGHT.get(r.severity, 1) * (avg_damage / 100)

        try:
            pest_types = json.loads(r.pest_types) if isinstance(r.pest_types, str) else r.pest_types
        except:
            pest_types = []

        for pest in pest_types:
            pest_scores[pest] += score

    total_score = sum(pest_scores.values())
    if total_score == 0:
        return RiskAlert(
            level="低",
            message="近期未发现显著病虫害威胁",
            basis=f"近 {RISK_WINDOW_DAYS} 天风险得分 0",
            generated_at=datetime.now(),
        )

    top_pest, top_score = pest_scores.most_common(1)[0]

    low, high = RISK_THRESHOLDS
    if total_score < low:
        level = "低"
    elif total_score <= high:
        level = "中"
    else:
        level = "高"

    message = f"近 {RISK_WINDOW_DAYS} 天内 {top_pest} 相关高危害检测占比上升"
    basis = f"近 {RISK_WINDOW_DAYS} 天风险得分 {round(total_score, 1)}（{top_pest} 贡献 {round(top_score, 1)}）"

    return RiskAlert(
        level=level,
        pest_name=top_pest,
        message=message,
        basis=basis,
        generated_at=datetime.now(),
    )

