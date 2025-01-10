from .room import Room

class TestRoom(Room):
    # Use the same table as Room
    __tablename__ = None

    __mapper_args__ = {
        'polymorphic_identity': 'test_room'
    }
