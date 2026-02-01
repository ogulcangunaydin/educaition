from pydantic import BaseModel

class Room(BaseModel):
    id: int
    user_id: int
    name: str | None

    class Config:
        from_attributes = True

class Session(BaseModel):
    id: int
    room_id: int
    name: str
    status: str
    player_ids: str
    # TODO: This union is for getting also old data which is dict type
    results: str | dict | None = None

    class Config:
        from_attributes = True
