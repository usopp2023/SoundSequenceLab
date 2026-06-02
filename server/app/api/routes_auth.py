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


@router.post("/redeem", response_model=schemas.RedeemResp)
def redeem(req: schemas.RedeemReq):
    """占位：任意非空码视为有效。"""
    code = (req.code or "").strip()
    if not code:
        return schemas.RedeemResp(ok=False, message="兑换码无效")
    # TODO(real): 校验码是否存在/未使用，绑定到当前 openid。
    return schemas.RedeemResp(
        ok=True,
        unlocked=True,
        badge="线下完整体验者",
        perkCode="码 5530",
    )
