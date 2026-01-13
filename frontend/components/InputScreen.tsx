'use client';

import { useState } from 'react';

interface InputScreenProps {
  onSubmit: (goal: string) => void;
}

export default function InputScreen({ onSubmit }: InputScreenProps) {
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    
    setLoading(true);
    await onSubmit(goal.trim());
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
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="例如：开发个人博客、掌握 React、学习机器学习..."
            className="w-full px-6 py-4 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 text-lg"
            disabled={loading}
          />
          
          <button
            type="submit"
            disabled={loading || !goal.trim()}
            className="w-full py-4 rounded-xl bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 text-white font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '生成中...' : '开始探索'}
          </button>
        </form>
      </div>
    </div>
  );
}

