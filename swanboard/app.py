#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
@DATE: 2023-11-30 20:47:18
@File: swanlab\server\route.py
@IDE: vscode
@Description:
    综合服务 api
"""
from dotenv import load_dotenv
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .middleware.common import (
    resp_base,
    resp_static,
    catch_error,
    log_print,
    resp_params,
)

# 响应路径
from .settings import ASSETS

# 加载 .env_test 文件
load_dotenv()

# 导入数据库连接管理器
from .db.mysql import mysql_manager, MySQLConfig

# 服务全局对象 - 配置OpenAPI文档
app = FastAPI(
    title="SwanLab-Server API",
    description="""
    SwanLab-Server API provides comprehensive endpoints for managing machine learning experiments,
    projects, and cloud synchronization.

    ## Features

    * **Projects**: Create and manage ML projects
    * **Experiments**: Track and visualize ML experiments
    * **Charts**: Generate and retrieve experiment charts
    * **Media**: Handle experiment media files
    * **Cloud Sync**: Synchronize experiments to cloud storage
    * **Namespaces**: Organize projects by namespace

    ## Authentication

    Some endpoints require API key authentication via the `Authorization` header.
    """,
    version="1.0.0",
    contact={
        "name": "SwanLab Team",
        "url": "https://github.com/SwanHubX/SwanLab",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    docs_url="/api/docs",  # Swagger UI路径
    redoc_url="/api/redoc", # ReDoc路径
    openapi_url="/api/v1/openapi.json"  # OpenAPI schema路径
)

# 注册前端静态文件路径
static_path = "/assets"
static = StaticFiles(directory=ASSETS)
app.mount(static_path, static)

# 将uvicorn的日志输出handler删除
import logging

# 删除 uvicorn logger
uvicorn_error = logging.getLogger("uvicorn.error")
uvicorn_error.disabled = True
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True


# ---------------------------------- 应用生命周期事件 ----------------------------------


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 初始化数据库连接（如果启用云端同步）
    if os.getenv("SWANLAB_CLOUD_SYNC", "false").lower() in ("true", "1", "yes"):
        try:
            # 尝试连接MySQL数据库
            config = MySQLConfig.from_env()
            connected = mysql_manager.connect(config)
            if connected:
                print("✓ Database connected successfully")
            else:
                print("⚠ Warning: Database connection failed, authentication features may not work")
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize database: {e}")
            print("  Authentication features may not work properly")

    # 初始化Redis（用于认证令牌存储）
    try:
        from .services.auth_service import AuthService
        from .config.auth_config import AuthConfig
        AuthService.initialize_redis(AuthConfig.REDIS_URL)
        print("✓ Redis initialized for authentication")
    except Exception as e:
        print(f"⚠ Warning: Redis initialization failed: {e}")
        print("  Token refresh may use database fallback")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    # 断开数据库连接
    try:
        mysql_manager.disconnect()
        print("✓ Database connection closed")
    except Exception as e:
        print(f"⚠ Warning: Error closing database: {e}")


# ---------------------------------- 在此处注册中间件 ----------------------------------


@app.middleware("http")
async def _(*args, **kwargs):
    """基础中间件，调整响应结果，添加处理时间等信息"""
    return await resp_base(*args, **kwargs)


@app.middleware("http")
async def _(*args, **kwargs):
    """资源中间件，此时所有与api相关的内容不会在此中间件中处理"""
    return await resp_static(*args, **kwargs)


@app.middleware("http")
async def _(*args, **kwargs):
    """异常中间件，捕获异常，重构异常信息"""
    return await catch_error(*args, **kwargs)


@app.middleware("http")
async def _(*args, **kwargs):
    """日志打印中间件"""
    return await log_print(*args, **kwargs)


@app.middleware("http")
async def _(*args, **kwargs):
    """参数中间件，处理api请求中的参数校验问题，重新结构化校验错误结果

    参数校验错误并不会影响其他情况的响应结果
    此外由于参数校验错误在绝大多数情况应该是开发时的错误
    所以不会影响正式版本的性能
    """
    return await resp_params(*args, **kwargs)


# ---------------------------------- 在此处注册相关路由 ----------------------------------

# 导入数据相关的路由
from .router.experiment import router as experiment
from .router.project import router as project
from .router.namespace import router as namespace
from .router.chart import router as chart

# 媒体文件路由，允许前端获取其他产生的媒体文件
from .router.media import router as media

# 云端API路由，支持EnhancedSwanBoardCallback的HTTP通信
from .router.cloud import router as cloud

# 认证相关路由
from .router.auth import router as auth
from .router.oauth import router as oauth

# API Key 管理路由
from .router.api_key import router as api_key

# 使用配置列表，统一导入
prefix = "/api/v1"
app.include_router(project, prefix=prefix + "/project", tags=["Projects"])
app.include_router(experiment, prefix=prefix + "/experiment", tags=["Experiments"])
app.include_router(media, prefix=prefix + "/media", tags=["Media"])
app.include_router(namespace, prefix=prefix + "/namespace", tags=["Namespaces"])
app.include_router(chart, prefix=prefix + "/chart", tags=["Charts"])
app.include_router(cloud, prefix=prefix + "/cloud", tags=["Cloud Sync"])
app.include_router(auth, prefix=prefix + "/auth", tags=["Authentication"])
app.include_router(oauth, prefix=prefix + "/oauth", tags=["OAuth"])
app.include_router(api_key, prefix=prefix, tags=["API Keys"])
