from nonebot import on_regex
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SuperUser
from nonebot.plugin import on_command, on_notice
from nonebot_plugin_guild_patch import Message

from ..CmdManager import *

log_in = on_command("登录")


@log_in.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    if not SuperUser():
        await log_in.finish()
    else:
        message = await login(event, bot)
        await log_in.finish(message)


append_sub = on_command("添加")


@append_sub.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await append_sub.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await add_sub(event=event, bot=bot, uid = str(args))
                await append_sub.finish(message)
            else:
                await append_sub.finish("请携带正确的UID")
        else:
            await append_sub.finish("请携带UID")


delete_sub = on_command("删除")


@delete_sub.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await delete_sub.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await del_sub(event, bot, str(args))
                await delete_sub.finish(message)
            else:
                await delete_sub.finish("请输入正确的UID")
        else:
            await delete_sub.finish("请携带UID")


live_push_on = on_command("开启直播")


@live_push_on.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await live_push_on.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await change_live_push_status(event, bot, str(args), 1)
                await live_push_on.finish(message)
            else:
                await live_push_on.finish("请输入正确的UID")
        else:
            await live_push_on.finish("请携带UID")


live_push_off = on_command("关闭直播")


@live_push_off.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await live_push_off.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await change_live_push_status(event, bot, str(args), 0)
                await live_push_off.finish(message)
            else:
                await live_push_off.finish("请输入正确的UID")
        else:
            await live_push_off.finish("请携带UID")


dynamic_push_on = on_command("开启动态")


@dynamic_push_on.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await dynamic_push_on.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await change_dynamic_push_status(event, bot, str(args), 1)
                await dynamic_push_on.finish(message)
            else:
                await dynamic_push_on.finish("请输入正确的UID")
        else:
            await dynamic_push_on.finish("请携带UID")


dynamic_push_off = on_command("关闭动态")


@dynamic_push_off.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], args: Message = CommandArg()):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await dynamic_push_off.finish()
    else:
        if args:
            if str(args).isdigit():
                message = await change_dynamic_push_status(event, bot, str(args), 0)
                await dynamic_push_off.finish(message)
            else:
                await dynamic_push_off.finish("请输入正确的UID")
        else:
            await dynamic_push_off.finish("请携带UID")


switch_on = on_command("天亮了")


@switch_on.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await switch_on.finish()
    else:
        message = await change_switch_status(event, bot, 1)
        await switch_on.finish(message)


switch_off = on_command("天黑了")


@switch_off.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    if event.message_type == "group" and not await (GROUP_ADMIN | GROUP_OWNER)(bot, event):
        await switch_off.finish()
    else:
        message = await change_switch_status(event, bot, 0)
        await switch_off.finish(message)


group_decrease = on_notice()


@group_decrease.handle()
async def _(bot: Bot, event: GroupDecreaseNoticeEvent):
    if event.self_id == event.user_id:
        await del_group_sub(event, bot)
        await group_decrease.finish()
    else:
        await group_decrease.finish()


help_send = on_command("帮助")


@help_send.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    message = await help_info(event, bot)
    if message:
        await MessageSender(event=event, bot=bot, message=message).send_back()
    await help_send.finish()


show_all_sub = on_command("列表")


@show_all_sub.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    message = await get_group_sub(event, bot)
    if message:
        await bot.send(event, message=message)
    await show_all_sub.finish()


dynamic_to_pic = on_regex("https:\/\/b23.tv\/")

@dynamic_to_pic.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    img = await share_to_pic(event, bot)
    if img:
        await dynamic_to_pic.send(message=img)
    await dynamic_to_pic.finish()
