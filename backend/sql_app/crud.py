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

def steam_games_update(token: str, steamid: str):
    """
    从Steam API获取拥有的游戏信息，与上次记录比较，并将新增的游戏时长存入数据库。
    - 增加了完整的错误处理和数据库会话管理。
    - 优化了数据库提交逻辑，改为批量提交。
    """
    db: Session = database.SessionLocal()
    try:
        # 1. 获取上次的查询结果
        last_res = db.query(models.SteamQuery).order_by(models.SteamQuery.create_time.desc()).first()

        # 2. 请求Steam API
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={token}&steamid={steamid}&format=json&include_appinfo=1&include_played_free_games=1"
        
        try:
            response = requests.get(url, timeout=15) # 使用 get 并设置超时
            response.raise_for_status()  # 如果状态码不是 2xx, 会抛出 HTTPError
            results_str = response.text
            results_data = response.json() # 直接解析JSON
        except requests.exceptions.RequestException as e:
            print(f"请求 Steam API 时发生网络错误: {e}")
            return
        except json.JSONDecodeError:
            print(f"无法解析 Steam API 返回的 JSON 数据。")
            return

        # 3. 将本次查询结果存入数据库
        if results_str:
            steam_query = models.SteamQuery(create_time=round(time.time()), games=results_str)
            db.add(steam_query)
            # 注意：这里的 commit 会和后面的记录一起提交

        # 4. 比较两次结果，计算并存储游戏时长记录
        if last_res and 'response' in results_data and 'games' in results_data['response']:
            current_games_json = results_data['response']['games']
            
            try:
                last_res_json = json.loads(last_res.games)['response']['games']
            except (json.JSONDecodeError, KeyError):
                # 如果旧数据格式有问题，则无法比较，直接跳过
                last_res_json = []

            last_res_dt = {game['appid']: game for game in last_res_json}
            new_records = []

            for game in current_games_json:
                duration = -1
                appid = game.get('appid')
                if not appid:
                    continue

                # 修正了拼写错误: duartion -> duration
                # 检查游戏是否已存在，并且游戏时间增加了
                if appid in last_res_dt and game.get('playtime_forever', 0) > last_res_dt[appid].get('playtime_forever', 0):
                    duration = game['playtime_forever'] - last_res_dt[appid]['playtime_forever']
                # 检查是否是新玩的游戏
                elif appid not in last_res_dt and game.get('playtime_forever', 0) > 0:
                    duration = game['playtime_forever']
                
                if duration > 0:
                    record = models.SteamGameRecord(
                        appid=str(game['appid']),
                        game_name=game.get('name', 'Unknown'),
                        playtime=game.get('playtime_forever', 0),
                        playtime_windows=game.get('playtime_windows_forever', 0),
                        playtime_mac=game.get('playtime_mac_forever', 0),
                        playtime_linux=game.get('playtime_linux_forever', 0),
                        playtime_deck=game.get('playtime_deck_forever', 0),
                        rtime_last_played=game.get('rtime_last_played', 0),
                        rtime_last_played_start=game.get('rtime_last_played', 0) - duration * 60,
                        rtime_last_played_duration=duration,
                    )
                    new_records.append(record)
            
            if new_records:
                db.add_all(new_records) # 优化：使用 add_all 批量添加
        
        db.commit() # 优化：所有操作完成后，只提交一次
        # db.refresh() 只能用于单个对象，如果需要获取ID，需要单独处理
        
    finally:
        db.close() # 关键：确保数据库会话总是被关闭


def get_cur_day_zero(t: int, timezone_offset_hours: int = 8) -> int:
    """
    获取指定时间戳当天的零点时间戳（考虑时区）。
    使用 timezone_offset_hours = 8 来处理 UTC+8 时区。
    """
    return t - (t + timezone_offset_hours * 3600) % 86400


def get_play_record_year() :
    """
    获取过去365天内，每天的游戏总时长（单位：分钟）。
    - 修复了 KeyError bug。
    - 增加了数据库会话管理。
    """
    db: Session = database.SessionLocal()
    try:
        record_all = db.query(models.SteamGameRecord).all()
        
        cur_time_stamp = int(time.time())
        a_day_stamp = 24 * 60 * 60
        
        # 使用 get_cur_day_zero 函数来保持一致性
        cur_zero = get_cur_day_zero(cur_time_stamp)

        daily_cnt = {cur_zero - i * a_day_stamp: 0 for i in range(365)}

        for record in record_all:
            start_day_zero = get_cur_day_zero(record.rtime_last_played_start)
            
            # 检查游戏会话是否跨天
            if record.rtime_last_played > start_day_zero + a_day_stamp:
                # 跨天了，需要拆分时间
                next_day_zero = start_day_zero + a_day_stamp
                
                cur_day_playtime_seconds = next_day_zero - record.rtime_last_played_start
                next_day_playtime_seconds = record.rtime_last_played - next_day_zero

                # 修复BUG：在增加时长前，检查日期是否存在于字典中
                if start_day_zero in daily_cnt:
                    daily_cnt[start_day_zero] += round(cur_day_playtime_seconds / 60)
                if next_day_zero in daily_cnt:
                    daily_cnt[next_day_zero] += round(next_day_playtime_seconds / 60)
            else:
                # 未跨天，直接增加时长
                # 修复BUG：在增加时长前，检查日期是否存在于字典中
                if start_day_zero in daily_cnt:
                    daily_cnt[start_day_zero] += record.rtime_last_played_duration

        return daily_cnt
    finally:
        db.close() # 关键：确保数据库会话总是被关闭


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

