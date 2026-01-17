'use client';

import { useState } from 'react';
import { Sparkles } from 'lucide-react';

interface InputScreenProps {
  onSubmit: (goal: string, context?: string) => void;
}

export default function InputScreen({ onSubmit }: InputScreenProps) {
  const [goal, setGoal] = useState('');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    
    setLoading(true);
    // 如果 context 为空，传递 undefined（触发 Mode A）
    // 如果 context 有值，传递它（触发 Mode B）
    await onSubmit(goal.trim(), context.trim() || undefined);
    setLoading(false);
  };

  return (
    <div className="fluid-gradient min-h-screen flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-2xl p-12 max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-white mb-2 text-center">
          Map Your Unknowns
        </h1>
        <p className="text-white/80 text-center mb-8">
          输入你的学习目标，让我们帮你识别前置知识
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 主输入框：学习目标 */}
          <input
            type="text"
            id="goal-input"
            name="goal"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="What do you want to learn? (例如：开发个人博客、掌握 React、学习机器学习...)"
            className="w-full px-6 py-4 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 text-lg"
            disabled={loading}
          />
          
          {/* "I have experience" Toggle */}
          <div className="flex items-center justify-center">
            <button
              type="button"
              onClick={() => setShowContext(!showContext)}
              className="flex items-center gap-2 text-white/70 hover:text-white transition-colors text-sm"
              disabled={loading}
            >
              <Sparkles size={16} />
              <span>{showContext ? '隐藏' : '我有相关经验'}</span>
            </button>
          </div>
          
          {/* 可选的 Context 输入框 */}
          {showContext && (
            <div className="animate-in slide-in-from-top-2 duration-300">
              <input
                type="text"
                id="context-input"
                name="context"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="What do you already know? (例如：我熟悉 Python、我懂 HTML/CSS、我有 Java 基础...)"
                className="w-full px-6 py-4 rounded-xl bg-white/15 backdrop-blur-sm border border-white/25 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/40 text-base"
                disabled={loading}
              />
              <p className="text-white/50 text-xs mt-2 px-2">
                告诉我们你的背景知识，我们会为你定制更精准的学习路径
              </p>
            </div>
          )}
          
          {/* Generate Map 按钮 */}
          <button
            type="submit"
            disabled={loading || !goal.trim()}
            className="w-full py-4 rounded-xl bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 text-white font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
          >
            {loading ? '生成中...' : 'Generate Map'}
          </button>
        </form>
      </div>
    </div>
  );
}

