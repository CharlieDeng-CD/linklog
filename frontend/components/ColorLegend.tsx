'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';

interface ColorItem {
  color: string;
  label: string;
  description: string;
  bgClass: string;
}

const colorItems: ColorItem[] = [
  {
    color: '蓝色',
    label: 'target',
    description: '目标节点：您要学习的主要目标',
    bgClass: 'bg-blue-500/90',
  },
  {
    color: '绿色',
    label: 'concept',
    description: '核心概念：学习路径中的关键知识点',
    bgClass: 'bg-green-500/90',
  },
  {
    color: '橙色',
    label: 'prerequisite / bridge',
    description: '前置知识 / 桥梁：连接已有知识和新知识的关键节点',
    bgClass: 'bg-orange-500/90',
  },
  {
    color: '紫色',
    label: 'new_concept',
    description: '全新概念：完全陌生的新知识',
    bgClass: 'bg-purple-500/90',
  },
  {
    color: '黄色',
    label: 'review',
    description: '复习节点：需要回顾的基础知识',
    bgClass: 'bg-yellow-500/90',
  },
  {
    color: '白色半透明',
    label: 'known',
    description: '已掌握：您已经了解的基础知识',
    bgClass: 'bg-white/10 border-dashed border-white/40',
  },
];

export default function ColorLegend() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <div className="glass border border-white/20 rounded-lg shadow-lg overflow-hidden backdrop-blur-md">
        {/* 标题栏：可点击展开/折叠 */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-white/5 transition-colors text-white"
        >
          <div className="flex items-center gap-2">
            <Info size={18} className="text-white/80" />
            <span className="text-sm font-semibold">颜色说明</span>
          </div>
          {isExpanded ? (
            <ChevronUp size={18} className="text-white/60" />
          ) : (
            <ChevronDown size={18} className="text-white/60" />
          )}
        </button>

        {/* 内容区域：折叠时隐藏 */}
        {isExpanded && (
          <div className="px-4 pb-4 space-y-3 border-t border-white/10">
            {colorItems.map((item, index) => (
              <div key={index} className="flex items-start gap-3 pt-3">
                {/* 颜色示例 */}
                <div
                  className={`w-6 h-6 rounded-full ${item.bgClass} border border-white/30 flex-shrink-0 mt-0.5`}
                />
                {/* 说明文字 */}
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-white/90 mb-0.5">
                    {item.label}
                  </div>
                  <div className="text-xs text-white/60 leading-relaxed">
                    {item.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

