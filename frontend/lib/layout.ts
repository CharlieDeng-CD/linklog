import dagre from 'dagre';
import { Node, Edge } from 'reactflow';

export type LayoutDirection = 'TB' | 'LR'; // Top to Bottom | Left to Right

export function getLayoutedElements(
  nodes: Node[], 
  edges: Edge[], 
  direction: LayoutDirection = 'TB'
) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  // 根据方向设置布局参数
  const layoutConfig = {
    rankdir: direction,
    nodesep: direction === 'TB' ? 100 : 150,  // 节点间距
    ranksep: direction === 'TB' ? 150 : 100,  // 层级间距
  };
  dagreGraph.setGraph(layoutConfig);

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 150, height: 60 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.position = {
      x: nodeWithPosition.x - 75,
      y: nodeWithPosition.y - 30,
    };
  });

  return { nodes, edges };
}

