'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import posthog from 'posthog-js';

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // 只在客户端初始化 PostHog
    if (typeof window !== 'undefined') {
      const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
      const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com';

      // 调试信息：显示环境变量状态（生产环境也显示）
      console.log('[PostHog] 初始化检查:', {
        hasKey: !!posthogKey,
        keyPrefix: posthogKey ? posthogKey.substring(0, 10) + '...' : 'undefined',
        host: posthogHost,
        nodeEnv: process.env.NODE_ENV,
      });

      if (posthogKey) {
        try {
          posthog.init(posthogKey, {
            api_host: posthogHost,
            person_profiles: 'identified_only',
            loaded: (posthog) => {
              console.log('✅ [PostHog] 已成功初始化');
            },
          });
          console.log('✅ [PostHog] 初始化请求已发送');
        } catch (error) {
          console.error('❌ [PostHog] 初始化失败:', error);
        }
      } else {
        console.warn('⚠️ [PostHog] NEXT_PUBLIC_POSTHOG_KEY 未设置，PostHog 未初始化');
        console.warn('⚠️ [PostHog] 这通常意味着环境变量在构建时没有被正确传递');
      }
    }
  }, []);

  useEffect(() => {
    // 页面浏览追踪
    if (pathname && typeof window !== 'undefined' && posthog.__loaded) {
      let url = window.origin + pathname;
      if (searchParams && searchParams.toString()) {
        url = url + `?${searchParams.toString()}`;
      }
      posthog.capture('$pageview', {
        $current_url: url,
      });
    }
  }, [pathname, searchParams]);

  return <>{children}</>;
}
