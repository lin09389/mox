"""Canvas 路由与引擎测试"""

import pytest
from fastapi.testclient import TestClient

from mox.api import app
from mox.workflows.canvas_engine import engine, CanvasDAG, NodeConfig


client = TestClient(app)


def test_canvas_dag_topological_sort():
    dag = CanvasDAG(
        nodes=[
            NodeConfig(id="a", type="dataset", data={"label": "test"}),
            NodeConfig(id="b", type="agent", data={"strategy": "jailbreak"}),
        ],
        edges=[{"source": "a", "target": "b"}],
    )
    sorted_nodes = engine._topological_sort(dag)
    assert sorted_nodes[0].id == "a"
    assert sorted_nodes[1].id == "b"


def test_canvas_deploy_endpoint():
    response = client.post(
        "/api/v1/canvas/deploy",
        json={
            "nodes": [
                {"id": "d1", "type": "dataset", "data": {"label": "test"}},
            ],
            "edges": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data