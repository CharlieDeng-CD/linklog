#!/usr/bin/env python3
"""
快速测试脚本 - 验证 Logic Linker 服务器配置
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    print("1. 测试模块导入...")
    try:
        from server import app, client, static_dir
        print("   ✓ 模块导入成功")
        return True
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        return False

def test_static_files():
    """测试静态文件"""
    print("\n2. 测试静态文件...")
    from server import static_dir
    index_path = static_dir / "index.html"
    if index_path.exists():
        print(f"   ✓ index.html 存在: {index_path}")
        return True
    else:
        print(f"   ✗ index.html 不存在: {index_path}")
        return False

def test_api_client():
    """测试 API 客户端"""
    print("\n3. 测试 API 客户端...")
    from server import client
    try:
        # 简单测试 - 列出模型
        models = client.models.list()
        print(f"   ✓ API 客户端正常，可用模型数: {len(models.data)}")
        return True
    except Exception as e:
        print(f"   ✗ API 客户端测试失败: {e}")
        return False

def test_server_routes():
    """测试服务器路由"""
    print("\n4. 测试服务器路由...")
    from server import app
    routes = [r.path for r in app.routes]
    expected_routes = ["/", "/api/analyze", "/api/add-url"]
    missing = [r for r in expected_routes if r not in routes]
    if not missing:
        print(f"   ✓ 所有路由已注册: {routes}")
        return True
    else:
        print(f"   ✗ 缺少路由: {missing}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Logic Linker 配置检查")
    print("=" * 50)
    
    results = [
        test_imports(),
        test_static_files(),
        test_api_client(),
        test_server_routes()
    ]
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ 所有检查通过！服务器应该可以正常启动。")
        print("\n启动命令:")
        print("  cd 'logic linker'")
        print("  python3 server.py")
        print("\n然后访问: http://localhost:8003")
    else:
        print("✗ 部分检查失败，请查看上面的错误信息。")
    print("=" * 50)

