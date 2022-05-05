import os
import sqlite3
from typing import Optional, Union


class DataManage:
    def __enter__(self):
        database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AllData.db')
        self.db = sqlite3.connect(database_path)
        self.cursor = self.db.cursor()
        # 如果不存在则创建一个存Cookie的表
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS CookieReserve 
                                (ID INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL,
                                Cookie  TEXT  NOT NULL,
                                ts INT     NOT NULL);""")

        # 如果不存在则创建一个存订阅信息的表
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS SubInfoReserve 
                                (ID INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL,
                                UID  INT  NOT NULL,
                                Name TEXT NOT NULL,
                                LiveStatus  INT  NOT NULL,
                                SubGroup TEXT NOT NULL);""")

        # 如果不存在就创建一个存bot开关的表
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS BotSwitch 
                                (ID INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL,
                                SwitchPosition TEXT NOT NULL,
                                SwitchStatus  INT  NOT NULL DEFAULT 1,
                                BotId TEXT INT NULL );""")

        # 如果不存在就创建一个存dynamic_id的表
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS DynamicReserve 
                                (ID INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL,
                                Dynamic TEXT NOT NULL,
                                Timestamp INT NOT NULL);""")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        self.cursor.close()
        self.db.close()

    async def store_cookie(self, cookie: str, ts: int) -> None:
        """
        将cookie存入数据库
        :param cookie: cookie
        :param ts: 时间戳
        :return: None
        """
        add_sql = "insert into CookieReserve (Cookie,ts) values(?,?);"
        data = (cookie, ts,)
        self.cursor.execute(add_sql, data)

    async def delete_old_cookie(self) -> None:
        """
        删除旧的cookie
        :return:
        """
        del_sql = "delete from CookieReserve"
        self.cursor.execute(del_sql)

    async def acquire_cookie(self) -> Optional[tuple]:
        """
        从数据库中取出 mid,AccessToken,RefreshToken,Cookie,expires
        :return: (mid:int,AccessToken:str,RefreshToken:str, Cookie:str, expires:int)
        """
        acquire_sql = "select Cookie,ts from CookieReserve"
        self.cursor.execute(acquire_sql)
        result = self.cursor.fetchone()
        return result

    async def store_SwitchStatus(self, switch_position: str, bot_id: int) -> None:
        """
        将bot开关存入数据库
        :param switch_type: str
        :param switch_position:int
        :param bot_id: int
        :return: None
        """
        store_sql = "insert into BotSwitch (SwitchPosition,BotId) values(?,?);"
        data = (switch_position, bot_id,)
        self.cursor.execute(store_sql, data)

    async def del_SwitchStatus(self, switch_position: str, bot_id: int) -> None:
        del_sql = "delete from SubInfoReserve where SwitchPosition=? and BotId=?"
        data = (switch_position, bot_id,)
        self.cursor.execute(del_sql, data)

    async def acquire_SwitchStatus(self, group_id: str, bot_id: int) -> Optional[tuple]:
        """
        通过群号查找对应群机器人的开关状态
        :param group_id: str
        :param bot_id: int
        :return: Optional[tuple[int]]
        """
        acquire_sql = "select SwitchStatus from BotSwitch where  SwitchPosition=? and BotId=?"
        data = (group_id, bot_id,)
        result = self.cursor.execute(acquire_sql, data).fetchone()
        return result

    async def modify_SwitchStatus(self, switch_position: str, bot_id: int, status: int) -> None:
        """
        修改Bot开关状态
        :param status:
        :param switch_position:
        :param bot_id:
        :return:
        """
        modify_sql = "update BotSwitch set SwitchStatus = ? where SwitchPosition=? and BotId=?"
        data = (status, switch_position, bot_id,)
        self.cursor.execute(modify_sql, data)

    async def store_subinfo(self, uid: int, name: str, live_status: int, sub_group: str) -> None:
        """
        新增加订阅数据到数据库中
        :param uid: int
        :param name: str
        :param live_status:int
        :param sub_group: str
        :return: None
        """
        store_sql = "insert into SubInfoReserve (UID,Name,LiveStatus,SubGroup) values(?,?,?,?);"
        data = (uid, name, live_status, sub_group,)
        self.cursor.execute(store_sql, data)

    async def del_subinfo_by_uid(self, uid: str):
        del_sql = "delete from SubInfoReserve where UID=?"
        data = (uid,)
        self.cursor.execute(del_sql, data)

    async def modify_subinfo(self, uid: str, sub_info) -> None:
        modify_sql = "update SubInfoReserve set SubGroup = ? where UID=?"
        data = (sub_info, uid,)
        self.cursor.execute(modify_sql, data)

    async def modify_live_status(self, uid: int, live_status) -> None:
        modify_sql = "update SubInfoReserve set LiveStatus = ? where UID=?"
        data = (live_status, uid,)
        self.cursor.execute(modify_sql, data)

    async def acquire_subinfo_by_uid(self, uid: Union[int, str]) -> Union[tuple, None]:
        """
        通过uid查找订阅信息
        :param uid:
        :return:
        """
        acquire_sql = "select UID,Name,LiveStatus,SubGroup from SubInfoReserve where UID = ?"
        data = (uid,)
        result = self.cursor.execute(acquire_sql, data).fetchone()
        return result

    async def acquire_full_subinfo(self) -> Union[list, None]:
        """
        获取所有信息
        :return: Union[tuple, None]
        """
        self.cursor.execute("select UID,Name,LiveStatus,SubGroup from SubInfoReserve")
        result = self.cursor.fetchall()
        return result

    async def store_dynamic_id(self, dynamic_id: str, timestamp: int) -> None:
        store_sql = "insert into DynamicReserve (Dynamic,Timestamp) values(?,?);"
        data = (dynamic_id, timestamp)
        self.cursor.execute(store_sql, data)

    async def acquire_dynamic_id(self, dynamic_id: str) -> Union[None, tuple]:
        acquire_sql = "select Dynamic,Timestamp from DynamicReserve where Dynamic = ?"
        data = (dynamic_id,)
        result = self.cursor.execute(acquire_sql, data).fetchone()
        return result

    async def del_dynamic_id(self, timestamp):
        sql = "delete from DynamicReserve where Timestamp<? "
        data = (timestamp,)
        self.cursor.execute(sql, data)


if __name__ == '__main__':
    print()
