'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Lightbulb, Target, Code, BookOpen, Send, MessageCircle } from 'lucide-react';
import { Node } from 'reactflow';

interface V3ContextSidebarProps {
  node: Node;
  originalGoal: string;
  userContext?: string;  // v3: 用户背景知识
  contextCache: Map<string, any>;
  setContextCache: (cache: Map<string, any>) => void;
  onClose: () => void;
}

interface NodeDetailData {
  title: string;
  definition: string;
  analogy: string | null;
  importance: string;
  action_item: string;
  resource_keywords: string[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function V3ContextSidebar({
  node,
  originalGoal,
  userContext,
  contextCache,
  setContextCache,
  onClose,
}: V3ContextSidebarProps) {
  const [detail, setDetail] = useState<NodeDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 先检查缓存
    const cachedDetail = contextCache.get(node.id);
    if (cachedDetail) {
      // 使用缓存，立即显示
      setDetail(cachedDetail);
      setLoading(false);
      return;
    }

    // 缓存不存在，调用 API（带重试机制）
    const fetchDetail = async (retryCount = 0) => {
      const MAX_RETRIES = 3;
      const RETRY_DELAY = 1000; // 1秒
      
      setLoading(true);
      try {
        const response = await fetch('/api/v3/node-detail', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            goal: originalGoal,
            context: userContext || null,
            node_label: node.data.label,
            node_id: node.id,
          }),
        });

        if (!response.ok) {
          // 如果是 500 错误且还有重试次数，则重试
          if (response.status === 500 && retryCount < MAX_RETRIES) {
            console.warn(`API 返回 500 错误，${RETRY_DELAY}ms 后重试 (${retryCount + 1}/${MAX_RETRIES})...`);
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)));
            return fetchDetail(retryCount + 1);
          }
          
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
          setDetail(result.data);
          // 保存到缓存
          const newCache = new Map(contextCache);
          newCache.set(node.id, result.data);
          setContextCache(newCache);
        } else {
          // 如果返回 success=false 且还有重试次数，则重试
          if (retryCount < MAX_RETRIES) {
            console.warn(`API 返回失败，${RETRY_DELAY}ms 后重试 (${retryCount + 1}/${MAX_RETRIES})...`);
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)));
            return fetchDetail(retryCount + 1);
          }
        }
      } catch (error) {
        console.error('获取节点详情失败:', error);
        
        // 如果是网络错误或超时，且还有重试次数，则重试
        if (retryCount < MAX_RETRIES && (
          error instanceof TypeError || // 网络错误
          (error instanceof Error && error.message.includes('fetch'))
        )) {
          console.warn(`网络错误，${RETRY_DELAY}ms 后重试 (${retryCount + 1}/${MAX_RETRIES})...`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)));
          return fetchDetail(retryCount + 1);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [node, originalGoal, userContext, contextCache, setContextCache]);

  // 当节点变化时，清空聊天记录
  useEffect(() => {
    setChatMessages([]);
    setChatInput('');
  }, [node.id]);

  // 发送聊天消息
  const handleSendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await fetch('/api/v3/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          goal: originalGoal,
          context: userContext || null,
          node_label: node.data.label,
          node_id: node.id,
          question: userMessage,
          conversation_history: chatMessages,
        }),
      });

      if (!response.ok) {
        throw new Error(`API 错误 ${response.status}`);
      }

      const result = await response.json();
      if (result.success) {
        setChatMessages(prev => [...prev, { role: 'assistant', content: result.data.answer }]);
      } else {
        throw new Error('API 返回失败');
      }
    } catch (error) {
      console.error('发送聊天消息失败:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，发送消息时出现错误，请稍后重试。' 
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  // 检查内容是否超出可视区域
  const [showFade, setShowFade] = useState(false);
  useEffect(() => {
    const checkOverflow = () => {
      if (contentRef.current && chatContainerRef.current) {
        const contentBottom = contentRef.current.scrollHeight;
        const containerHeight = contentRef.current.clientHeight;
        setShowFade(contentBottom > containerHeight);
      }
    };
    
    checkOverflow();
    const resizeObserver = new ResizeObserver(checkOverflow);
    if (contentRef.current) {
      resizeObserver.observe(contentRef.current);
    }
    
    return () => resizeObserver.disconnect();
  }, [detail, chatMessages]);

  return (
    <div className="fixed right-0 top-[60px] h-[calc(100vh-60px)] w-[420px] glass shadow-2xl z-50 transform transition-transform duration-300 flex flex-col">
      {/* 头部 */}
      <div className="flex justify-between items-center p-6 border-b border-white/10 flex-shrink-0">
        <h2 className="text-2xl font-bold text-white">{node.data.label}</h2>
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
        >
          <X size={24} />
        </button>
      </div>

      {/* 内容区域：可滚动，带渐隐效果 */}
      <div className="flex-1 overflow-hidden relative">
        <div 
          ref={contentRef}
          className="h-full overflow-y-auto px-6 py-6"
        >
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-white/60">加载中...</div>
            </div>
          ) : detail ? (
            <div className="space-y-6 pb-6">
              {/* 定义 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen size={18} className="text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">定义</h3>
                </div>
                <p className="text-white/90 leading-relaxed">{detail.definition}</p>
              </div>

              {/* 类比（如果有） */}
              {detail.analogy && (
                <div className="bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-lg p-4 border border-purple-400/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb size={18} className="text-yellow-400" />
                    <h3 className="text-lg font-semibold text-white">
                      {userContext ? '类比理解' : '生活类比'}
                    </h3>
                  </div>
                  <p className="text-white/90 leading-relaxed italic">
                    "{detail.analogy}"
                  </p>
                  {userContext && (
                    <p className="text-white/60 text-xs mt-2">
                      基于你的背景知识：{userContext}
                    </p>
                  )}
                </div>
              )}

              {/* 重要性 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <Target size={18} className="text-orange-400" />
                  <h3 className="text-lg font-semibold text-white">为什么重要</h3>
                </div>
                <p className="text-white/90 leading-relaxed">{detail.importance}</p>
              </div>

              {/* 行动建议 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <Code size={18} className="text-green-400" />
                  <h3 className="text-lg font-semibold text-white">行动建议</h3>
                </div>
                <div className="bg-black/30 rounded-lg p-3 border border-white/10">
                  <pre className="text-white/90 text-sm font-mono whitespace-pre-wrap break-words">
                    {detail.action_item}
                  </pre>
                </div>
              </div>

              {/* 资源关键词（如果有） */}
              {detail.resource_keywords && detail.resource_keywords.length > 0 && (
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h3 className="text-sm font-semibold text-white/80 mb-2">相关关键词</h3>
                  <div className="flex flex-wrap gap-2">
                    {detail.resource_keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-white/10 rounded-full text-white/70 text-xs border border-white/20"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-white/60 text-center py-12">无法加载节点详情</div>
          )}
        </div>
        
        {/* 渐隐遮罩：当内容超出时显示 */}
        {showFade && (
          <div className="absolute bottom-0 left-0 right-0 h-20 pointer-events-none">
            {/* 背景渐变层 */}
            <div className="absolute inset-0 bg-gradient-to-t from-white/10 via-white/5 to-transparent" />
            {/* 磨砂效果渐变层：从强到弱 */}
            <div 
              className="absolute inset-0 backdrop-blur-sm"
              style={{
                maskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0) 100%)',
                WebkitMaskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0) 100%)',
              }}
            />
          </div>
        )}
      </div>

      {/* Chatbox：固定在底部，在上层 */}
      <div 
        ref={chatContainerRef}
        className="border-t border-white/10 glass flex-shrink-0 relative z-10"
      >
        {/* 聊天消息列表 */}
        {chatMessages.length > 0 && (
          <div className="max-h-[200px] overflow-y-auto px-4 py-3 space-y-3">
            {chatMessages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 ${
                    msg.role === 'user'
                      ? 'bg-blue-500/30 text-white border border-blue-400/30'
                      : 'bg-white/10 text-white/90 border border-white/20'
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {msg.content}
                  </p>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-white/10 text-white/60 rounded-lg px-3 py-2 border border-white/20">
                  <p className="text-sm">思考中...</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 输入框 */}
        <div className="px-4 pb-4 pt-3">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-white/60 mb-2">
              <MessageCircle size={16} />
              <span className="text-xs">提问</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              id="chat-input"
              name="chat-input"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="输入你的问题..."
              className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50"
              disabled={chatLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || chatLoading}
              className="bg-gradient-to-r from-blue-500/80 to-purple-500/80 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg px-4 py-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
