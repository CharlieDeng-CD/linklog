'use client';

import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { ChevronDown, BookOpen } from 'lucide-react';

interface CustomNodeData {
  label: string;
  category: 'goal' | 'action' | 'prerequisite' | 'target' | 'bridge' | 'new_concept' | 'review' | 'concept' | 'known';
  description?: string;
  level?: number; // 节点层级：0=目标, 1=核心支柱, 2=基础依赖, 3=已知基石
  expanded?: boolean;
  onExpand?: () => void;
  onShowDetail?: () => void;
}

function CustomNode({ data }: NodeProps<CustomNodeData>) {
  const [isHovered, setIsHovered] = useState(false);

  const categoryStyles = {
    goal: 'bg-blue-500/90 text-white glow-goal',
    action: 'bg-green-500/90 text-white glow-action',
    prerequisite: 'bg-orange-500/90 text-white glow-prerequisite',
    target: 'bg-blue-500/90 text-white glow-goal',
    bridge: 'bg-orange-500/90 text-white border-orange-400/50',
    new_concept: 'bg-purple-500/90 text-white',
    review: 'bg-yellow-500/90 text-white border-yellow-400/50',
    concept: 'bg-green-500/90 text-white glow-action',
    known: 'bg-white/10 text-white/80 border-dashed border-white/40 backdrop-blur-md',
  };

  const handleExpandClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (data.onExpand) {
      data.onExpand();
    }
  };

  const handleDetailClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (data.onShowDetail) {
      data.onShowDetail();
    }
  };

  return (
    <div 
      className={`relative px-6 py-3 rounded-full ${categoryStyles[data.category as keyof typeof categoryStyles] || categoryStyles.concept} backdrop-blur-sm border border-white/30 shadow-lg min-w-[120px] text-center cursor-pointer transition-all`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Handle type="target" position={Position.Top} />
      <div className="font-semibold text-sm">{data.label}</div>
      {data.expanded && (
        <div className="text-xs mt-1 opacity-75">已展开</div>
      )}
      <Handle type="source" position={Position.Bottom} />
      
      {/* 按钮容器：右下角，悬停时显示 */}
      <div 
        className={`absolute bottom-0.5 right-0.5 flex gap-0.5 transition-opacity duration-200 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 展开按钮：Level 0（目标）和 Level 2（最底层）节点不显示，Level 3（已知基石）可以展开 */}
        {data.level !== 0 && data.level !== 2 && (
          <button
            onClick={handleExpandClick}
            className="glass bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/40 rounded-full p-0.5 shadow-md hover:shadow-lg transition-all group"
            title={data.expanded ? "收起" : "展开"}
          >
            <ChevronDown 
              size={10} 
              className={`text-white transition-transform duration-200 ${
                data.expanded ? 'rotate-180' : ''
              }`}
            />
          </button>
        )}
        
        {/* 内容说明按钮 */}
        <button
          onClick={handleDetailClick}
          className="glass bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/40 rounded-full p-0.5 shadow-md hover:shadow-lg transition-all group"
          title="查看说明"
        >
          <BookOpen size={10} className="text-white" />
        </button>
      </div>
    </div>
  );
}

export default memo(CustomNode);

