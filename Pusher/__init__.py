import json

from nonebot import require

from .DynamicPusher import PushDynamic
from .LivePusher import PushLive
from ..DataManager import DataManage

scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job('cron', second='*/10', id='dynamic_push', max_instances=10)
async def _():
    with DataManage() as acquire:
        cookie = await acquire.acquire_cookie()
        all_sub_info = await acquire.acquire_full_subinfo()
    if cookie and all_sub_info:
        cookie = json.loads(cookie[0])
        await PushDynamic(cookie).pusher()


@scheduler.scheduled_job('cron', second='*/15', id='live_push', max_instances=10)
async def _():
    with DataManage() as acquire:
        cookie = await acquire.acquire_cookie()
        all_sub_info = await acquire.acquire_full_subinfo()
    if cookie and all_sub_info:
        cookie = json.loads(cookie[0])
        await PushLive(cookie, all_sub_info).pusher()
