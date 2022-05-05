import asyncio
import traceback
import urllib.parse
from typing import Optional, Union
from urllib.parse import urlsplit

import httpx
from dynamicrender.DynamicChecker import Item
from nonebot import logger


class Api:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88\
                              Safari/537.36 Edg/87.0.664.60',
            'Referer': 'https://www.bilibili.com/'

        }

    async def get_short_link(self, long_url):
        """
        获取短链接
        :param long_url:
        :return:
        """
        async with httpx.AsyncClient(headers=self.headers) as session:
            try:
                url = "https://api.bilibili.com/x/share/click"
                data = {'build': '9331',
                        'buvid': '74fe03588ceace988e365fd982bd0955',
                        'oid': long_url,
                        'platform': 'ios',
                        'share_channel': 'COPY',
                        'share_id': 'public.webview.0.0.pv',
                        'share_mode': '3'}
                response = await session.post(url, data=data)
                response = response.json()
                return response["data"]["content"]
            except Exception as e:
                logger.error(traceback.print_exc())
                return

    async def get_uid_info(self, uid) -> Optional[dict]:
        """
        :param uid:UID
        :return:
        """
        async with httpx.AsyncClient(headers=self.headers) as session:
            try:
                url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
                response = await session.get(url)
                response = response.json()
                return {"nick_name": response['data']['name'],
                        "roomStatus": response['data']['live_room']['roomStatus'],
                        "liveStatus": response['data']['live_room']['liveStatus']}
            except Exception as e:
                logger.error(traceback.print_exc())
                return

    async def change_follow(self, uid, act, cookie: dict):
        """
        将up添加到关注列表或者从关注列表删除up
        :param uid:要关注或者取关的UID
        :param act: 1为关注，2为取关
        :param cookie:cookie
        :return:
        """
        url = "https://api.bilibili.com/x/relation/modify"
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'Referer': 'https://space.bilibili.com',
            'referer': f'https://space.bilibili.com/{uid}?spm_id_from=..0.0',
        }
        data = {
            "fid": f"{uid}",
            "act": f"{act}",
            "re_src": "11",
            "spmid": "333.999.0.0",
            "extend_content": {"entity": "user", "entity_id": uid},
            "json": "json",
            "csrf": cookie["bili_jct"]
        }
        try:
            response = httpx.post(url=url, headers=headers, data=data, cookies=cookie)
            response = response.json()
            return True if response["code"] == 0 else response['message']
        except Exception as e:
            return str(e)

    async def get_room_info(self, uids):
        """
        查看是否开播,以及直播间信息
        :param uids: UID的列表
        :return:空或者字典
        """
        uids = {'uids': uids}
        try:
            async with httpx.AsyncClient(headers=self.headers) as session:
                url = 'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids'
                response = await session.post(url, json=uids)
                data = response.json()
                data = data["data"]
            return data
        except Exception as e:
            logger.error(traceback.print_exc())
            return

    async def dynamic_new(self, cookie: dict, page: int, offset: int = None) -> Union[None, list]:
        """
        获得关注列表内动态
        :param page:
        :param cookie:
        :return:
        """
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'Referer': 'https://space.bilibili.com',
            'referer': f'https://t.bilibili.com/?spm_id_from=..0.0'
        }
        if not offset:
            url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&page={page}'
        else:
            url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&offset={offset}&page={page}'
        try:
            async with httpx.AsyncClient(headers=headers, cookies=cookie) as client:
                response = await client.get(url)
                data = response.json()
                if data["code"] == 0:
                    return data["data"]["items"]
                else:
                    return
        except Exception as e:
            logger.error(traceback.print_exc())
            return

    async def get_location(self, url: str):
        """通过短链接获取动态链接"""
        try:
            async with httpx.AsyncClient() as client:
                url = url
                response = await client.get(url, headers=self.headers)
            return response.headers.get("location")
        except TimeoutError as e:
            logger.error(traceback.print_exc())
            return

    async def get_single_dynamic(self, url: str):
        try:
            async with httpx.AsyncClient() as client:
                url = url
                response = await client.get(url, headers=self.headers)
            dynamic = response.json()
            dynamic_item = dynamic["data"]["item"]
            item = Item(**dynamic_item)
            return item
        except Exception as e:
            logger.error(traceback.print_exc())
            return
    # async def thumb(self, cookie: dict, dynamic_id: str):
    #     """
    #     点赞
    #     :param dynamic_id: str
    #     :param cookie: dict
    #     :return:
    #     """
    #     data = {
    #         "uid": cookie["DedeUserID"],
    #         "csrf": cookie["bili_jct"],
    #         "up": 1,
    #         "csrf_token": cookie["bili_jct"],
    #         "dynamic_id": dynamic_id
    #     }
    #     url = "https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb"

    # async def dynamic_history(self, cookie: dict, offset_dynamic_id):
    #     """
    #     获取offset_dynamic_id后的20条动态
    #     :param cookie: cookie->dict
    #     :param offset_dynamic_id: str
    #     :return:
    #     """
    #     uid = cookie["DedeUserID"]
    #     url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid={uid}&" \
    #           f"offset_dynamic_id={offset_dynamic_id}&type=268435455&from=weball&platform=web "
    #     try:
    #         async with httpx.AsyncClient(headers=self.headers, cookies=cookie) as client:
    #             response = await client.get(url)
    #         data = response.json()
    #         cards = GetDynamicResponseContent(**data)
    #         if cards.code == 0:
    #             return cards.data.cards
    #         else:
    #             return
    #     except Exception as e:
    #         logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
    #                                                                    sys._getframe(0).f_code.co_name,
    #                                                                    sys._getframe(0).f_lineno, str(e)))
    #         return


class ApiWebLogin:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                                             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88\
                                              Safari/537.36 Edg/87.0.664.60',
            'Referer': 'https://www.bilibili.com/'
        }
        self.oauth_key = None

    # WEB端扫码登录
    # region
    async def get_oauth_key(self):
        """
        获取oauthKey以及下一步用于制作二维码的连接
        :return: [url, oauthKey]

        """
        async with httpx.AsyncClient(headers=self.headers) as session:
            try:
                url = 'http://passport.bilibili.com/qrcode/getLoginUrl'
                response = await session.get(url)
                response = response.json()
                data = response["data"]
                if data:
                    url = data["url"]
                    oauthKey = data['oauthKey']
                    ts = response["ts"]
                    return [url, oauthKey, ts]
                else:
                    return
            except TimeoutError as e:
                logger.error(traceback.print_exc())
                return

    async def get_cookie(self):
        """
        完成登录并且获得cookie
        :return:
        {'code': 0, 'status': True, 'ts': 1649509996,
        'data': {'url': 'https://passport.biligame.com/crossDomain?DedeUserID=37815472&DedeUserID__ckMd5=8d9f478853b39f41&Expires=15551000&SESSDATA=248e30dd%2C1665061996%2C8890b%2A41&bili_jct=e8c72566fc80a19340154bf0140cf9ae&gourl=http%3A%2F%2Fwww.bilibili.com'}}

        """
        try:
            async with httpx.AsyncClient() as client:
                url = 'http://passport.bilibili.com/qrcode/getLoginInfo'
                data = {'oauthKey': urllib.parse.quote(self.oauth_key)}
                response = await client.post(url, headers=self.headers, data=data)
                response = response.json()
                return response
        except TimeoutError as e:
            logger.error(traceback.print_exc())
            return

    # endregion


# class ApiTvLogin:
#     def __init__(self):
#         self.headers = {
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
#                                      AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88\
#                                       Safari/537.36 Edg/87.0.664.60',
#             'Referer': 'https://www.bilibili.com/'
#         }
#         self.local_id = 0
#         self.auth_code = None
#         self.app_key = "4409e2ce8ffd12b8"
#         self.app_sec = "59b43e04ad6965f34319062b478f83dd"
#
#     async def get_auth_code(self) -> Union[None, GetAuthCodeResponseContent]:
#         """
#         获取用于制作扫码登录的二维码的链接和用于查看是否扫码登录成功的auth_code
#         :return:
#         """
#
#         params: dict = {'local_id': self.local_id, 'appkey': self.app_key, 'ts': int(time.time())}
#         params['sign'] = md5(f"{urlencode(sorted(params.items()))}{self.app_sec}".encode('utf-8')).hexdigest()
#         try:
#             async with httpx.AsyncClient(headers=self.headers) as session:
#                 url = "http://passport.bilibili.com/x/passport-tv-login/qrcode/auth_code"
#                 response = await session.post(url, data=params)
#                 data = response.json()
#                 try:
#                     data = GetAuthCodeResponseContent(**data)
#                     return data
#                 except ValidationError as e:
#                     logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
#                                                                                sys._getframe(0).f_code.co_name,
#                                                                                sys._getframe(0).f_lineno, str(e)))
#
#                     return
#         except TimeoutError as e:
#             logger.error("file:API line:216 error:{}".format(str(e)))
#             return
#
#     # 获取token
#     async def get_token(self) -> Union[None, GetTokenResponseContent]:
#
#         params: dict = {'local_id': self.local_id, 'appkey': self.app_key, 'ts': int(time.time()),
#                         'auth_code': self.auth_code}
#         params['sign'] = md5(f"{urlencode(sorted(params.items()))}{self.app_sec}".encode('utf-8')).hexdigest()
#         try:
#             url = "http://passport.bilibili.com/x/passport-tv-login/qrcode/poll"
#             async with httpx.AsyncClient(headers=self.headers) as session:
#                 response = await session.post(url, data=params)
#                 data = response.json()
#             try:
#                 data = GetTokenResponseContent(**data)
#                 return data
#             except ValidationError as e:
#                 logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
#                                                                            sys._getframe(0).f_code.co_name,
#                                                                            sys._getframe(0).f_lineno, str(e)))
#
#                 return
#         except TimeoutError as e:
#             logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
#                                                                        sys._getframe(0).f_code.co_name,
#                                                                        sys._getframe(0).f_lineno, str(e)))
#
#             return
#
#     # 刷新cookie
#     async def refresh_cookie(self, access_token: str, refresh_token: str) -> Union[None, GetTokenResponseContent]:
#
#         params: dict = {'access_token': access_token, 'refresh_token': refresh_token,
#                         'appkey': self.app_key}
#         params['sign'] = md5(f"{urlencode(sorted(params.items()))}{self.app_sec}".encode('utf-8')).hexdigest()
#         try:
#             url = "https://passport.bilibili.com/api/v2/oauth2/refresh_token"
#             async with httpx.AsyncClient(headers=self.headers) as session:
#                 response = await session.post(url, data=params)
#                 data = response.json()
#             try:
#                 data = GetTokenResponseContent(**data)
#                 return data
#             except ValidationError as e:
#                 logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
#                                                                            sys._getframe(0).f_code.co_name,
#                                                                            sys._getframe(0).f_lineno, str(e)))
#                 return
#         except TimeoutError as e:
#             logger.error("file:{} function:{} line:{} error:{}".format(sys._getframe(0).f_code.co_filename,
#                                                                        sys._getframe(0).f_code.co_name,
#                                                                        sys._getframe(0).f_lineno, str(e)))
#             return
if __name__ == '__main__':
    async def run():
        log_in = ApiWebLogin()
        while True:
            result = await log_in.get_cookie()
            print(result)
            if "code" in result.keys() and result["code"] == 0:
                cookie = {}
                ts = result["ts"]
                url = result["data"]["url"]
                query = urlsplit(url).query
                for s in query.split('&'):
                    key, value = s.split("=")
                    cookie[key] = value
                cookie.pop("gourl")
                break
            await asyncio.sleep(5)


    asyncio.run(run())
