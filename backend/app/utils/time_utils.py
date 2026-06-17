from datetime import datetime
from zoneinfo import ZoneInfo

def get_now_sp():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))

def get_now_sp_naive():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
