"""数据集管理路由 — 基于 DatasetManager 的内置数据集列表。"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from mox.core.auth import User
from mox.routes.auth_helpers import require_optional_access

router = APIRouter(prefix="/datasets", tags=["Datasets"])

_BUILTIN_DATASETS = {
    "advbench",
    "harmbench",
    "harmbench_standard",
    "defense_test",
    "jailbreakbench",
    "owasp_llm",
}


def _format_dataset_entry(name: str, manager) -> Dict[str, Any]:
    metadata = manager.get_metadata(name)
    stats = manager.get_statistics(name)
    categories = metadata.categories or list(stats.get("category_counts", {}).keys())
    return {
        "id": name,
        "name": name.replace("_", " ").title(),
        "type": "text",
        "size": f"{metadata.size} cases",
        "samples": metadata.size,
        "tags": metadata.tags or categories[:4],
        "date": metadata.created_at or "builtin",
        "source": metadata.source,
        "description": metadata.description,
    }


@router.get("")
async def list_datasets(
    current_user: User = Depends(require_optional_access),
) -> Dict[str, List[Dict[str, Any]]]:
    """列出可用数据集（内置 + data/benchmarks 下的用户文件）。"""
    from mox.evaluation.datasets import get_dataset_manager

    manager = get_dataset_manager()
    entries = [_format_dataset_entry(name, manager) for name in manager.list_datasets()]
    return {"datasets": entries}


@router.post("/upload")
async def upload_dataset(
    current_user: User = Depends(require_optional_access),
) -> Dict[str, str]:
    """用户上传暂未实现，避免前端误以为成功。"""
    raise HTTPException(
        status_code=501,
        detail="Dataset upload is not implemented yet. Use built-in datasets or place files under data/benchmarks/.",
    )


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(require_optional_access),
) -> Dict[str, str]:
    """仅允许删除非内置数据集（当前仅内置集）。"""
    if dataset_id in _BUILTIN_DATASETS:
        raise HTTPException(status_code=403, detail="Built-in datasets cannot be deleted")
    raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
