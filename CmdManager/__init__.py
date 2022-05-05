import asyncio
import base64
import json
import os
import time
import traceback
from io import BytesIO
from typing import Union
from urllib.parse import urlsplit
import re
from dynamicrender.Renderer import BiliRender
import qrcode
from PIL import ImageFont, Image, ImageDraw
from nonebot import Bot
from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment, GroupDecreaseNoticeEvent
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..BliApi import ApiWebLogin, Api
from ..DataManager import DataManage
from ..MessageManager import MessageSender


async def check_bot_status(*args, **kwargs) -> bool:
    """检查开关状态函数"""
    # 查看这个群是否开启了开关
    if kwargs:
        event: Union[GroupMessageEvent, GuildMessageEvent] = kwargs["event"]
        bot: Bot = kwargs["bot"]
    else:
        event: Union[GroupMessageEvent, GuildMessageEvent] = args[0]
        bot: Bot = args[1]
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = int(bot.self_id)
    with DataManage() as switch_getter:
        switch = await switch_getter.acquire_SwitchStatus(position, bot_id)
    # 如果没找到开关就新添一个开关
    if not switch:
        with DataManage() as switch_setter:
            await switch_setter.store_SwitchStatus(position, bot_id)
        return True
    else:
        if switch[0] == 1:
            return True
        else:
            return False


async def check_cookie():
    with DataManage() as require:
        cookie = await require.acquire_cookie()
    if not cookie:
        return "未登录"
    if cookie[1] + 15550000 < int(time.time()):
        return "登录过期"
    cookie = json.loads(cookie[0])
    del cookie["Expires"]
    return cookie


def bot_checker(func):
    """检查bot开关的装饰器"""
    async def inner(*args, **kwargs):
        bot_status = await check_bot_status(*args, **kwargs)
        return await func(*args, **kwargs) if bot_status else ""
    return inner


async def make_qrcode(url) -> Union[MessageSegment, None]:
    qr_url = url
    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=10, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte = BytesIO()
    img.save(img_byte, format='PNG')
    binary_content = img_byte.getvalue()
    ls_f = str(base64.b64encode(binary_content), "utf8")
    return MessageSegment.image(f"base64://{ls_f}")


@bot_checker
async def login(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot):
    """登录函数"""
    log_in = ApiWebLogin()
    log_info = await log_in.get_oauth_key()
    log_in.oauth_key = log_info[1]
    log_pic = await make_qrcode(log_info[0])
    time_line = log_info[2]
    await MessageSender(event=event, bot=bot, message=log_pic).send_back()
    try:
        while True:
            if time.time() - time_line > 150:
                message = "登录超时"
                break
            else:
                result = await log_in.get_cookie()
                if "code" in result.keys() and result["code"] == 0:
                    cookie = {}
                    ts = result["ts"]
                    url = result["data"]["url"]
                    query = urlsplit(url).query
                    for s in query.split('&'):
                        key, value = s.split("=")
                        cookie[key] = value
                    cookie.pop("gourl")
                    message = "登录成功"
                    with DataManage() as store:
                        await store.delete_old_cookie()
                        await store.store_cookie(json.dumps(cookie), ts)
                    break
                await asyncio.sleep(5)
    except:
        logger.error(traceback.print_exc())
        message = "登录错误"
    return message


@bot_checker
async def add_sub(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot, uid: str):
    """添加订阅的函数"""
    with DataManage() as get:
        sub_info_uid = await get.acquire_subinfo_by_uid(uid)
    # 所有群都没订阅过
    bot_id = bot.self_id
    if not sub_info_uid:
        uid_info = await Api().get_uid_info(uid)
        if not uid_info:
            message = "UID错误"
        else:
            cookie = await check_cookie()
            if isinstance(cookie, dict):
                logger.info(cookie)
                follow_result = await Api().change_follow(uid, 1, cookie)
                if isinstance(follow_result, bool):
                    if event.message_type == "group":
                        sub_group = {str(event.group_id): {bot_id: {"DynamicOn": 1, "LiveOn": 1}}}
                        sub_group = json.dumps(sub_group)
                    else:
                        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
                        sub_group = json.dumps({position: {bot_id: {"DynamicOn": 1, "LiveOn": 1}}})
                    with DataManage() as store:
                        await store.store_subinfo(int(uid), uid_info["nick_name"], live_status=uid_info["liveStatus"],
                                                  sub_group=sub_group)
                    message = f"成功添加：{uid_info['nick_name']}({uid})"
                else:
                    message = follow_result
            else:
                message = cookie
    else:
        if event.message_type == "group":
            position = str(event.group_id)
        else:
            position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
        sub_group = json.loads(sub_info_uid[3])
        if position in sub_group.keys():
            if bot_id in sub_group[position].keys():
                message = "重复订阅"
            else:
                sub_group[position][bot_id] = {"DynamicOn": 1, "LiveOn": 1}
                with DataManage() as update:
                    await update.modify_subinfo(uid, sub_info=json.dumps(sub_group))
                message = f"成功添加：{sub_info_uid[1]}({uid})"
        else:
            bot_info = {bot_id: {"DynamicOn": 1, "LiveOn": 1}}
            sub_group[position] = bot_info
            sub_group = json.dumps(sub_group)
            with DataManage() as update:
                await update.modify_subinfo(uid, sub_info=sub_group)
            message = f"成功添加：{sub_info_uid[1]}({uid})"
    return message


@bot_checker
async def del_sub(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot, uid: str):
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = bot.self_id
    with DataManage() as acquire:
        sub_info = await acquire.acquire_subinfo_by_uid(uid)
    all_sub_group = json.loads(sub_info[3])
    if position not in all_sub_group.keys() or bot_id not in all_sub_group[position].keys():
        return f"未订阅：{uid}"
    del all_sub_group[position][bot_id]
    if not all_sub_group[position]:
        del all_sub_group[position]
        if not all_sub_group:
            with DataManage() as del_data:
                await del_data.del_subinfo_by_uid(uid)
        else:
            all_sub_group = json.dumps(all_sub_group)
            with DataManage() as update:
                await update.modify_subinfo(uid, all_sub_group)
    else:
        all_sub_group = json.dumps(all_sub_group)
        with DataManage() as update:
            await update.modify_subinfo(uid, all_sub_group)
    return f"成功删除：{sub_info[1]}({sub_info[0]})"


@bot_checker
async def change_live_push_status(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot, uid: str, status: int):
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = bot.self_id
    with DataManage() as acquire:
        all_info = await acquire.acquire_subinfo_by_uid(uid)
    if all_info:
        all_sub_group = json.loads(all_info[3])
        if position in all_sub_group.keys() and bot_id in all_sub_group[position].keys():
            if all_sub_group[position][bot_id]["LiveOn"] == status:
                message = f" 请勿重复{'开启' if status == 1 else '关闭'}"
            else:
                all_sub_group[position][bot_id]["LiveOn"] = status
                all_sub_group = json.dumps(all_sub_group)
                with DataManage() as update:
                    await update.modify_subinfo(uid, all_sub_group)
                if status == 1:
                    message = f"{all_info[1]}({all_info[0]})\n\n直播推送：关 ==> 开"
                else:
                    message = f"{all_info[1]}({all_info[0]})\n\n直播推送：开 ==> 关"
        else:
            message = f"未订阅：{uid}"
    else:
        message = f"未订阅：{uid}"

    return message


@bot_checker
async def change_dynamic_push_status(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot, uid: str,
                                     status: int):
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = bot.self_id
    with DataManage() as acquire:
        all_info = await acquire.acquire_subinfo_by_uid(uid)
    if all_info:
        all_sub_group = json.loads(all_info[3])
        if position in all_sub_group.keys() and bot_id in all_sub_group[position].keys():
            if all_sub_group[position][bot_id]["LiveOn"] == status:
                message = f" 请勿重复{'开启' if status == 1 else '关闭'}"
            else:
                all_sub_group[position][bot_id]["DynamicOn"] = status
                all_sub_group = json.dumps(all_sub_group)
                with DataManage() as update:
                    await update.modify_subinfo(uid, all_sub_group)
                if status == 1:
                    message = f"{all_info[1]}({all_info[0]})\n\n动态推送：关 ==> 开"
                else:
                    message = f"{all_info[1]}({all_info[0]})\n\n动态推送：开 ==> 关"
        else:
            message = f"未订阅：{uid}"
    else:
        message = f"未订阅：{uid}"

    return message


async def change_switch_status(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot, switch_status: int):
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = int(bot.self_id)
    old_status = await check_bot_status(event, bot)
    new_status = switch_status == 1
    if old_status == new_status:
        return f'当前Bot已为{"开启" if switch_status == 1 else "关闭"}状态'
    with DataManage() as change_switch:
        await change_switch.modify_SwitchStatus(position, bot_id, switch_status)
    return "{}".format("晚~安~ \n(¦3[▓▓]" if switch_status == 0 else "早安！！(o゜▽゜)o☆~~")


async def del_group_sub(event: GroupDecreaseNoticeEvent, bot: Bot):
    with DataManage() as acquire:
        all_sub_info = await acquire.acquire_full_subinfo()
    position = str(event.group_id)
    bot_id = bot.self_id
    for single_sub_info in all_sub_info:
        sub_group = json.loads(single_sub_info[3])
        if position in sub_group.keys() and bot_id in sub_group[position].keys():
            del sub_group[position][bot_id]
            if not sub_group[position]:
                del sub_group[position]
            sub_group = json.dumps(sub_group)
            with DataManage() as update:
                await update.modify_subinfo(str(single_sub_info[0]), sub_group)


@bot_checker
async def get_group_sub(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot):
    if event.message_type == "group":
        position = str(event.group_id)
    else:
        position = json.dumps({"guild_id": event.guild_id, "channel_id": event.channel_id})
    bot_id = bot.self_id
    # 取出数据库中所有信息
    with DataManage() as get_all_info:
        all_sub = await get_all_info.acquire_full_subinfo()
    # 如果数据库是空的那么这个群一定没有订阅数据
    if not all_sub:
        return "订阅列表为空"
    else:
        sub_list = []
        for i in all_sub:
            info_dic = json.loads(i[3])
            if position in info_dic.keys() and bot_id in info_dic[position].keys():
                info_dic[position][str(event.self_id)]["Name"] = i[1]
                info_dic[position][str(event.self_id)]["UID"] = i[0]
                sub_list.append(info_dic[position][bot_id])
        if not sub_list:
            return "订阅列表为空"
        else:
            try:
                img_base64 = "base64://{}".format(await get_sub_pic(sub_list))
                return MessageSegment.image(img_base64)
            except Exception as e:
                logger.error(traceback.print_exc())
                return "获取订阅列表错误"


async def get_sub_pic(sub_list):
    """
    将订阅数据做成图片
    :param sub_list: 订阅信息列表
    :return: base64字符串
    """
    img_list = []
    title_info = ["UID", "昵称", "动态推送", "直播推送"]
    font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "HanaMinA.ttf"), 25)
    title_image = Image.new("RGB", (1200, 50), (255, 255, 255, 255))
    draw = ImageDraw.Draw(title_image)
    # 制作表头框
    for i in range(4):
        draw.rectangle((300 * i, 0, 300 * (i + 1), 50), fill=None, outline=(0, 0, 0), width=2)
    # 制作表头
    for j in range(4):
        x = ((300 - font.getsize(str(title_info[j]))[0]) / 2) + 300 * j
        y = (50 - font.getsize(str(title_info[j]))[1]) / 2
        draw.text((x, y), text=str(title_info[j]), fill="black", font=font)
    img_list.append(title_image)
    for sub_detail in sub_list:
        img_new = Image.new("RGB", (1200, 50), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img_new)
        for x in range(4):
            draw.rectangle((300 * x, 0, 300 * (x + 1), 50), fill=None, outline=(0, 0, 0), width=2)
        uid = str(sub_detail["UID"])
        draw.text((((300 - font.getsize(uid)[0]) / 2), (50 - font.getsize(uid)[1]) / 2), uid, fill="black", font=font)
        name = str(sub_detail["Name"])
        draw.text((((300 - font.getsize(name)[0]) / 2) + 300, (50 - font.getsize(name)[1]) / 2), name, fill="black",
                  font=font)
        dynamic_on = "关" if sub_detail["DynamicOn"] == 0 else "开"
        color = "red" if dynamic_on == "关" else "black"
        draw.text((((300 - font.getsize(dynamic_on)[0]) / 2) + 600, (50 - font.getsize(dynamic_on)[1]) / 2),
                  dynamic_on, fill=color, font=font)
        live_on = "关" if sub_detail["LiveOn"] == 0 else "开"
        color = "red" if live_on == "关" else "black"
        draw.text((((300 - font.getsize(live_on)[0]) / 2) + 900, (50 - font.getsize(live_on)[1]) / 2), live_on,
                  fill=color, font=font)
        img_list.append(img_new)
    img_h = len(img_list) * 50
    combination = Image.new("RGB", (1200, img_h), (255, 255, 255))
    for i in range(len(img_list)):
        combination.paste(img_list[i], (0, 50 * i))
    img_byte = BytesIO()
    combination.save(img_byte, format='PNG')
    binary_content = img_byte.getvalue()
    return str(base64.b64encode(binary_content), "utf8")


@bot_checker
async def help_info(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot):
    img = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "help.png"))
    img_byte = BytesIO()
    img.save(img_byte, format='PNG')
    binary_content = img_byte.getvalue()
    img_base64 = f'base64://{str(base64.b64encode(binary_content), "utf8")}'
    return MessageSegment.image(img_base64)

@bot_checker
async def share_to_pic(event: Union[GroupMessageEvent, GuildMessageEvent], bot: Bot):
    short_link = re.search("https://b23\.tv/(\w+)", str(event.get_message()))
    if short_link.group():
        data = await Api().get_location(short_link.group())
        try:
            if data and (m_link := re.search("https://m.bilibili.com/dynamic/(\d+)", data)):
                m_link = m_link.group()
                m_link = m_link.replace("https://m.bilibili.com/dynamic/",
                                        "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&id=")
                item = await Api().get_single_dynamic(m_link)
                if item:
                    img = await BiliRender(item).render()
                    img_byte = BytesIO()
                    img.save(img_byte, format='PNG')
                    binary_content = img_byte.getvalue()
                    img_base64 = f'base64://{str(base64.b64encode(binary_content), "utf8")}'
                    return MessageSegment.image(img_base64)
                else:
                    return
            else:
                return
        except:
            logger.error(traceback.print_exc())
            return


