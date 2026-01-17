'use client';

import { memo } from 'react';

interface FoundationBoxProps {
  data: {
    label: string;
  };
  style?: React.CSSProperties;
}

function FoundationBox({ data, style }: FoundationBoxProps) {
  return (
    <div 
      className="glass border-2 border-dashed border-white/20 rounded-3xl pointer-events-none flex flex-col items-center pt-4"
      style={{
        width: style?.width,
        height: style?.height,
        backgroundColor: 'rgba(255, 255, 255, 0.03)',
      }}
    >
      <div className="bg-white/10 px-4 py-1 rounded-full border border-white/20 backdrop-blur-md">
        <span className="text-white/60 text-xs font-bold tracking-widest uppercase">
          {data.label}
        </span>
      </div>
    </div>
  );
}

export default memo(FoundationBox);

