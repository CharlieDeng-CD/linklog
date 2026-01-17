'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import ContextSidebar from './ContextSidebar';
import { getLayoutedElements } from '@/lib/layout';

interface GraphCanvasProps {
  originalGoal: string;
  initialNodes: any[];
  initialEdges: any[];
}

const nodeTypes = {
  customNode: CustomNode,
};

export default function GraphCanvas({
  originalGoal,
  initialNodes,
  initialEdges,
}: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandingNodeId, setExpandingNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // 跟踪每个节点的子节点（用于收起功能）
  const [nodeChildren, setNodeChildren] = useState<Map<string, Set<string>>>(new Map());
  // 缓存已展开节点的完整数据（节点和边），用于快速重新展开
  const [expandedNodesCache, setExpandedNodesCache] = useState<Map<string, { nodes: Node[], edges: Edge[] }>>(new Map());
  // 缓存侧边栏内容（解释内容）
  const [sidebarContextCache, setSidebarContextCache] = useState<Map<string, any>>(new Map());
  // 双击检测：用于区分单击和双击
  const [clickTimer, setClickTimer] = useState<NodeJS.Timeout | null>(null);

  // 初始化节点和边，并自动布局
  useEffect(() => {
    const reactFlowNodes: Node[] = initialNodes.map((node) => ({
      id: node.id,
      type: 'customNode',
      position: { x: 0, y: 0 }, // 临时位置，后续自动布局
      data: {
        label: node.label,
        category: node.category || 'action',
        description: node.description,
        expanded: false,
      },
    }));

    const reactFlowEdges: Edge[] = initialEdges.map((edge) => ({
      id: `e${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
    }));

    // 自动布局
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      reactFlowNodes,
      reactFlowEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
    
    // 初始化节点子节点关系（基于初始边）
    const initialChildren = new Map<string, Set<string>>();
    initialEdges.forEach(edge => {
      if (!initialChildren.has(edge.source)) {
        initialChildren.set(edge.source, new Set());
      }
      initialChildren.get(edge.source)!.add(edge.target);
    });
    setNodeChildren(initialChildren);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // 收起节点：移除该节点的所有子节点和相关的边
  const handleNodeCollapse = useCallback(
    (nodeId: string) => {
      const children = nodeChildren.get(nodeId);
      if (!children || children.size === 0) {
        return; // 没有子节点，无需收起
      }

      // 递归获取所有后代节点（包括子节点的子节点）
      const getAllDescendants = (parentId: string, visited: Set<string>): Set<string> => {
        const descendants = new Set<string>();
        const directChildren = nodeChildren.get(parentId) || new Set();
        
        for (const childId of directChildren) {
          if (!visited.has(childId)) {
            visited.add(childId);
            descendants.add(childId);
            // 递归获取子节点的后代
            const childDescendants = getAllDescendants(childId, visited);
            childDescendants.forEach(d => descendants.add(d));
          }
        }
        
        return descendants;
      };

      const allDescendants = getAllDescendants(nodeId, new Set());
      
      // 移除所有后代节点
      const remainingNodes = nodes.filter(n => !allDescendants.has(n.id));
      
      // 移除所有与后代节点相关的边
      const remainingEdges = edges.filter(
        e => !allDescendants.has(e.source) && !allDescendants.has(e.target)
      );
      
      // 标记节点为未展开
      const updatedNodes = remainingNodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, expanded: false } } : n
      );
      
      // 清除该节点的子节点记录
      const newNodeChildren = new Map(nodeChildren);
      newNodeChildren.delete(nodeId);
      // 同时清除所有后代的子节点记录
      allDescendants.forEach(descId => newNodeChildren.delete(descId));
      setNodeChildren(newNodeChildren);
      
      // 重新布局
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        updatedNodes,
        remainingEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    },
    [nodes, edges, nodeChildren, setNodes, setEdges]
  );

  const handleNodeClick = useCallback(
    async (event: React.MouseEvent, node: Node) => {
      // 双击处理：收起或展开节点，不打开侧边栏
      if (event.detail === 2) {
        // 清除单击定时器（如果有）
        if (clickTimer) {
          clearTimeout(clickTimer);
          setClickTimer(null);
        }
        
        if (node.data.expanded) {
          // 已展开，收起节点
          handleNodeCollapse(node.id);
        } else {
          // 未展开，展开节点（使用缓存或调用 API）
          await expandNode(node);
        }
        return;
      }

      // 单击处理：延迟执行，如果检测到双击则取消
      if (clickTimer) {
        clearTimeout(clickTimer);
      }

      const timer = setTimeout(async () => {
        // 打开侧边栏（使用缓存或调用 API）
      setSelectedNode(node);
      setSidebarOpen(true);

      // 如果节点还未展开，则展开它
      if (!node.data.expanded && !expandingNodeId) {
          await expandNode(node);
        }
        
        setClickTimer(null);
      }, 200); // 200ms 延迟，用于检测双击

      setClickTimer(timer);
    },
    [originalGoal, nodes, edges, nodeChildren, expandedNodesCache, sidebarContextCache, setNodes, setEdges, expandingNodeId, handleNodeCollapse, clickTimer]
  );

  // 展开节点的函数（提取出来，供单击和双击使用）
  const expandNode = useCallback(
    async (node: Node) => {
      // 先检查缓存，如果存在则立即使用缓存数据
      const cachedData = expandedNodesCache.get(node.id);
      if (cachedData) {
        // 使用缓存数据，立即展开（无需等待 API）
        const allNodes = [...nodes, ...cachedData.nodes];
        const allEdges = [...edges, ...cachedData.edges];
        
        // 标记节点为已展开
        const updatedNodes = allNodes.map((n) =>
          n.id === node.id ? { ...n, data: { ...n.data, expanded: true } } : n
        );

        // 记录子节点关系
        const childIds = new Set(cachedData.nodes.map(n => n.id));
        const newNodeChildren = new Map(nodeChildren);
        newNodeChildren.set(node.id, childIds);
        setNodeChildren(newNodeChildren);

        // 自动布局
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          updatedNodes,
          allEdges
        );

        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
        return; // 使用缓存，直接返回
      }

      // 缓存不存在，调用 API
        setExpandingNodeId(node.id);
        setLoading(true);
        
        try {
          const nodePath = [originalGoal, node.data.label];
          const existingNodes = nodes.map((n) => ({
            label: n.data.label,
            id: n.id,
          }));

          const response = await fetch('/api/v2/expand', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              original_goal: originalGoal,
              node_id: node.id,
              node_label: node.data.label,
              node_path: nodePath,
              node_category: node.data.category,
              existing_nodes: existingNodes,
            }),
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API 错误 ${response.status}: ${errorText.substring(0, 100)}`);
          }

          const contentType = response.headers.get('content-type');
          if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`响应不是 JSON: ${text.substring(0, 100)}`);
          }

          const result = await response.json();

          if (result.success && result.data.nodes.length > 0) {
            // 添加新节点（临时位置）
            const newNodes: Node[] = result.data.nodes.map((newNode: any) => ({
              id: newNode.id,
              type: 'customNode',
              position: { x: 0, y: 0 }, // 临时位置，后续自动布局
              data: {
                label: newNode.label,
                category: newNode.category || 'action',
                description: newNode.description,
                expanded: false,
              },
            }));

            // 添加新边
            const newEdges: Edge[] = result.data.edges.map((edge: any) => ({
              id: `e${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
            }));

          // 保存到缓存
          const newCache = new Map(expandedNodesCache);
          newCache.set(node.id, { nodes: newNodes, edges: newEdges });
          setExpandedNodesCache(newCache);

            // 记录子节点关系
            const childIds = new Set(newNodes.map(n => n.id));
            const newNodeChildren = new Map(nodeChildren);
            newNodeChildren.set(node.id, childIds);
            setNodeChildren(newNodeChildren);

            // 合并所有节点和边，然后重新布局
            const allNodes = [...nodes, ...newNodes];
            const allEdges = [...edges, ...newEdges];
            
            // 标记节点为已展开
            const updatedNodes = allNodes.map((n) =>
              n.id === node.id ? { ...n, data: { ...n.data, expanded: true } } : n
            );

            // 自动布局
            const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
              updatedNodes,
              allEdges
            );

            setNodes(layoutedNodes);
            setEdges(layoutedEdges);
          }
        } catch (error) {
          console.error('展开节点失败:', error);
          alert('展开节点失败，请重试');
        } finally {
          setExpandingNodeId(null);
          setLoading(false);
      }
    },
    [originalGoal, nodes, edges, nodeChildren, expandedNodesCache, setNodes, setEdges]
  );


  return (
    <div className="fluid-gradient min-h-screen relative">
      {loading && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 glass px-6 py-3 rounded-lg">
          <div className="text-white">正在生成子节点...</div>
        </div>
      )}
      
      <div className={`absolute inset-0 ${sidebarOpen ? 'blur-sm' : ''} transition-all`}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      {sidebarOpen && selectedNode && (
        <ContextSidebar
          node={selectedNode}
          originalGoal={originalGoal}
          contextCache={sidebarContextCache}
          setContextCache={setSidebarContextCache}
          onClose={() => {
            setSidebarOpen(false);
            setSelectedNode(null);
          }}
        />
      )}
    </div>
  );
}

