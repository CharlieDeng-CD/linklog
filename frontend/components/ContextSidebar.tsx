'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Node } from 'reactflow';

interface ContextSidebarProps {
  node: Node;
  originalGoal: string;
  contextCache: Map<string, any>;
  setContextCache: (cache: Map<string, any>) => void;
  onClose: () => void;
}

export default function ContextSidebar({
  node,
  originalGoal,
  contextCache,
  setContextCache,
  onClose,
}: ContextSidebarProps) {
  const [context, setContext] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 先检查缓存
    const cachedContext = contextCache.get(node.id);
    if (cachedContext) {
      // 使用缓存，立即显示
      setContext(cachedContext);
      setLoading(false);
      return;
    }

    // 缓存不存在，调用 API
    const fetchContext = async () => {
      setLoading(true);
      try {
        const nodePath = [originalGoal, node.data.label];
        const response = await fetch('/api/v2/context', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            node_id: node.id,
            node_label: node.data.label,
            original_goal: originalGoal,
            node_path: nodePath,
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
        if (result.success) {
          setContext(result.data);
          // 保存到缓存
          const newCache = new Map(contextCache);
          newCache.set(node.id, result.data);
          setContextCache(newCache);
        }
      } catch (error) {
        console.error('获取上下文失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchContext();
  }, [node, originalGoal, contextCache, setContextCache]);

  return (
    <div className="fixed right-0 top-0 h-full w-96 glass shadow-2xl z-50 transform transition-transform duration-300">
      <div className="p-6 h-full overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">{node.data.label}</h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {loading ? (
          <div className="text-white/60">加载中...</div>
        ) : context ? (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">定义</h3>
              <p className="text-white/80">{context.definition || '暂无定义'}</p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-2">为什么需要</h3>
              <p className="text-white/80">{context.context || '暂无说明'}</p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-2">行动建议</h3>
              <p className="text-white/80 font-mono bg-white/10 p-3 rounded-lg">
                {context.action || '暂无建议'}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-white/60">无法加载上下文</div>
        )}
      </div>
    </div>
  );
}

