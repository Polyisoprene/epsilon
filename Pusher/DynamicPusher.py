import asyncio
import base64
import json
import time
import traceback
from io import BytesIO

from dynamicrender.DynamicChecker import Item
from dynamicrender.Renderer import BiliRender
from nonebot import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..BliApi import Api
from ..DataManager import DataManage
from ..MessageManager import MessageSender


class PushDynamic:
    def __init__(self, cookie):
        self.cookie = cookie
        self.page = 1
        self.offset = None

    async def pusher(self):
        items = await Api().dynamic_new(self.cookie, self.page, offset=self.offset)
        try:
            offset_item = Item(**items[-1])
            self.offset = offset_item.id_str
            ts = offset_item.modules.module_author.pub_ts
            self.page += 1
            tasks = []
            for item in items:
                item = Item(**item)
                tasks.append(self.push_data_process(item))
            await asyncio.gather(*tasks)
            with DataManage() as del_dynamic_id:
                await del_dynamic_id.del_dynamic_id(int(time.time()) - 10800)
            if time.time() - ts < 20:
                await self.pusher()
        except:
            logger.error(traceback.print_exc())

    async def push_data_process(self, item: Item):
        pub_ts = item.modules.module_author.pub_ts
        mid = item.modules.module_author.mid
        if time.time() - pub_ts < 10600:
            dynamic_id = item.id_str
            with DataManage() as compare:
                result = await compare.acquire_dynamic_id(dynamic_id)
            if not result:
                with DataManage() as store:
                    await store.store_dynamic_id(dynamic_id, pub_ts)
                if item.type != "DYNAMIC_TYPE_LIVE_RCMD":
                    with DataManage() as acquire:
                        subscribe_info = await acquire.acquire_subinfo_by_uid(mid)
                    if subscribe_info:
                        all_sub_group = json.loads(subscribe_info[3])
                        message = await self.__formate_message(item)
                        tasks = []
                        for k, v in all_sub_group.items():
                            tasks.append(self.__send_checker(message, k, v))
                        await asyncio.gather(*tasks)


    async def __formate_message(self, item: Item) -> Message:
        start = time.time()
        img = await BiliRender(item).render()
        logger.info("???????????????: " + str(time.time() - start))
        img_byte = BytesIO()
        img.save(img_byte, format='PNG')
        img = str(base64.b64encode(img_byte.getvalue()), "utf8")
        dtype = item.type
        url = "https://t.bilibili.com/" + item.id_str
        name = item.modules.module_author.name
        type_msg = {
            "DYNAMIC_TYPE_WORD": "??????????????????",
            "DYNAMIC_TYPE_DRAW": "?????????????????????",
            "DYNAMIC_TYPE_AV": "????????????????????????",
            "DYNAMIC_TYPE_LIVE_RCMD": "?????????????????????",
            "DYNAMIC_TYPE_LIVE": "?????????????????????",
            "DYNAMIC_TYPE_ARTICLE": "??????????????????",
            "DYNAMIC_TYPE_COMMON_VERTICAL": "??????????????????",
            "DYNAMIC_TYPE_COURSES_SEASON": "?????????????????????",
            "DYNAMIC_TYPE_MEDIALIST": "??????????????????",
            "DYNAMIC_TYPE_PGC": "??????????????????",
            "DYNAMIC_TYPE_MUSIC": "??????????????????",
            "DYNAMIC_TYPE_COMMON_SQUARE": "??????????????????",
            "DYNAMIC_TYPE_FORWARD": "?????????????????????"
        }
        message = (
                          f"{name}" + f"{type_msg.get(dtype, type_msg['DYNAMIC_TYPE_WORD'])}:\n\n" + "????????????" + f"{url}") + "\n" + MessageSegment.image(
            f"base64://{img}")

        return message

    async def __send_checker(self, message: Message, position, group_sub_info):
        tasks = []
        for k, v in group_sub_info.items():
            tasks.append(self.__message_sender(message, position, k, v))
        await asyncio.gather(*tasks)

    async def __message_sender(self, message: Message, position, bot_id, sub_info):
        """????????????"""
        # ??????bot????????????
        try:
            bot_status = await self.__check_bot_status(position, bot_id)
            if bot_status:
                if sub_info["DynamicOn"] == 1:
                    if position.isdigit():
                        await MessageSender(message=message, bot_id=bot_id).send_to("group", position)
                    else:
                        position_dic = json.loads(position)
                        await MessageSender(message=message, bot_id=bot_id).send_to("guild",
                                                                                    guild_id=position_dic["guild_id"],
                                                                                    channel_id=position_dic[
                                                                                        "channel_id"])
        except Exception as e:
            logger.error(traceback.print_exc())

    async def __check_bot_status(self, position, bot_id) -> bool:
        """????????????????????????"""
        # ????????????????????????????????????
        bot_id = int(bot_id)
        with DataManage() as switch_getter:
            switch = await switch_getter.acquire_SwitchStatus(position, bot_id)
        # ??????????????????????????????????????????
        if not switch:
            with DataManage() as switch_setter:
                await switch_setter.store_SwitchStatus(position, bot_id)
            return True
        else:
            if switch[0] == 1:
                return True
            else:
                return False
