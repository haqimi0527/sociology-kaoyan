import { test as base } from '@playwright/test';

// DeepSeek API mock 响应
const MOCK_AI_RESPONSE = {
  choices: [{
    message: {
      content: JSON.stringify({
        totalScore: 85,
        maxScore: 100,
        dimensions: [
          { name: '概念准确性', score: 28, max: 30, comment: '概念表述基本准确' },
          { name: '逻辑完整性', score: 25, max: 30, comment: '论证链条完整' },
          { name: '理论深度', score: 22, max: 25, comment: '有适当理论引用' },
          { name: '表达规范', score: 10, max: 15, comment: '语言通顺' },
        ],
        overallComment: '整体回答质量良好，概念掌握扎实。',
      })
    }
  }]
};

export const test = base.extend({
  page: async ({ page }, use) => {
    const consoleErrors: string[] = [];

    // 拦截 DeepSeek API，返回 mock 数据
    await page.route('**/api.deepseek.com/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_AI_RESPONSE),
      });
    });

    // 监听 console error
    const STOP_LIST = ['favicon.ico', 'ERR_CONNECTION_REFUSED'];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!STOP_LIST.some((p) => text.includes(p))) {
          consoleErrors.push(text);
        }
      }
    });

    page.on('pageerror', (err) => {
      consoleErrors.push(`[未捕获异常] ${err.message}`);
    });

    await use(page);

    if (consoleErrors.length > 0) {
      console.error(`⚠️ ${consoleErrors.length} 个 console error:`);
      consoleErrors.forEach((e) => console.error(`  ${e}`));
    }
  },
});

export { expect } from '@playwright/test';
