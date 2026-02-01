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

      if (posthogKey) {
        posthog.init(posthogKey, {
          api_host: posthogHost,
          person_profiles: 'identified_only', // 或 'always' 如果你想要所有用户都有 profile
          loaded: (posthog) => {
            if (process.env.NODE_ENV === 'development') {
              console.log('✅ PostHog 已初始化');
            }
          },
        });
      } else {
        console.warn('⚠️ PostHOG_KEY 未设置，PostHog 未初始化');
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
