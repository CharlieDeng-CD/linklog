'use client';

import { useState } from 'react';
import InputScreen from '@/components/InputScreen';
import GraphCanvas from '@/components/GraphCanvas';

export default function Home() {
  const [goal, setGoal] = useState<string | null>(null);
  const [context, setContext] = useState<string | undefined>(undefined);
  const [initialNodes, setInitialNodes] = useState<any[]>([]);
  const [initialEdges, setInitialEdges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleGoalSubmit = async (userGoal: string, userContext?: string) => {
    setGoal(userGoal);
    setContext(userContext);
    setLoading(true);
    
    // 调用后端 v3 API 生成初始图谱
    try {
      const requestBody: { goal: string; context?: string } = { goal: userGoal };
      if (userContext) {
        requestBody.context = userContext;
      }
      
      const response = await fetch('/api/v3/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API 错误:', response.status, errorText);
        alert(`生成图谱失败: ${response.status} ${errorText.substring(0, 100)}`);
        setLoading(false);
        return;
      }
      
      // 检查 Content-Type
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('响应不是 JSON:', contentType, text.substring(0, 200));
        alert('服务器返回了非 JSON 格式的响应');
        setLoading(false);
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
    } finally {
      setLoading(false);
    }
  };

  if (!goal || initialNodes.length === 0) {
    return <InputScreen onSubmit={handleGoalSubmit} />;
  }

  return (
    <GraphCanvas
      originalGoal={goal}
      userContext={context}
      initialNodes={initialNodes}
      initialEdges={initialEdges}
    />
  );
}

