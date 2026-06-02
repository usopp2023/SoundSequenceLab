"""路由公共依赖。"""
from fastapi import Header


def get_openid(x_openid: str = Header(default="anon")) -> str:
    """从请求头 X-Openid 取用户标识。dev 直接信任该值；缺失则用 'anon'。"""
    return x_openid or "anon"
