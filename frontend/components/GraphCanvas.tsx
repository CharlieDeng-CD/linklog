'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import V3ContextSidebar from './V3ContextSidebar';
import ColorLegend from './ColorLegend';
import { getLayoutedElements, LayoutDirection } from '@/lib/layout';
import { convertToMermaid } from '@/lib/mermaid';
import { getCachedGraphs, deleteGraphFromCache, GraphCache } from '@/lib/storage';
import { trackMermaidExported, trackGraphSwitched, trackConceptIntegrated, trackNodeExpanded, trackNodeDetailViewed } from '@/lib/analytics';
import { ArrowDown, ArrowRight, RotateCw, Layout, Link2, X, Code, Copy, Check, History, Trash2 } from 'lucide-react';

interface GraphCanvasProps {
  originalGoal: string;
  userContext?: string;  // v3: 用户背景知识（可选）
  initialNodes: any[];
  initialEdges: any[];
  onSwitchGraph?: (goal: string, context: string | undefined, nodes: any[], edges: any[]) => void; // 切换图谱的回调
}

const nodeTypes = {
  customNode: CustomNode,
};

export default function GraphCanvas({
  originalGoal,
  userContext,
  initialNodes,
  initialEdges,
  onSwitchGraph,
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
  // 布局方向：从上往下 (TB) 或从左往右 (LR)
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('TB');
  // 关联新概念 Modal 状态
  const [showIntegrateModal, setShowIntegrateModal] = useState(false);
  const [newConceptInput, setNewConceptInput] = useState('');
  const [integrating, setIntegrating] = useState(false);
  // Mermaid 导出 Modal 状态
  const [showMermaidModal, setShowMermaidModal] = useState(false);
  const [mermaidCode, setMermaidCode] = useState('');
  const [copied, setCopied] = useState(false);
  // 历史记录状态
  const [showHistory, setShowHistory] = useState(false);
  const [cachedGraphs, setCachedGraphs] = useState<GraphCache[]>([]);

  // 加载缓存的图谱列表
  useEffect(() => {
    const graphs = getCachedGraphs();
    // 过滤掉当前图谱
    const filtered = graphs.filter(g => !(g.goal === originalGoal && g.context === userContext));
    setCachedGraphs(filtered);
  }, [originalGoal, userContext]);

  // 切换图谱
  const handleSwitchGraph = useCallback((graph: GraphCache) => {
    if (onSwitchGraph) {
      onSwitchGraph(graph.goal, graph.context, graph.nodes, graph.edges);
      setShowHistory(false);
      
      // 追踪事件
      trackGraphSwitched(graph.goal);
    }
  }, [onSwitchGraph]);

  // 删除缓存图谱
  const handleDeleteGraph = useCallback((e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('确定要删除这个图谱吗？')) {
      deleteGraphFromCache(id);
      const graphs = getCachedGraphs();
      const filtered = graphs.filter(g => !(g.goal === originalGoal && g.context === userContext));
      setCachedGraphs(filtered);
    }
  }, [originalGoal, userContext]);

  // 使用 ref 存储回调函数，避免循环依赖
  const handleExpandButtonRef = useRef<((node: Node) => Promise<void>) | null>(null);
  const handleDetailButtonRef = useRef<((node: Node) => void) | null>(null);

  // 初始化节点和边，并自动布局
  useEffect(() => {
    const reactFlowNodes: Node[] = initialNodes.map((node) => ({
      id: node.id,
      type: 'customNode',
      position: { x: 0, y: 0 }, // 临时位置，后续自动布局
      data: {
        label: node.label,
        category: node.category || node.type || 'action',
        description: node.description,
        level: node.level, // 保存层级信息
        expanded: false,
      },
    }));

    const reactFlowEdges: Edge[] = initialEdges.map((edge) => ({
      id: `e${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      markerEnd: {
        type: MarkerType.ArrowClosed,
      },
      style: { stroke: 'rgba(255, 255, 255, 0.4)', strokeWidth: 2 },
    }));

    // 自动布局
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      reactFlowNodes,
      reactFlowEdges,
      layoutDirection
    );

    // 直接添加回调，避免额外的 useEffect
    const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
    setNodes(enrichedNodes);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNodes, initialEdges, layoutDirection]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    []
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
        remainingEdges,
        layoutDirection
      );

      const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
      setNodes(enrichedNodes);
      setEdges(layoutedEdges);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [nodes, edges, nodeChildren, layoutDirection]
  );

  const handleNodeClick = useCallback(
    async (event: React.MouseEvent, node: Node) => {
      // 现在节点点击主要用于拖拽等操作，具体功能由按钮处理
      // 保留双击收起功能作为快捷方式
      if (event.detail === 2 && node.data.expanded) {
        handleNodeCollapse(node.id);
      }
    },
    [handleNodeCollapse]
  );

  // 展开节点的函数（提取出来，供按钮使用）
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
          allEdges,
          layoutDirection
        );

        const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
        setNodes(enrichedNodes);
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
              node_level: node.data.level, // 传递节点层级
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
                category: newNode.category || newNode.type || 'action',
                description: newNode.description,
                level: newNode.level, // 保存层级信息（展开的节点通常是 Level 2）
                expanded: false,
              },
            }));

            // 添加新边
            const newEdges: Edge[] = result.data.edges.map((edge: any) => ({
              id: `e${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
              style: { stroke: 'rgba(255, 255, 255, 0.4)', strokeWidth: 2 },
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
              allEdges,
              layoutDirection
            );

            const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
            setNodes(enrichedNodes);
            setEdges(layoutedEdges);
            
            // 追踪事件
            trackNodeExpanded(node.data.label, node.data.category || 'unknown', newNodes.length);
          }
        } catch (error) {
          console.error('展开节点失败:', error);
          alert('展开节点失败，请重试');
        } finally {
          setExpandingNodeId(null);
          setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [originalGoal, nodes, edges, nodeChildren, expandedNodesCache, layoutDirection]
  );

  // 处理展开按钮点击
  const handleExpandButton = useCallback(
    async (node: Node) => {
      if (node.data.expanded) {
        // 已展开，收起节点
        handleNodeCollapse(node.id);
      } else {
        // 未展开，展开节点
        await expandNode(node);
      }
    },
    [expandNode, handleNodeCollapse]
  );

  // 处理内容说明按钮点击
  const handleDetailButton = useCallback(
    (node: Node) => {
      setSelectedNode(node);
      setSidebarOpen(true);
      
      // 追踪事件
      trackNodeDetailViewed(node.data.label);
    },
    []
  );

  // 更新 ref，确保回调函数始终是最新的
  useEffect(() => {
    handleExpandButtonRef.current = handleExpandButton;
    handleDetailButtonRef.current = handleDetailButton;
  }, [handleExpandButton, handleDetailButton]);

  // 为节点添加按钮回调函数
  const enrichNodesWithCallbacks = useCallback(
    (nodesToEnrich: Node[]): Node[] => {
      // 只为普通节点添加回调
      const filteredNodes = nodesToEnrich.filter(n => n.type === 'customNode');

      const enriched = filteredNodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onExpand: () => handleExpandButtonRef.current?.(node),
          onShowDetail: () => handleDetailButtonRef.current?.(node),
        },
      }));

      return enriched;
    },
    [handleExpandButton, handleDetailButton]
  );

  // 更新所有节点，添加按钮回调（用于初始化后更新）
  useEffect(() => {
    if (nodes.length > 0) {
      // 检查是否需要添加回调（只检查一次，避免无限循环）
      const needsUpdate = nodes.some((node) => {
        return node.type === 'customNode' && (!node.data.onExpand || !node.data.onShowDetail);
      });
      if (needsUpdate) {
        const enrichedNodes = enrichNodesWithCallbacks(nodes);
        setNodes(enrichedNodes);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length]);

  // 当布局方向改变时，重新布局所有节点
  useEffect(() => {
    if (nodes.length > 0 && edges.length > 0) {
      // 移除位置信息，重新布局
      const nodesWithoutPosition = nodes.map(node => ({
        ...node,
        position: { x: 0, y: 0 }
      }));
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodesWithoutPosition,
        edges,
        layoutDirection
      );
      const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
      setNodes(enrichedNodes);
      setEdges(layoutedEdges);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layoutDirection]); // 只在 layoutDirection 改变时触发

  // 切换布局方向
  const toggleLayoutDirection = useCallback(() => {
    setLayoutDirection(prev => prev === 'TB' ? 'LR' : 'TB');
  }, []);

  // 关联新概念到图谱
  const handleIntegrateNode = useCallback(async () => {
    if (!newConceptInput.trim()) {
      alert('请输入新概念');
      return;
    }

    setIntegrating(true);
    try {
      // 准备现有节点数据
      const existingNodes = nodes
        .filter(n => n.type === 'customNode')
        .map(n => ({
          id: n.id,
          label: n.data?.label || '',
          category: n.data?.category || n.data?.type || 'concept',
          level: n.data?.level ?? 1,
        }));

      const response = await fetch('/api/v3/integrate-node', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          goal: originalGoal,
          context: userContext,
          existing_nodes: existingNodes,
          new_concept: newConceptInput.trim(),
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API 错误 ${response.status}: ${errorText.substring(0, 100)}`);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        throw new Error(`响应不是 JSON: ${text.substring(0, 200)}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.detail || 'API 返回失败');
      }

      if (!result.data) {
        throw new Error('API 返回数据为空');
      }

      const { node: newNodeData, edges: newEdgesData } = result.data;

      // 验证返回数据
      if (!newNodeData || !newEdgesData) {
        throw new Error('返回数据格式不正确：缺少 node 或 edges');
      }

      if (!newNodeData.id || !newNodeData.label) {
        throw new Error('返回节点数据不完整：缺少 id 或 label');
      }

      // 创建新节点
      // 通过"关联新概念"添加的节点统一使用 known 样式（虚线边框和白色半透明）
      // 因为这是用户主动添加的已知知识
      const newNode: Node = {
        id: newNodeData.id,
        type: 'customNode',
        position: { x: 0, y: 0 }, // 临时位置，后续自动布局
        data: {
          label: newNodeData.label,
          category: 'known', // 统一使用 known 样式
          description: newNodeData.description,
          level: 3, // 统一使用 level 3（已知基石）
          expanded: false,
        },
      };

      // 创建新边（验证边的有效性）
      const newEdges: Edge[] = newEdgesData
        .filter((edge: any) => edge.source && edge.target) // 过滤无效边
        .map((edge: any) => {
          // 检查目标节点是否存在（在合并前检查）
          const targetExists = nodes.some(n => n.id === edge.target);
          if (!targetExists) {
            console.warn(`警告：目标节点 ${edge.target} 不存在，跳过此边`);
            return null;
          }
          return {
            id: `e${edge.source}-${edge.target}`,
            source: edge.source,
            target: edge.target,
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
            style: { stroke: 'rgba(255, 255, 255, 0.4)', strokeWidth: 2 },
          };
        })
        .filter((edge: Edge | null) => edge !== null) as Edge[];

      // 检查是否有有效的边
      if (newEdges.length === 0) {
        throw new Error('没有有效的连接关系，请检查新概念与现有节点的关联');
      }

      // 合并节点和边
      const allNodes = [...nodes, newNode];
      const allEdges = [...edges, ...newEdges];

      // 重新布局
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        allNodes,
        allEdges,
        layoutDirection
      );

      // 添加回调并更新
      const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
      setNodes(enrichedNodes);
      setEdges(layoutedEdges);

      // 关闭 Modal 并清空输入
      setShowIntegrateModal(false);
      setNewConceptInput('');
      
      // 追踪事件
      trackConceptIntegrated(newConceptInput.trim());
    } catch (error) {
      console.error('关联新概念失败:', error);
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      alert(`关联新概念失败: ${errorMessage}\n\n请检查浏览器控制台查看详细信息。`);
    } finally {
      setIntegrating(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newConceptInput, nodes, edges, originalGoal, userContext, layoutDirection, enrichNodesWithCallbacks]);

  // 格式化图谱：一键恢复排版
  const formatGraph = useCallback(() => {
    if (nodes.length > 0 && edges.length > 0) {
      // 移除所有节点的位置信息，重新布局
      const nodesWithoutPosition = nodes.map(node => ({
        ...node,
        position: { x: 0, y: 0 }
      }));
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodesWithoutPosition,
        edges,
        layoutDirection
      );
      const enrichedNodes = enrichNodesWithCallbacks(layoutedNodes);
      setNodes(enrichedNodes);
      setEdges(layoutedEdges);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, layoutDirection, enrichNodesWithCallbacks]);

  // 处理导出 Mermaid
  const handleExportMermaid = useCallback(() => {
    const code = convertToMermaid(nodes, edges, layoutDirection);
    setMermaidCode(code);
    setShowMermaidModal(true);
    setCopied(false);
    
    // 追踪事件
    trackMermaidExported(nodes.length, edges.length);
  }, [nodes, edges, layoutDirection]);

  // 复制代码到剪贴板
  const copyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(mermaidCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [mermaidCode]);

  return (
    <div className="fluid-gradient min-h-screen h-screen relative flex flex-col">
      {/* 功能栏：固定在顶部 */}
      <div className={`glass border-b border-white/10 px-6 py-3 flex items-center justify-between z-50 flex-shrink-0 transition-all ${sidebarOpen ? 'blur-sm' : ''}`}>
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white">图谱控制</h3>
        </div>
        <div className="flex items-center gap-3">
          {/* 旋转图谱按钮 */}
          <button
            onClick={toggleLayoutDirection}
            className="glass bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2 shadow-md hover:shadow-lg transition-all flex items-center gap-2 text-white"
            title={layoutDirection === 'TB' ? '切换到从左往右' : '切换到从上往下'}
          >
            <RotateCw size={18} />
            <span className="text-sm">
              {layoutDirection === 'TB' ? '横向布局' : '纵向布局'}
            </span>
          </button>
          
          {/* 格式化图谱按钮 */}
          <button
            onClick={formatGraph}
            className="glass bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2 shadow-md hover:shadow-lg transition-all flex items-center gap-2 text-white"
            title="一键恢复图谱排版"
          >
            <Layout size={18} />
            <span className="text-sm">格式化</span>
          </button>

          {/* 关联新概念按钮 */}
          <button
            onClick={() => setShowIntegrateModal(true)}
            className="glass bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2 shadow-md hover:shadow-lg transition-all flex items-center gap-2 text-white"
            title="关联新概念到图谱"
          >
            <Link2 size={18} />
            <span className="text-sm">关联新概念</span>
          </button>

          {/* 导出 Mermaid 按钮 */}
          <button
            onClick={handleExportMermaid}
            className="glass bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2 shadow-md hover:shadow-lg transition-all flex items-center gap-2 text-white"
            title="导出为 Mermaid 代码"
          >
            <Code size={18} />
            <span className="text-sm">导出 Mermaid</span>
          </button>

          {/* 历史记录按钮 */}
          {onSwitchGraph && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="glass bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2 shadow-md hover:shadow-lg transition-all flex items-center gap-2 text-white"
              title="切换其他图谱"
            >
              <History size={18} />
              <span className="text-sm">
                历史记录 {cachedGraphs.length > 0 && `(${cachedGraphs.length})`}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* 历史记录面板 */}
      {showHistory && onSwitchGraph && (
        <div className="absolute top-16 right-6 z-[55] glass bg-white/10 border border-white/20 rounded-xl shadow-xl p-4 w-80 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-semibold flex items-center gap-2">
              <History size={16} />
              切换图谱 {cachedGraphs.length > 0 && `(${cachedGraphs.length})`}
            </h3>
            <button
              type="button"
              onClick={() => setShowHistory(false)}
              className="text-white/60 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
          </div>
          {cachedGraphs.length > 0 ? (
            <div className="space-y-2">
              {cachedGraphs.map((graph) => (
                <div
                  key={graph.id}
                  onClick={() => handleSwitchGraph(graph)}
                  className="p-3 glass bg-white/10 hover:bg-white/15 border border-white/20 rounded-lg cursor-pointer transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium truncate">{graph.goal}</p>
                      {graph.context && (
                        <p className="text-white/60 text-xs mt-1 truncate">
                          背景: {graph.context}
                        </p>
                      )}
                      <p className="text-white/40 text-xs mt-1">
                        {new Date(graph.updatedAt).toLocaleString('zh-CN')}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteGraph(e, graph.id)}
                      className="ml-2 p-1 text-white/40 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                      title="删除"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-white/60 text-sm">暂无其他图谱</p>
              <p className="text-white/40 text-xs mt-2">生成更多图谱后可以在这里切换</p>
            </div>
          )}
        </div>
      )}

      {/* Mermaid 导出 Modal */}
      {showMermaidModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="glass border border-white/20 rounded-lg shadow-xl p-6 w-full max-w-2xl mx-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Code className="text-white" size={20} />
                <h3 className="text-lg font-semibold text-white">导出 Mermaid 代码</h3>
              </div>
              <button
                onClick={() => setShowMermaidModal(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="relative mb-4">
              <pre className="w-full h-64 overflow-auto p-4 glass bg-black/30 border border-white/10 rounded-lg text-white/90 font-mono text-sm whitespace-pre">
                {mermaidCode}
              </pre>
              <button
                onClick={copyToClipboard}
                className="absolute top-3 right-3 p-2 glass bg-white/10 hover:bg-white/20 border border-white/20 rounded-md text-white transition-all flex items-center gap-2"
                title="复制代码到剪贴板"
              >
                {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                <span className="text-xs">{copied ? '已复制' : '复制'}</span>
              </button>
            </div>

            <p className="text-sm text-white/60 mb-6">
              你可以将此代码粘贴到支持 Mermaid 的工具中（如 Notion, Obsidian, GitHub README 等）。
            </p>

            <div className="flex justify-end">
              <button
                onClick={() => setShowMermaidModal(false)}
                className="px-6 py-2 glass bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 关联新概念 Modal */}
      {showIntegrateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="glass border border-white/20 rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">关联新概念</h3>
              <button
                onClick={() => {
                  setShowIntegrateModal(false);
                  setNewConceptInput('');
                }}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-white/80 mb-2">
                新发现的概念
              </label>
              <input
                type="text"
                value={newConceptInput}
                onChange={(e) => setNewConceptInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !integrating) {
                    handleIntegrateNode();
                  }
                }}
                placeholder="例如：MCP"
                className="w-full px-4 py-2 glass bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                disabled={integrating}
                autoFocus
              />
              <p className="mt-2 text-xs text-white/60">
                输入你新发现的概念，系统会自动分析它与现有图谱的关系
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowIntegrateModal(false);
                  setNewConceptInput('');
                }}
                className="flex-1 px-4 py-2 glass bg-white/5 hover:bg-white/10 border border-white/20 rounded-lg text-white transition-all"
                disabled={integrating}
              >
                取消
              </button>
              <button
                onClick={handleIntegrateNode}
                disabled={integrating || !newConceptInput.trim()}
                className="flex-1 px-4 py-2 glass bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {integrating ? '关联中...' : '关联'}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-50 glass px-6 py-3 rounded-lg">
          <div className="text-white">正在生成子节点...</div>
        </div>
      )}
      
      <div className={`flex-1 relative overflow-hidden ${sidebarOpen ? 'blur-sm' : ''} transition-all`}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={{
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
            style: { stroke: 'rgba(255, 255, 255, 0.4)', strokeWidth: 2 },
          }}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      {sidebarOpen && selectedNode && (
        <V3ContextSidebar
          node={selectedNode}
          originalGoal={originalGoal}
          userContext={userContext}
          contextCache={sidebarContextCache}
          setContextCache={setSidebarContextCache}
          onClose={() => {
            setSidebarOpen(false);
            setSelectedNode(null);
          }}
        />
      )}

      {/* 颜色说明组件 */}
      <ColorLegend />
    </div>
  );
}

