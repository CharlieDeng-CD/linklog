/**
 * PostHog 事件追踪工具函数
 * 统一管理所有分析事件
 */

import posthog from 'posthog-js';

// 检查 PostHog 是否已加载
function isPostHogLoaded(): boolean {
  if (typeof window === 'undefined') return false;
  
  // 检查 PostHog 是否已初始化
  const isLoaded = posthog.__loaded === true;
  
  // 如果未加载，输出调试信息
  if (!isLoaded) {
    console.warn('[PostHog] 事件追踪失败：PostHog 尚未加载', {
      __loaded: posthog.__loaded,
      hasPosthog: typeof posthog !== 'undefined',
    });
  }
  
  return isLoaded;
}

/**
 * 追踪图谱生成事件
 */
export function trackGraphGenerated(goal: string, hasContext: boolean, mode: 'Mode A' | 'Mode B', nodeCount: number, edgeCount: number) {
  if (!isPostHogLoaded()) {
    console.warn('[PostHog] 跳过事件追踪：graph_generated（PostHog 未加载）');
    return;
  }
  
  try {
    posthog.capture('graph_generated', {
      goal,
      has_context: hasContext,
      mode,
      node_count: nodeCount,
      edge_count: edgeCount,
    });
    console.log('[PostHog] ✅ 事件已发送：graph_generated', { goal, mode, nodeCount });
  } catch (error) {
    console.error('[PostHog] ❌ 事件发送失败：graph_generated', error);
  }
}

/**
 * 追踪节点展开事件
 */
export function trackNodeExpanded(nodeLabel: string, nodeCategory: string, newNodesCount: number) {
  if (!isPostHogLoaded()) return;
  
  posthog.capture('node_expanded', {
    node_label: nodeLabel,
    node_category: nodeCategory,
    new_nodes_count: newNodesCount,
  });
}

/**
 * 追踪 Mermaid 导出事件
 */
export function trackMermaidExported(nodeCount: number, edgeCount: number) {
  if (!isPostHogLoaded()) {
    console.warn('[PostHog] 跳过事件追踪：mermaid_exported（PostHog 未加载）');
    return;
  }
  
  try {
    posthog.capture('mermaid_exported', {
      node_count: nodeCount,
      edge_count: edgeCount,
    });
    console.log('[PostHog] ✅ 事件已发送：mermaid_exported', { nodeCount, edgeCount });
  } catch (error) {
    console.error('[PostHog] ❌ 事件发送失败：mermaid_exported', error);
  }
}

/**
 * 追踪图谱切换事件
 */
export function trackGraphSwitched(goal: string) {
  if (!isPostHogLoaded()) return;
  
  posthog.capture('graph_switched', {
    goal,
  });
}

/**
 * 追踪新概念关联事件
 */
export function trackConceptIntegrated(concept: string) {
  if (!isPostHogLoaded()) return;
  
  posthog.capture('concept_integrated', {
    concept,
  });
}

/**
 * 追踪节点详情查看事件
 */
export function trackNodeDetailViewed(nodeLabel: string) {
  if (!isPostHogLoaded()) return;
  
  posthog.capture('node_detail_viewed', {
    node_label: nodeLabel,
  });
}
