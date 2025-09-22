#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2024-02-05 16:56:06
@File: swanlab/db/connect.py
@IDE: vscode
@Description:
    数据库连接模块
"""
from peewee import MySQLDatabase
from .table_config import tables, Tag
from .migrate import compat_tag_key

db_config = None
"""
全局挂载的数据库配置，用于存储MySQL连接信息
"""


def connect(database: str = "swanlab", user: str = "swanlab", password: str = "swanlab123", host: str = "host.docker.internal", port: int = 3306, autocreate: bool = False) -> MySQLDatabase:
    """
    连接MySQL数据库，只有调用此方法以后，数据库才会被创建，所有导出的类才可用


    Parameters:
    ----------
    database : str
        数据库名称，第一次连接时必须指定数据库名称
        后续使用如果不指定，会使用第一次指定的数据库名称
    user : str
        MySQL用户名，默认为'root'
    password : str
        MySQL密码，默认为空字符串
    host : str
        MySQL主机地址，默认为'localhost'
    port : int
        MySQL端口号，默认为3306
    autocreate : bool
        是否自动创建数据库，如果设置为True，当数据库不存在时，会自动创建数据库
        如果设置为False，当数据库不存在时，会抛出ConnectionError异常
        设置此参数是为了严格控制数据库创建行为，避免误操作

    Return:
    -------
    swandb :
        MySQL数据库实例

    Raises:
    -------
    ConnectionError :
        如果数据库不存在，并且autocreate为False，则会抛出ConnectionError异常
    ValueError :
        如果第一次连接时未指定数据库名称
    """
    global db_config
    bound = True

    # 设置数据库配置
    if not database and not db_config:
        raise ValueError("First time connect must specify the database name")
    elif database:
        # 更新全局配置
        db_config = {
            'database': database,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        bound = False

    # 创建MySQL数据库连接
    try:
        # 先连接到MySQL服务器（不指定数据库）
        temp_db = MySQLDatabase("swanlab", user=db_config['user'], password=db_config['password'],
                               host=db_config['host'], port=db_config['port'])

        # Debug: print temp_db dbconfig
        print(f"DEBUG temp_db config: {db_config}")

        temp_db.connect()

        # 检查数据库是否存在
        cursor = temp_db.execute_sql("SHOW DATABASES LIKE %s", (db_config['database'],))
        db_exists = cursor.fetchone() is not None

        if not db_exists and not autocreate:
            temp_db.close()
            raise ConnectionError(f"Database '{db_config['database']}' not found")

        if not db_exists and autocreate:
            # 创建数据库
            temp_db.execute_sql(f"CREATE DATABASE `{db_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

        temp_db.close()

    except Exception as e:
        raise ConnectionError(f"Failed to connect to MySQL server: {e}")

    # 连接到指定数据库
    swandb = MySQLDatabase(db_config['database'], user=db_config['user'], password=db_config['password'],
                          host=db_config['host'], port=db_config['port'], charset='utf8mb4')

    if not bound:
        # 动态绑定数据库
        swandb.connect()
        swandb.bind(tables)
        swandb.create_tables(tables)
        swandb.close()
        if not Tag.field_exists("folder"):
            # 添加 folder 字段
            compat_tag_key(swandb)

    return swandb
