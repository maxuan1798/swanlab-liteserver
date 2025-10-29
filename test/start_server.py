import os
import uvicorn
from swanboard.app import app
from swanboard.db import connect, Project
from swanboard.utils import FONT

# 设置数据库连接配置
db_config = {
    'database': 'swanlab',
    'user': 'swanlab',
    'password': 'swanlab123',
    'host': 'localhost',
    'port': 3306,
    'autocreate': True
}
connect(**db_config)
# Initialize default project
Project.init(name="Default Project", description="Default project for SwanLab")
HOST = "0.0.0.0"
PORT = 6092


def main():
    return app


if __name__ == "__main__":
    print("Try to explore the swanlab experiment logs in: \n")
    print("               --> " + FONT.dark_green("http://127.0.0.1:" + str(PORT)))
    print("\n")
    uvicorn.run("start_server:main", host=HOST, port=PORT, reload=True, log_level="critical")
