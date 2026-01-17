#!/usr/bin/env python3
"""
测试 LinkLog v3 完整流程
1. Mode A: 无 context 生成图谱
2. Mode B: 有 context 生成图谱
3. Mode C: 获取节点详情（有/无 context）
"""
import json
import time
import sys
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_mode_a():
    """测试 Mode A: 无 context 生成图谱"""
    print("\n" + "="*80)
    print("🧪 测试 Mode A: 生成初始图谱（无 context）")
    print("="*80)
    
    payload = {"goal": "学习 React 开发"}
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/init",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        if status_code == 200 and result.get("success"):
            nodes = result.get("data", {}).get("nodes", [])
            print(f"✅ Mode A 成功: 生成 {len(nodes)} 个节点")
            return nodes[0] if nodes else None
        else:
            print(f"❌ Mode A 失败")
            return None
    except Exception as e:
        print(f"❌ Mode A 异常: {str(e)}")
        return None


def test_mode_b():
    """测试 Mode B: 有 context 生成图谱"""
    print("\n" + "="*80)
    print("🧪 测试 Mode B: 生成初始图谱（有 context）")
    print("="*80)
    
    payload = {
        "goal": "学习 React 开发",
        "context": "我熟悉 JavaScript 和 jQuery"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/init",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        if status_code == 200 and result.get("success"):
            nodes = result.get("data", {}).get("nodes", [])
            print(f"✅ Mode B 成功: 生成 {len(nodes)} 个节点")
            
            # 检查是否有 bridge/review/new_concept 类型
            has_special_types = any(
                node.get("type") in ["bridge", "review", "new_concept"]
                for node in nodes
            )
            if has_special_types:
                print(f"   ✅ 检测到 Mode B 特有的节点类型")
            
            return nodes[0] if nodes else None
        else:
            print(f"❌ Mode B 失败")
            return None
    except Exception as e:
        print(f"❌ Mode B 异常: {str(e)}")
        return None


def test_mode_c(goal, context, node_label):
    """测试 Mode C: 获取节点详情"""
    print(f"\n🧪 测试 Mode C: 节点详情")
    print(f"   └─ Goal: {goal}")
    print(f"   └─ Context: {context or '无'}")
    print(f"   └─ Node: {node_label}")
    
    payload = {
        "goal": goal,
        "context": context,
        "node_label": node_label
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v3/node-detail",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            status_code = response.getcode()
            result = json.loads(response.read().decode('utf-8'))
        
        if status_code == 200 and result.get("success"):
            data = result.get("data", {})
            has_analogy = data.get("analogy") is not None and data.get("analogy") != ""
            has_definition = data.get("definition") is not None and data.get("definition") != ""
            has_importance = data.get("importance") is not None and data.get("importance") != ""
            has_action = data.get("action_item") is not None and data.get("action_item") != ""
            
            print(f"✅ Mode C 成功")
            print(f"   └─ Definition: {'✅' if has_definition else '❌'}")
            print(f"   └─ Analogy: {'✅' if has_analogy else '❌'}")
            print(f"   └─ Importance: {'✅' if has_importance else '❌'}")
            print(f"   └─ Action: {'✅' if has_action else '❌'}")
            
            if has_analogy:
                print(f"   └─ 类比内容: {data.get('analogy', '')[:60]}...")
            
            return has_definition and has_analogy and has_importance and has_action
        else:
            print(f"❌ Mode C 失败: {result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"❌ Mode C 异常: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🚀 LinkLog v3 完整流程测试")
    print("="*80)
    
    # 检查服务器
    try:
        req = urllib.request.Request(f"{BASE_URL}/docs")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() != 200:
                print(f"\n❌ 服务器未正常运行")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ 无法连接到服务器: {str(e)}")
        sys.exit(1)
    
    print(f"\n✅ 服务器连接正常")
    
    results = []
    
    # 1. 测试 Mode A
    print("\n" + "="*80)
    print("📋 步骤 1: 测试 Mode A（全量模式）")
    print("="*80)
    mode_a_node = test_mode_a()
    results.append(("Mode A", mode_a_node is not None))
    time.sleep(2)
    
    # 2. 测试 Mode B
    print("\n" + "="*80)
    print("📋 步骤 2: 测试 Mode B（差量模式）")
    print("="*80)
    mode_b_node = test_mode_b()
    results.append(("Mode B", mode_b_node is not None))
    time.sleep(2)
    
    # 3. 测试 Mode C（无 context）
    print("\n" + "="*80)
    print("📋 步骤 3: 测试 Mode C（节点详情 - 无 context）")
    print("="*80)
    if mode_a_node:
        node_label = mode_a_node.get("label", "React State")
        mode_c_result = test_mode_c("学习 React 开发", None, node_label)
        results.append(("Mode C (无背景)", mode_c_result))
    else:
        # 使用默认节点
        mode_c_result = test_mode_c("学习 React 开发", None, "React State")
        results.append(("Mode C (无背景)", mode_c_result))
    time.sleep(2)
    
    # 4. 测试 Mode C（有 context）
    print("\n" + "="*80)
    print("📋 步骤 4: 测试 Mode C（节点详情 - 有 context）")
    print("="*80)
    if mode_b_node:
        node_label = mode_b_node.get("label", "React Props")
        mode_c_result = test_mode_c("学习 React 开发", "我熟悉 JavaScript 和 jQuery", node_label)
        results.append(("Mode C (有背景)", mode_c_result))
    else:
        # 使用默认节点
        mode_c_result = test_mode_c("学习 React 开发", "我熟悉 JavaScript 和 jQuery", "React Props")
        results.append(("Mode C (有背景)", mode_c_result))
    
    # 总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print(f"\n🎉 所有测试通过！v3 完整流程工作正常！")
        sys.exit(0)
    else:
        print(f"\n⚠️  部分测试失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()

