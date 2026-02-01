/**
 * localStorage 工具函数
 * 用于保存和读取用户生成的图谱数据
 */

export interface GraphCache {
  id: string; // 唯一标识（时间戳 + 随机数）
  goal: string;
  context?: string;
  nodes: any[];
  edges: any[];
  createdAt: number; // 创建时间戳
  updatedAt: number; // 最后更新时间戳
}

const STORAGE_KEY = 'linklog_graphs';
const MAX_CACHED_GRAPHS = 10; // 最多保存 10 个图谱

/**
 * 获取所有缓存的图谱
 */
export function getCachedGraphs(): GraphCache[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];
    
    const graphs: GraphCache[] = JSON.parse(data);
    // 按更新时间倒序排列（最新的在前）
    return graphs.sort((a, b) => b.updatedAt - a.updatedAt);
  } catch (error) {
    console.error('读取缓存图谱失败:', error);
    return [];
  }
}

/**
 * 保存图谱到缓存
 */
export function saveGraphToCache(graph: Omit<GraphCache, 'id' | 'createdAt' | 'updatedAt'>): string {
  if (typeof window === 'undefined') return '';
  
  try {
    const graphs = getCachedGraphs();
    
    // 生成唯一 ID
    const id = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const now = Date.now();
    
    const newGraph: GraphCache = {
      id,
      ...graph,
      createdAt: now,
      updatedAt: now,
    };
    
    // 如果已存在相同的 goal（且 context 也相同），则更新而不是新增
    const existingIndex = graphs.findIndex(
      g => g.goal === graph.goal && g.context === graph.context
    );
    
    if (existingIndex >= 0) {
      // 更新现有图谱
      graphs[existingIndex] = {
        ...graphs[existingIndex],
        ...newGraph,
        createdAt: graphs[existingIndex].createdAt, // 保留原始创建时间
        updatedAt: now,
      };
    } else {
      // 添加新图谱
      graphs.unshift(newGraph);
      
      // 如果超过最大数量，删除最旧的
      if (graphs.length > MAX_CACHED_GRAPHS) {
        graphs.pop();
      }
    }
    
    // 保存到 localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(graphs));
    
    return id;
  } catch (error) {
    console.error('保存图谱到缓存失败:', error);
    return '';
  }
}

/**
 * 根据 ID 获取单个图谱
 */
export function getGraphById(id: string): GraphCache | null {
  const graphs = getCachedGraphs();
  return graphs.find(g => g.id === id) || null;
}

/**
 * 删除指定的图谱
 */
export function deleteGraphFromCache(id: string): boolean {
  if (typeof window === 'undefined') return false;
  
  try {
    const graphs = getCachedGraphs();
    const filtered = graphs.filter(g => g.id !== id);
    
    if (filtered.length === graphs.length) {
      return false; // 没找到
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  } catch (error) {
    console.error('删除图谱失败:', error);
    return false;
  }
}

/**
 * 清空所有缓存
 */
export function clearAllGraphs(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('清空缓存失败:', error);
  }
}
