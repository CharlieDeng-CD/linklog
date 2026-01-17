'use client';

import { useState } from 'react';
import InputScreen from '@/components/InputScreen';
import GraphCanvas from '@/components/GraphCanvas';

export default function Home() {
  const [goal, setGoal] = useState<string | null>(null);
  const [initialNodes, setInitialNodes] = useState<any[]>([]);
  const [initialEdges, setInitialEdges] = useState<any[]>([]);

  const handleGoalSubmit = async (userGoal: string) => {
    setGoal(userGoal);
    
    // 调用后端 API 生成初始图谱
    try {
      const response = await fetch('/api/v2/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ goal: userGoal }),
      });
      
      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API 错误:', response.status, errorText);
        alert(`生成图谱失败: ${response.status} ${errorText.substring(0, 100)}`);
        return;
      }
      
      // 检查 Content-Type
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('响应不是 JSON:', contentType, text.substring(0, 200));
        alert('服务器返回了非 JSON 格式的响应');
        return;
      }
      
      const result = await response.json();
      
      if (result.success) {
        setInitialNodes(result.data.nodes || []);
        setInitialEdges(result.data.edges || []);
      } else {
        alert('生成图谱失败: ' + (result.error || '未知错误'));
      }
    } catch (error) {
      console.error('生成初始图谱失败:', error);
      if (error instanceof SyntaxError) {
        alert('JSON 解析错误，请检查后端服务是否正常运行');
      } else {
        alert('生成图谱失败: ' + (error instanceof Error ? error.message : '未知错误'));
      }
    }
  };

  if (!goal || initialNodes.length === 0) {
    return <InputScreen onSubmit={handleGoalSubmit} />;
  }

  return (
    <GraphCanvas
      originalGoal={goal}
      initialNodes={initialNodes}
      initialEdges={initialEdges}
    />
  );
}

