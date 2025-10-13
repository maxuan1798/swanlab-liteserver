#!/usr/bin/env python3
"""
SwanLab HTTP MinIO 客户端集成测试脚本

测试通过 HTTP 调用 SwanLab-Server 进行 MinIO 操作的完整流程。

使用方法:
  export SWANLAB_API_HOST="http://localhost:5173/api/v1/cloud"
  export SWANLAB_API_KEY="your-api-key"  # 可选
  python3 scripts/test_minio_proxy.py

测试内容:
  - 获取服务端 MinIO 配置
  - 上传测试文件
  - 下载并验证文件内容
  - 生成预签名 URL
  - 删除测试文件
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加 SwanLab 客户端到 Python 路径
current_dir = Path(__file__).parent
swanlab_root = current_dir.parent
sys.path.insert(0, str(swanlab_root))

try:
    from swanlab.utils.minio_client import get_minio_client, HTTPMinIOClient
    from swanlab.log import swanlog
except ImportError as e:
    print(f"Failed to import SwanLab modules: {e}")
    print("Make sure you're running this script from the SwanLab-Server directory")
    print("and SwanLab is properly installed or available in the path")
    sys.exit(1)


def test_minio_client():
    """测试 HTTP MinIO 客户端的完整功能"""

    print("=" * 60)
    print("SwanLab HTTP MinIO 客户端集成测试")
    print("=" * 60)

    # 获取客户端
    print("\n1. 获取 MinIO 客户端...")
    client = get_minio_client()

    if not client:
        print("❌ 无法获取 MinIO 客户端")
        print("请确保设置了 SWANLAB_API_HOST 环境变量")
        print("例如: export SWANLAB_API_HOST='http://localhost:5173/api/v1/cloud'")
        return False

    print(f"✅ 成功创建 HTTP MinIO 客户端: {client.api_base}")

    # 测试配置获取
    print("\n2. 获取服务端 MinIO 配置...")
    config = client.get_config()
    if config:
        print("✅ 成功获取配置:")
        print(f"   - 启用状态: {config.get('enabled')}")
        print(f"   - 端点: {config.get('endpoint')}")
        print(f"   - 存储桶: {config.get('bucket')}")
        print(f"   - 区域: {config.get('region')}")
    else:
        print("⚠️ 无法获取配置，可能服务端未启动或未配置 MinIO")

    # 测试文件上传
    print("\n3. 测试文件上传...")
    test_key = "test-suite/http-client/hello.txt"
    test_content = b"Hello from SwanLab HTTP MinIO Client!\nTimestamp: " + str(os.times()).encode()

    upload_success = client.upload_file(test_content, test_key, "text/plain")
    if upload_success:
        print(f"✅ 成功上传文件: {test_key}")
    else:
        print(f"❌ 文件上传失败: {test_key}")
        return False

    # 测试文件下载
    print("\n4. 测试文件下载...")
    downloaded_data = client.download_file(test_key)
    if downloaded_data:
        downloaded_content = downloaded_data.getvalue()
        if downloaded_content == test_content:
            print("✅ 文件下载成功，内容验证通过")
        else:
            print("❌ 文件下载成功，但内容不匹配")
            print(f"   期望: {test_content[:50]}...")
            print(f"   实际: {downloaded_content[:50]}...")
            return False
    else:
        print("❌ 文件下载失败")
        return False

    # 测试预签名 URL
    print("\n5. 测试预签名 URL 生成...")
    presigned_url = client.generate_presigned_url(test_key, expiration=3600)
    if presigned_url:
        print("✅ 成功生成预签名 URL:")
        print(f"   URL: {presigned_url[:80]}...")
    else:
        print("⚠️ 预签名 URL 生成失败（可能服务端不支持）")

    # 测试批量上传
    print("\n6. 测试批量文件上传...")
    batch_files = [
        (b"File 1 content", "test-suite/batch/file1.txt", "text/plain"),
        (b"File 2 content", "test-suite/batch/file2.txt", "text/plain"),
        (b"Binary data", "test-suite/batch/binary.bin", "application/octet-stream"),
    ]

    success_count = client.upload_files(batch_files)
    print(f"✅ 批量上传完成: {success_count}/{len(batch_files)} 个文件成功")

    # 测试文件是否存在
    print("\n7. 测试文件存在性检查...")
    exists = client.file_exists(test_key)
    if exists:
        print(f"✅ 文件存在性检查通过: {test_key}")
    else:
        print(f"❌ 文件存在性检查失败: {test_key}")

    # 测试文件删除
    print("\n8. 测试文件删除...")
    delete_success = client.delete_file(test_key)
    if delete_success:
        print(f"✅ 成功删除文件: {test_key}")

        # 验证文件已被删除
        exists_after_delete = client.file_exists(test_key)
        if not exists_after_delete:
            print("✅ 文件删除验证通过")
        else:
            print("⚠️ 文件删除后仍然存在")
    else:
        print(f"❌ 文件删除失败: {test_key}")

    # 清理批量上传的文件
    print("\n9. 清理测试文件...")
    cleanup_count = 0
    for _, object_key, _ in batch_files:
        if client.delete_file(object_key):
            cleanup_count += 1
    print(f"✅ 清理完成: {cleanup_count}/{len(batch_files)} 个文件已删除")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！HTTP MinIO 客户端工作正常。")
    print("=" * 60)

    return True


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("错误处理测试")
    print("=" * 60)

    client = get_minio_client()
    if not client:
        print("❌ 无法获取客户端，跳过错误处理测试")
        return

    # 测试下载不存在的文件
    print("\n1. 测试下载不存在的文件...")
    non_existent = client.download_file("non-existent/file.txt")
    if non_existent is None:
        print("✅ 正确处理了不存在文件的下载请求")
    else:
        print("⚠️ 下载不存在的文件时返回了数据")

    # 测试删除不存在的文件
    print("\n2. 测试删除不存在的文件...")
    delete_result = client.delete_file("non-existent/file.txt")
    print(f"ℹ️ 删除不存在文件的结果: {delete_result}")

    # 测试上传空文件名
    print("\n3. 测试上传到空文件名...")
    try:
        empty_key_result = client.upload_file(b"test", "", "text/plain")
        print(f"ℹ️ 空文件名上传结果: {empty_key_result}")
    except Exception as e:
        print(f"✅ 正确抛出异常: {e}")


def main():
    """主测试函数"""
    print("SwanLab HTTP MinIO 客户端测试")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python 路径: {sys.path[0]}")

    # 检查环境变量
    api_host = os.getenv('SWANLAB_API_HOST')
    api_key = os.getenv('SWANLAB_API_KEY')

    print(f"\n环境配置:")
    print(f"  SWANLAB_API_HOST: {api_host or '未设置'}")
    print(f"  SWANLAB_API_KEY: {'已设置' if api_key else '未设置'}")

    if not api_host:
        print("\n❌ 未设置 SWANLAB_API_HOST 环境变量")
        print("请设置后重试:")
        print("  export SWANLAB_API_HOST='http://localhost:5173/api/v1/cloud'")
        print("  export SWANLAB_API_KEY='your-api-key'  # 可选")
        return 1

    try:
        # 运行主要测试
        if not test_minio_client():
            return 1

        # 运行错误处理测试
        test_error_handling()

        print("\n🎉 所有测试完成！")
        return 0

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
