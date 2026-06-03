"""现场体验机（H5 kiosk）：为某次结果出一张线下认领码 + 二维码。"""
import io

import qrcode
import qrcode.image.svg
from fastapi import APIRouter, Response

from ..models import schemas
from ..store import db

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])


@router.post("/claim-code", response_model=schemas.ClaimCodeResp)
def make_claim_code(req: schemas.ClaimCodeReq):
    """现场设备调用：传 resultId，生成一次性认领码 + 对应二维码地址。"""
    row = db.get_result(req.resultId)
    if not row:
        return schemas.ClaimCodeResp(ok=False, message="结果不存在")
    code = db.create_claim_code(req.resultId)
    return schemas.ClaimCodeResp(ok=True, code=code, qrUrl=f"/api/kiosk/claim-qr?code={code}")


@router.get("/claim-qr")
def claim_qr(code: str):
    """把认领码编码成二维码（SVG）。
    现场屏幕显示，用户在小程序里用 wx.scanCode 扫一下即可认领（不需要 AppID）。
    TODO(real): 拿到正式 AppID 后，这里可换成微信「小程序码」(wxacode.getUnlimited)，
    用微信冷扫码即可直接打开小程序并自动认领。
    """
    img = qrcode.make(code, image_factory=qrcode.image.svg.SvgImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return Response(content=buf.getvalue(), media_type="image/svg+xml")
