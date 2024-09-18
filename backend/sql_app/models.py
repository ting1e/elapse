from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class SteamQuery(Base):
    __tablename__ = "steam_owned_game_query"
    id = Column(Integer, primary_key=True)
    create_time = Column(Integer)
    games = Column(String)


class SteamGameRecord(Base):
    __tablename__ = "steam_owned_game_record"
    id = Column(Integer, primary_key=True)
    appid = Column(String)
    game_name = Column(String)
    playtime = Column(Integer)
    playtime_windows = Column(Integer)
    playtime_mac = Column(Integer)
    playtime_linux = Column(Integer)
    playtime_deck = Column(Integer)
    rtime_last_played = Column(Integer)
    rtime_last_palyed_start = Column(Integer)
    rtime_last_palyed_duration = Column(Integer)

