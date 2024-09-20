from sqlalchemy.orm import Session

from . import models
from . import database
import requests
import json
import time
import sys 

# {
#   "response": {
#     "game_count": 140,
#     "games": [
#       {
#         "appid": 400,
#         "name": "Portal",
#         "playtime_forever": 160,
#         "img_icon_url": "cfa928ab4119dd137e50d728e8fe703e4e970aff",
#         "has_community_visible_stats": true,
#         "playtime_windows_forever": 160,
#         "playtime_mac_forever": 0,
#         "playtime_linux_forever": 0,
#         "playtime_deck_forever": 0,
#         "rtime_last_played": 1689355097,
#         "playtime_disconnected": 0
#       },]
#   }
# }

def steam_games_update(tocken,steamid):

    db = database.SessionLocal()
    last_res = db.query(models.SteamQuery).order_by(models.SteamQuery.create_time.desc()).first()

    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%s&steamid=%s&format=json&include_appinfo=1&include_played_free_games=1" % (tocken,steamid)
    results_str = requests.request("GET", url, headers={}, data={}).text
    if results_str:
        steam_query = models.SteamQuery(create_time=round(time.time()),games=results_str)
        db.add(steam_query)
        db.commit()
        db.refresh(steam_query)

    
    if last_res and results_str:
        results_json = json.loads(results_str)['response']['games']
        last_res_json = json.loads(last_res.games)['response']['games']
        last_res_dt = {i['appid']:i for i in last_res_json}
        for game in results_json:
            duartion = -1
            if game['appid'] in last_res_dt and game['playtime_forever'] > last_res_dt[game['appid']]['playtime_forever']:
                duartion = game['playtime_forever'] - last_res_dt[game['appid']]['playtime_forever']
            elif game['appid'] not in last_res_dt and game['playtime_forever'] > 0:
                duartion = game['playtime_forever']
            if duartion>0:
                record = models.SteamGameRecord(
                        appid = game['appid'],
                        game_name = game['name'],
                        playtime = game['playtime_forever'],
                        playtime_windows = game['playtime_windows_forever'],
                        playtime_mac = game['playtime_mac_forever'],
                        playtime_linux = game['playtime_linux_forever'],
                        playtime_deck = game['playtime_deck_forever'],
                        rtime_last_played = game['rtime_last_played'],
                        rtime_last_palyed_start = game['rtime_last_played'] - duartion * 60,
                        rtime_last_palyed_duration = duartion,
                    )
                db.add(record)
                db.commit()
                db.refresh(record)


def GetCurDayZero(t):
    return t - (( t + 8*60*60) % (24*60*60))

def GetPlayRecordYear():
    db = database.SessionLocal()
    record_all = db.query(models.SteamGameRecord)
    cur_time_stamp = int(time.time())
    cur_zero = GetCurDayZero(cur_time_stamp)
    a_day_stamp = 24*60*60
    daily_cnt = {}
    for i in range(365):
        daily_cnt[cur_zero-i*a_day_stamp]=0

    for record in record_all:
        print(record.rtime_last_palyed_start)
        cur_day = GetCurDayZero(record.rtime_last_palyed_start)
        next_day = cur_day + a_day_stamp

        if record.rtime_last_played > next_day:
            next_day_playtime = (record.rtime_last_played - next_day)
            cur_day_playtime = next_day - record.rtime_last_palyed_start
            print(next_day_playtime,cur_day_playtime,record.rtime_last_palyed_duration*60)
            daily_cnt[cur_day]+=int(cur_day_playtime/60)
            daily_cnt[next_day]+=int(next_day_playtime/60)
        else:
            cur_day_playtime = record.rtime_last_palyed_duration
            daily_cnt[cur_day]+=cur_day_playtime

    return daily_cnt



# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item

