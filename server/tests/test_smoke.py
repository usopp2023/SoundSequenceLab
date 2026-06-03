"""冒烟测试：覆盖每个路由返回 200 + 关键字段，并跑一条完整链路。"""
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_generate

OPENID = "test_user_001"
HEADERS = {"X-Openid": OPENID}


@pytest.fixture(scope="module")
def client():
    # 缩短 job 延迟，加速测试
    routes_generate._JOB_DELAY_SEC = 0.3
    with TestClient(app) as c:
        yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


def test_login(client):
    r = client.post("/api/login", json={"code": "abc123"})
    assert r.status_code == 200
    assert r.json()["openid"].startswith("dev_")
    # 同 code 稳定
    r2 = client.post("/api/login", json={"code": "abc123"})
    assert r2.json()["openid"] == r.json()["openid"]


def test_upload(client):
    files = {"file": ("clip.wav", b"RIFFfake-audio-bytes", "audio/wav")}
    r = client.post("/api/upload", files=files, data={"openid": OPENID})
    assert r.status_code == 200
    body = r.json()
    assert body["text"]
    assert body["audioUrl"].startswith("/static/uploads/")


def _assert_valid_result(res: dict):
    assert res["resultId"].startswith("r_")
    assert set(res["persona"].keys()) == {"name", "en"}
    assert isinstance(res["report"], str) and res["report"]
    assert len(res["dims"]) == 4
    expected_labels = [
        ("独处", "共处"),
        ("涌动", "平静"),
        ("直说", "含蓄"),
        ("回望过去", "望向远方"),
    ]
    for d, (left, right) in zip(res["dims"], expected_labels):
        assert d["left"] == left and d["right"] == right
        assert 0 <= d["value"] <= 100
        assert d["activeSide"] == ("left" if d["value"] < 50 else "right")
    assert res["curveUrl"] == ""
    assert res["music"]["url"].startswith("/static/fallback_music/")
    assert res["music"]["duration"] >= 1


def test_full_flow(client):
    # 1) generate
    payload = {
        "answers": [
            {"q": 0, "text": "我最想待在黄昏的海边。"},
            {"q": 1, "text": "有件事放在心里没说。"},
            {"q": 2, "text": "有句话一直想说却没说出口。"},
        ],
        "audioRefs": [],
    }
    r = client.post("/api/generate", json=payload, headers=HEADERS)
    assert r.status_code == 200
    job_id = r.json()["jobId"]
    assert job_id.startswith("j_")

    # 2) 轮询：先 running，后 done
    saw_running = False
    result = None
    for _ in range(40):
        rj = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
        assert rj.status_code == 200
        body = rj.json()
        assert body["steps"] == [
            "正在听你说的话……", "读出你藏起来的情绪……", "正在谱一段曲子……",
        ]
        if body["status"] == "running":
            saw_running = True
            assert body["result"] is None
        elif body["status"] == "done":
            result = body["result"]
            break
        time.sleep(0.1)
    assert result is not None, "job never reached done"
    _assert_valid_result(result)
    result_id = result["resultId"]

    # 3) results/{id} 取回
    rr = client.get(f"/api/results/{result_id}", headers=HEADERS)
    assert rr.status_code == 200
    _assert_valid_result(rr.json())
    assert rr.json()["resultId"] == result_id

    # 4) 档案里能看到这条
    ra = client.get("/api/me/archive", headers=HEADERS)
    assert ra.status_code == 200
    assert any(it["resultId"] == result_id for it in ra.json()["items"])

    # 5) plaza 列表
    rp = client.get("/api/plaza?n=6", headers=HEADERS)
    assert rp.status_code == 200
    items = rp.json()["items"]
    assert len(items) == 6
    pid = items[0]["id"]

    # 6) plaza 详情
    rd = client.get(f"/api/plaza/{pid}", headers=HEADERS)
    assert rd.status_code == 200
    detail = rd.json()
    assert detail["music"]["url"].startswith("/static/fallback_music/")

    # 7) like 切换 + collected
    rl = client.post(f"/api/plaza/{pid}/like", headers=HEADERS)
    assert rl.status_code == 200
    assert rl.json()["liked"] is True
    rc = client.get("/api/me/collected", headers=HEADERS)
    assert any(it["plazaId"] == pid for it in rc.json()["items"])
    # 再点一次取消
    rl2 = client.post(f"/api/plaza/{pid}/like", headers=HEADERS)
    assert rl2.json()["liked"] is False

    # 8) similarity（按 me 人格 + 对方 plazaId）
    me_name = result["persona"]["name"]
    rs = client.post(
        "/api/similarity",
        json={"meName": me_name, "otherPlazaId": pid},
        headers=HEADERS,
    )
    assert rs.status_code == 200
    sim = rs.json()
    assert 0 <= sim["score"] <= 100
    assert sim["you"]["name"] == me_name
    assert sim["reading"]

    # 9) redeem：正确码成功 / 错码失败 / 空码失败
    rok = client.post("/api/redeem", json={"code": "anysxzn2026"})
    assert rok.status_code == 200 and rok.json()["ok"] is True
    assert rok.json()["unlocked"] is True
    rwrong = client.post("/api/redeem", json={"code": "wrong-code"})
    assert rwrong.json()["ok"] is False
    rfail = client.post("/api/redeem", json={"code": ""})
    assert rfail.json()["ok"] is False


def test_offline_claim_flow(client):
    # 1) 现场设备（kioskdev）生成一条结果
    payload = {
        "answers": [
            {"q": 0, "text": "我最想待在黄昏的海边。"},
            {"q": 1, "text": "有件事放在心里没说。"},
            {"q": 2, "text": "有句话一直想说却没说出口。"},
        ],
        "audioRefs": [],
    }
    kiosk_h = {"X-Openid": "kioskdev"}
    rg = client.post("/api/generate", json=payload, headers=kiosk_h)
    assert rg.status_code == 200
    job_id = rg.json()["jobId"]

    result_id = None
    for _ in range(40):
        rj = client.get(f"/api/jobs/{job_id}", headers=kiosk_h)
        assert rj.status_code == 200
        body = rj.json()
        if body["status"] == "done":
            result_id = body["result"]["resultId"]
            break
        time.sleep(0.1)
    assert result_id is not None, "job never reached done"

    # 2) 现场出认领码
    rc = client.post("/api/kiosk/claim-code", json={"resultId": result_id})
    assert rc.status_code == 200
    cbody = rc.json()
    assert cbody["ok"] is True
    code = cbody["code"]
    assert isinstance(code, str) and len(code) == 8
    # 易读字符集：无 O/0/I/1/L
    assert not (set(code) & set("O0I1L"))

    # 3) 用户本人（userA）输码认领
    user_h = {"X-Openid": "userA"}
    rr = client.post("/api/redeem", json={"code": code}, headers=user_h)
    assert rr.status_code == 200
    rbody = rr.json()
    assert rbody["ok"] is True
    assert rbody["claimed"] is True
    assert rbody["resultId"] == result_id
    assert rbody["result"] is not None
    _assert_valid_result(rbody["result"])

    # 4) 认领后进入 userA 档案
    ra = client.get("/api/me/archive", headers=user_h)
    assert ra.status_code == 200
    assert any(it["resultId"] == result_id for it in ra.json()["items"])

    # 5) 同码再领 → 一次性，失败
    rr2 = client.post("/api/redeem", json={"code": code}, headers=user_h)
    assert rr2.status_code == 200
    assert rr2.json()["ok"] is False

    # 6) 演示码仍可用（claimed=false）
    rdemo = client.post("/api/redeem", json={"code": "anysxzn2026"}, headers=user_h)
    assert rdemo.status_code == 200
    assert rdemo.json()["ok"] is True
    assert rdemo.json()["claimed"] is False

    # 不存在的 resultId 出码失败
    rbad = client.post("/api/kiosk/claim-code", json={"resultId": "r_nope"})
    assert rbad.json()["ok"] is False


def test_similarity_by_name(client):
    r = client.post(
        "/api/similarity",
        json={"meName": "黄昏独行者", "otherName": "深海回声者"},
    )
    assert r.status_code == 200
    assert r.json()["other"]["name"] == "深海回声者"
