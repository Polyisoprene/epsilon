import traceback
from typing import Union, Optional

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent, Bot, Message
from nonebot_plugin_guild_patch import GuildMessageEvent


class MessageSender:
    def __init__(self, bot: Optional[Bot] = None,
                 event: Union[GuildMessageEvent, GroupMessageEvent, None] = None,
                 message: Union[MessageSegment, Message, str] = None, bot_id: str = None):
        self.__bot = bot or nonebot.get_bot(self_id=bot_id)
        self.__event = event
        self.__message = message
        self.__send_method = {"group": self.__send_group_message, "guild": self.__send_guild_message}

    async def send_back(self) -> None:
        try:
            await self.__send_method[str(self.__event.message_type)]()
        except Exception as e:
            logger.error(traceback.print_exc())

    async def send_to(self, send_type: str, group_id=None, channel_id=None, guild_id=None) -> None:

        if send_type == "group":
            await self.__send_method[send_type](group_id)
        elif send_type == "guild":
            await self.__send_method[send_type](guild_id, channel_id)
        else:
            raise Exception("Unknown message type")

    async def __send_guild_message(self, guild_id: Optional[int] = None, channel_id: Optional[int] = None) -> None:
        if self.__event:
            await self.__bot.call_api("send_guild_channel_msg",
                                      **{"guild_id": self.__event.guild_id,
                                         "channel_id": self.__event.channel_id,
                                         "message": self.__message})
        else:
            await self.__bot.call_api("send_guild_channel_msg",
                                      **{"guild_id": guild_id,
                                         "channel_id": channel_id,
                                         "message": self.__message})

    async def __send_group_message(self, group_id: Optional[int] = None) -> None:
        if self.__event:
            await self.__bot.call_api("send_group_msg",**{"group_id": self.__event.group_id, "message": self.__message})
        else:
            await self.__bot.call_api("send_group_msg", **{"group_id": group_id, "message": self.__message})
