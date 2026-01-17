#!/usr/bin/env python3
"""
测试 LinkLog v3 API
测试 Mode A (Standard Exploration) 和 Mode B (Gap Analysis)
"""
import json
import time
import sys
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_mode_a():
    """测试 Mode A: Standard Exploration (无 context)"""
    print("\n" + "="*80)
    print("🧪 测试 Mode A: Standard Exploration (全量模式)")
    print("="*80)
    
    payload = {
        "goal": "学习 React 开发"
    }
    
    print(f"\n[Request] 发送请求到 /api/v3/init")
    print(f"   └─ Goal: {payload['goal']}")
    print(f"   └─ Context: 无（触发 Mode A）")
    
    start_time = time.time()
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/init",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            elapsed = time.time() - start_time
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        print(f"\n[Response] 响应状态: {status_code}")
        print(f"   └─ 耗时: {elapsed:.2f}秒")
        
        if status_code == 200:
            if result.get("success"):
                data = result.get("data", {})
                nodes = data.get("nodes", [])
                edges = data.get("edges", [])
                mode = result.get("mode", "Unknown")
                
                print(f"\n✅ Mode A 测试成功！")
                print(f"   └─ 模式: {mode}")
                print(f"   └─ 节点数: {len(nodes)}")
                print(f"   └─ 边数: {len(edges)}")
                print(f"\n   节点列表:")
                for i, node in enumerate(nodes[:5], 1):  # 只显示前5个
                    node_type = node.get("type", node.get("category", "unknown"))
                    print(f"      {i}. [{node_type}] {node.get('label', 'N/A')}")
                if len(nodes) > 5:
                    print(f"      ... 还有 {len(nodes) - 5} 个节点")
                
                return True
            else:
                print(f"\n❌ Mode A 测试失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Mode A 测试失败: HTTP {status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Mode A 测试异常: {str(e)}")
        return False


def test_mode_b():
    """测试 Mode B: Gap Analysis (有 context)"""
    print("\n" + "="*80)
    print("🧪 测试 Mode B: Gap Analysis (差量模式)")
    print("="*80)
    
    payload = {
        "goal": "学习 React 开发",
        "context": "我熟悉 JavaScript 和 jQuery，有 HTML/CSS 基础"
    }
    
    print(f"\n[Request] 发送请求到 /api/v3/init")
    print(f"   └─ Goal: {payload['goal']}")
    print(f"   └─ Context: {payload['context']}")
    print(f"   └─ 预期: 触发 Mode B（差量模式）")
    
    start_time = time.time()
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/init",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            elapsed = time.time() - start_time
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        print(f"\n[Response] 响应状态: {status_code}")
        print(f"   └─ 耗时: {elapsed:.2f}秒")
        
        if status_code == 200:
            if result.get("success"):
                data = result.get("data", {})
                nodes = data.get("nodes", [])
                edges = data.get("edges", [])
                mode = result.get("mode", "Unknown")
                
                print(f"\n✅ Mode B 测试成功！")
                print(f"   └─ 模式: {mode}")
                print(f"   └─ 节点数: {len(nodes)}")
                print(f"   └─ 边数: {len(edges)}")
                
                # 检查是否有 bridge/review/new_concept 类型的节点
                node_types = {}
                for node in nodes:
                    node_type = node.get("type", node.get("category", "unknown"))
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                print(f"\n   节点类型统计:")
                for node_type, count in node_types.items():
                    print(f"      - {node_type}: {count}")
                
                print(f"\n   节点列表:")
                for i, node in enumerate(nodes[:5], 1):  # 只显示前5个
                    node_type = node.get("type", node.get("category", "unknown"))
                    print(f"      {i}. [{node_type}] {node.get('label', 'N/A')}")
                if len(nodes) > 5:
                    print(f"      ... 还有 {len(nodes) - 5} 个节点")
                
                # 验证是否包含 Mode B 特有的节点类型
                has_bridge_or_review = any(
                    node.get("type") in ["bridge", "review", "new_concept"]
                    for node in nodes
                )
                
                if has_bridge_or_review:
                    print(f"\n   ✅ 检测到 Mode B 特有的节点类型（bridge/review/new_concept）")
                else:
                    print(f"\n   ⚠️  未检测到 Mode B 特有的节点类型")
                
                return True
            else:
                print(f"\n❌ Mode B 测试失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Mode B 测试失败: HTTP {status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Mode B 测试异常: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🚀 LinkLog v3 API 测试")
    print("="*80)
    
    # 检查服务器是否运行
    try:
        req = urllib.request.Request(f"{BASE_URL}/docs")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() != 200:
                print(f"\n❌ 服务器未正常运行 (状态码: {response.getcode()})")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ 无法连接到服务器: {str(e)}")
        print(f"   请确保服务器正在运行: python3 server.py")
        sys.exit(1)
    
    print(f"\n✅ 服务器连接正常")
    
    # 运行测试
    results = []
    
    # 测试 Mode A
    results.append(("Mode A", test_mode_a()))
    
    # 等待一下，避免 API 限流
    time.sleep(2)
    
    # 测试 Mode B
    results.append(("Mode B", test_mode_b()))
    
    # 总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print(f"\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n⚠️  部分测试失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()

