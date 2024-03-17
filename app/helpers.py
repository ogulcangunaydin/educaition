from fastapi import HTTPException
from starlette.requests import Request

async def parse_players(request: Request):
    data = await request.form()
    if not data:
        raise HTTPException(status_code=400, detail="No player data provided")
    return dict(data)


def to_dict(model_instance):
    return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}
