from .room import Room

class GameRoom(Room):
    # Use the same table as Room
    __tablename__ = None

    __mapper_args__ = {
        'polymorphic_identity': 'game_room'
    }
