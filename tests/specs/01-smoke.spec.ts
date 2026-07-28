import { test, expect } from '../fixtures';

test.describe('冒烟测试', () => {

  test('页面标题正确', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/社会学考研/);
  });

  test('所有 6 个面板 DOM 存在', async ({ page }) => {
    await page.goto('/');
    const panels = ['panel-dashboard', 'panel-politics', 'panel-english',
                    'panel-theory', 'panel-methods', 'panel-settings'];
    for (const id of panels) {
      await expect(page.locator(`#${id}`)).toBeAttached();
    }
  });

  test('侧边栏切换面板', async ({ page }) => {
    await page.goto('/');
    await page.click('.nav-item[data-panel="politics"]');
    await expect(page.locator('#panel-politics')).toBeVisible();
    await expect(page.locator('#panel-dashboard')).toBeHidden();

    await page.click('.nav-item[data-panel="theory"]');
    await expect(page.locator('#panel-theory')).toBeVisible();
  });

  test('暗色模式不崩溃', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/');
    await expect(page.locator('#panel-dashboard')).toBeVisible();
  });

  test('所有数据 fetch 返回 200', async ({ page }) => {
    const results: { url: string; status: number }[] = [];
    page.on('response', (r) => {
      if (r.url().includes('data/') && r.url().endsWith('.json')) {
        results.push({ url: r.url(), status: r.status() });
      }
    });
    await page.goto('/', { waitUntil: 'networkidle' });
    const failed = results.filter((r) => r.status !== 200);
    expect(failed).toEqual([]);
  });

  test('无 console error', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
  });
});
