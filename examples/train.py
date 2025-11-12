import swanlab
import random
import time

def train_one_epoch():
    """Mock training function that returns a random loss value"""
    time.sleep(0.1)  # 模拟训练耗时
    return random.uniform(0.1, 1.0)

# 初始化 cloud 模式连接到 SwanLab-Server
run = swanlab.init(
    project="my-project",
    mode="host",  # 启用 host 模式，swanlab原有的模式也支持
)

# 记录训练指标
for epoch in range(100):
    loss = train_one_epoch()
    swanlab.log({"loss": loss, "epoch": epoch})
