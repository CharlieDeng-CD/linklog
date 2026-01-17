#!/usr/bin/env python3
"""
测试 LinkLog v3 Mode C (节点详情)
测试节点详情 API 的类比功能
"""
import json
import time
import sys
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_mode_c_with_context():
    """测试 Mode C: 有 context 时的类比功能"""
    print("\n" + "="*80)
    print("🧪 测试 Mode C: 节点详情（有背景知识）")
    print("="*80)
    
    payload = {
        "goal": "学习 React 开发",
        "context": "我熟悉 JavaScript 和 jQuery，有 HTML/CSS 基础",
        "node_label": "React Props"
    }
    
    print(f"\n[Request] 发送请求到 /api/v3/node-detail")
    print(f"   └─ Goal: {payload['goal']}")
    print(f"   └─ Context: {payload['context']}")
    print(f"   └─ Node: {payload['node_label']}")
    print(f"   └─ 预期: 应该提供基于背景知识的类比")
    
    start_time = time.time()
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/node-detail",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            elapsed = time.time() - start_time
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        print(f"\n[Response] 响应状态: {status_code}")
        print(f"   └─ 耗时: {elapsed:.2f}秒")
        
        if status_code == 200:
            if result.get("success"):
                data = result.get("data", {})
                
                print(f"\n✅ Mode C 测试成功！")
                print(f"\n   节点详情:")
                print(f"   └─ Title: {data.get('title', 'N/A')}")
                print(f"   └─ Definition: {data.get('definition', 'N/A')[:80]}...")
                print(f"   └─ Analogy: {data.get('analogy', 'N/A')[:80] if data.get('analogy') else '无'}")
                print(f"   └─ Importance: {data.get('importance', 'N/A')[:80]}...")
                print(f"   └─ Action Item: {data.get('action_item', 'N/A')[:80]}...")
                print(f"   └─ Resource Keywords: {data.get('resource_keywords', [])}")
                
                # 验证关键字段
                has_analogy = data.get('analogy') is not None and data.get('analogy') != ''
                has_definition = data.get('definition') is not None and data.get('definition') != ''
                has_importance = data.get('importance') is not None and data.get('importance') != ''
                has_action = data.get('action_item') is not None and data.get('action_item') != ''
                
                print(f"\n   字段验证:")
                print(f"   └─ Definition: {'✅' if has_definition else '❌'}")
                print(f"   └─ Analogy: {'✅' if has_analogy else '❌'}")
                print(f"   └─ Importance: {'✅' if has_importance else '❌'}")
                print(f"   └─ Action Item: {'✅' if has_action else '❌'}")
                
                if has_analogy:
                    print(f"\n   ✅ 检测到类比内容（应该基于背景知识：jQuery/HTML）")
                else:
                    print(f"\n   ⚠️  未检测到类比内容")
                
                all_fields_present = has_definition and has_analogy and has_importance and has_action
                return all_fields_present
            else:
                print(f"\n❌ Mode C 测试失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Mode C 测试失败: HTTP {status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Mode C 测试异常: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_mode_c_without_context():
    """测试 Mode C: 无 context 时的通用类比"""
    print("\n" + "="*80)
    print("🧪 测试 Mode C: 节点详情（无背景知识）")
    print("="*80)
    
    payload = {
        "goal": "学习 React 开发",
        "context": None,
        "node_label": "React State"
    }
    
    print(f"\n[Request] 发送请求到 /api/v3/node-detail")
    print(f"   └─ Goal: {payload['goal']}")
    print(f"   └─ Context: 无")
    print(f"   └─ Node: {payload['node_label']}")
    print(f"   └─ 预期: 应该提供通用类比（生活类比）")
    
    start_time = time.time()
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/node-detail",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            elapsed = time.time() - start_time
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        print(f"\n[Response] 响应状态: {status_code}")
        print(f"   └─ 耗时: {elapsed:.2f}秒")
        
        if status_code == 200:
            if result.get("success"):
                data = result.get("data", {})
                
                print(f"\n✅ Mode C 测试成功！")
                print(f"\n   节点详情:")
                print(f"   └─ Title: {data.get('title', 'N/A')}")
                print(f"   └─ Definition: {data.get('definition', 'N/A')[:80]}...")
                print(f"   └─ Analogy: {data.get('analogy', 'N/A')[:80] if data.get('analogy') else '无'}")
                print(f"   └─ Importance: {data.get('importance', 'N/A')[:80]}...")
                print(f"   └─ Action Item: {data.get('action_item', 'N/A')[:80]}...")
                
                # 验证关键字段
                has_analogy = data.get('analogy') is not None and data.get('analogy') != ''
                
                if has_analogy:
                    print(f"\n   ✅ 检测到通用类比（生活类比）")
                else:
                    print(f"\n   ⚠️  未检测到类比内容")
                
                return has_analogy
            else:
                print(f"\n❌ Mode C 测试失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Mode C 测试失败: HTTP {status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Mode C 测试异常: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🚀 LinkLog v3 Mode C (节点详情) 测试")
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
    
    # 测试 Mode C (有 context)
    results.append(("Mode C (有背景)", test_mode_c_with_context()))
    
    # 等待一下，避免 API 限流
    time.sleep(2)
    
    # 测试 Mode C (无 context)
    results.append(("Mode C (无背景)", test_mode_c_without_context()))
    
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

