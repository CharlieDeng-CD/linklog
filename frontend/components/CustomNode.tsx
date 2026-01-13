'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface CustomNodeData {
  label: string;
  category: 'goal' | 'action' | 'prerequisite';
  description?: string;
  expanded?: boolean;
}

function CustomNode({ data }: NodeProps<CustomNodeData>) {
  const categoryStyles = {
    goal: 'bg-blue-500/90 text-white glow-goal',
    action: 'bg-green-500/90 text-white glow-action',
    prerequisite: 'bg-orange-500/90 text-white glow-prerequisite',
  };

  return (
    <div className={`px-6 py-3 rounded-full ${categoryStyles[data.category]} backdrop-blur-sm border border-white/30 shadow-lg min-w-[120px] text-center cursor-pointer`}>
      <Handle type="target" position={Position.Top} />
      <div className="font-semibold text-sm">{data.label}</div>
      {data.expanded && (
        <div className="text-xs mt-1 opacity-75">已展开 (双击收起)</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default memo(CustomNode);

