"""登录 + 兑换码。"""
import hashlib

from fastapi import APIRouter

from ..models import schemas

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResp)
def login(req: schemas.LoginReq):
    """dev：用 code（或随机串）生成稳定伪 openid。"""
    # TODO(real): 调微信 code2session：
    #   GET https://api.weixin.qq.com/sns/jscode2session
    #       ?appid=WECHAT_APPID&secret=WECHAT_SECRET&js_code=code&grant_type=authorization_code
    #   返回真实 openid / session_key。
    import uuid
    code = (req.code or uuid.uuid4().hex).strip() or uuid.uuid4().hex
    digest = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
    return schemas.LoginResp(openid=f"dev_{digest}")


# 演示用完整权益兑换码（V3）。TODO(real): 改为校验码库/绑定 openid/防重复核销。
FULL_CODE = "anysxzn2026"


@router.post("/redeem", response_model=schemas.RedeemResp)
def redeem(req: schemas.RedeemReq):
    """校验固定演示码 anysxzn2026（忽略大小写）→ 解锁完整权益。"""
    code = (req.code or "").strip()
    if not code:
        return schemas.RedeemResp(ok=False, message="请输入兑换码")
    if code.lower() != FULL_CODE:
        return schemas.RedeemResp(ok=False, message="兑换码不正确，请检查后重试")
    return schemas.RedeemResp(ok=True, unlocked=True)
