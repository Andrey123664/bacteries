from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
import psycopg2

engine = create_engine('postgresql+psycopg2://postgres:Postgre12345@localhost/bacteries')


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    address = Column(String)
    x = Column(Integer, default=500)
    y = Column(Integer, default=500)
    size = Column(Integer, default=50)
    errors = Column(Integer, default=0)
    abs_speed = Column(Integer, default=1)
    speed_x = Column(Integer, default=0)
    speed_y = Column(Integer, default=0)
    color = Column(String, default='green')
    w_vision = Column(Integer, default=800)
    h_vision = Column(Integer, default=600)

    def __init__(self, name, address):
        self.name = name
        self.address = address


if __name__ == '__main__':
    Base.metadata.create_all(engine)
