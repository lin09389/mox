"""防御相关路由"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from mox.defense import InputFilter, OutputFilter, SystemPromptHardening
from mox.core.database import Database
from mox.core.auth import get_current_active_user, User

router = APIRouter(prefix="/defense", tags=["Defense"])


# ============ 请求模型 ============

class ScanRequest(BaseModel):
    text: str
    scan_type: str = "input"


class DefenseRequest(BaseModel):
    input_text: str
    defense_types: List[str] = ["input_filter", "output_filter"]


# ============ 依赖 ============

_db = Database()


# ============ 辅助函数 ============

def _analyze_detection_patterns(detected_patterns: List[str]) -> Dict[str, Any]:
    """分析检测到的模式"""
    if not detected_patterns:
        return {
            "total_patterns": 0,
            "severity_breakdown": {},
            "categories": [],
            "risk_summary": "未检测到威胁模式",
        }

    severity_map = {
        "prompt_injection": {"severity": "高", "category": "注入攻击"},
        "jailbreak": {"severity": "极高", "category": "绕过攻击"},
        "role_play": {"severity": "中", "category": "社工攻击"},
        "encoding_attack": {"severity": "高", "category": "编码攻击"},
        "context_injection": {"severity": "中", "category": "注入攻击"},
        "system_override": {"severity": "极高", "category": "权限提升"},
        "base64": {"severity": "高", "category": "编码攻击"},
        "refusal_suppression": {"severity": "中", "category": "对抗技术"},
    }

    severity_counts = {"极高": 0, "高": 0, "中": 0, "低": 0}
    categories = set()

    for pattern in detected_patterns:
        pattern_lower = pattern.lower()
        for key, info in severity_map.items():
            if key in pattern_lower:
                severity_counts[info["severity"]] += 1
                categories.add(info["category"])
                break

    highest_severity = "低"
    for sev in ["极高", "高", "中", "低"]:
        if severity_counts[sev] > 0:
            highest_severity = sev
            break

    return {
        "total_patterns": len(detected_patterns),
        "severity_breakdown": severity_counts,
        "categories": list(categories),
        "highest_severity": highest_severity,
        "risk_summary": f"检测到 {len(detected_patterns)} 个威胁模式，最高严重程度: {highest_severity}",
    }


def _generate_defense_recommendations(
    is_malicious: bool, confidence: float, detected_patterns: List[str]
) -> List[Dict[str, str]]:
    """生成防御建议"""
    recommendations = []

    if is_malicious and confidence > 0.8:
        recommendations.append({
            "priority": "紧急",
            "category": "立即行动",
            "content": "高置信度检测到恶意内容，建议立即阻止该请求",
        })
    elif is_malicious:
        recommendations.append({
            "priority": "高",
            "category": "审查建议",
            "content": "检测到可疑内容，建议进行人工审查",
        })
    else:
        recommendations.append({
            "priority": "低",
            "category": "安全状态",
            "content": "未检测到明显威胁，内容可以放行",
        })

    if any("injection" in p.lower() for p in detected_patterns):
        recommendations.append({
            "priority": "高",
            "category": "专项加固",
            "content": "检测到注入攻击，建议部署专门的注入检测器",
        })

    if any("jailbreak" in p.lower() or "role_play" in p.lower() for p in detected_patterns):
        recommendations.append({
            "priority": "高",
            "category": "专项加固",
            "content": "检测到越狱尝试，建议增强系统提示词加固",
        })

    return recommendations


# ============ 路由端点 ============

@router.post("/scan")
async def scan_input(
    request: ScanRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """扫描输入/输出内容"""
    try:
        if request.scan_type == "input":
            input_filter = InputFilter()
            result = await input_filter.detect(request.text)
            scan_type_name = "输入检测"
            defense_type = "input_filter"
        else:
            output_filter = OutputFilter()
            result = await output_filter.detect(request.text)
            scan_type_name = "输出检测"
            defense_type = "output_filter"

        # 威胁等级评估
        threat_levels = {
            (0.0, 0.3): {"level": "低风险", "color": "green", "action": "允许通过"},
            (0.3, 0.6): {"level": "中风险", "color": "yellow", "action": "警告并记录"},
            (0.6, 0.8): {"level": "高风险", "color": "orange", "action": "需要审查"},
            (0.8, 1.0): {"level": "严重风险", "color": "red", "action": "立即阻止"},
        }

        threat_info = {"level": "未知", "color": "gray", "action": "待评估"}
        for (low, high), info in threat_levels.items():
            if low <= result.confidence < high:
                threat_info = info
                break
        if result.confidence >= 0.8:
            threat_info = threat_levels[(0.8, 1.0)]

        pattern_analysis = _analyze_detection_patterns(result.detected_patterns)

        return {
            "success": True,
            "scan_info": {
                "scan_type": request.scan_type,
                "scan_type_name": scan_type_name,
                "defense_type": defense_type,
            },
            "result": {
                "is_malicious": result.is_malicious,
                "confidence": round(result.confidence, 4),
                "confidence_percent": f"{result.confidence * 100:.1f}%",
                "threat_level": threat_info["level"],
                "threat_color": threat_info["color"],
                "recommended_action": threat_info["action"],
            },
            "detected_patterns": result.detected_patterns,
            "pattern_analysis": pattern_analysis,
            "sanitized_input": result.sanitized_input,
            "recommendations": _generate_defense_recommendations(
                result.is_malicious, result.confidence, result.detected_patterns
            ),
            "text_stats": {
                "input_length": len(request.text),
                "word_count": len(request.text.split()),
                "pattern_count": len(result.detected_patterns),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Defense scan failed")


@router.post("/sanitize")
async def sanitize_input(
    request: ScanRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """净化输入内容"""
    try:
        input_filter = InputFilter()
        result = await input_filter.detect(request.text)

        if result.is_malicious:
            sanitized = await input_filter.sanitize(request.text)
        else:
            sanitized = request.text

        return {
            "original": request.text,
            "sanitized": sanitized,
            "was_malicious": result.is_malicious,
            "detected_patterns": result.detected_patterns,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Sanitization failed")


@router.get("/history")
async def get_defense_history(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """获取防御历史"""
    try:
        records = await _db.get_defense_records(limit=limit)
        return {
            "records": [
                {
                    "id": r.id,
                    "defense_type": r.defense_type,
                    "input_text": r.input_text,
                    "output_text": r.output_text,
                    "is_malicious": r.is_malicious,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        }
    except Exception as e:
        return {"records": []}


@router.post("/injection/detect")
async def detect_injection(
    request: ScanRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """检测注入攻击"""
    try:
        from mox.defense.injection_detector import PromptInjectionDetector

        detector = PromptInjectionDetector()
        result = await detector.detect(request.text)

        return {
            "is_malicious": result.is_malicious,
            "confidence": result.confidence,
            "detected_patterns": result.detected_patterns,
        }
    except Exception as e:
        return {"is_malicious": False, "confidence": 0, "error": "Injection detection failed"}


@router.get("/logs")
async def get_defense_logs() -> List[Dict[str, Any]]:
    """获取防御日志"""
    return [
        {"defense_type": "input_filter", "confidence": 0.85, "blocked": True},
        {"defense_type": "injection_detector", "confidence": 0.12, "blocked": False},
    ]