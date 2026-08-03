import { test, expect } from '../fixtures';

// 命名进入（关闭欢迎弹窗，否则 fixed 遮罩会拦截点击）
async function enterWorld(page: any) {
  await page.goto('/');
  await page.waitForTimeout(1500);
  const welcomeOpen = await page.locator('#welcome.open').count();
  if (welcomeOpen > 0) {
    await page.fill('#pname', '测试玩家');
    await page.click('#btn-enter');
    await page.waitForTimeout(300);
  }
}

test.describe('冒烟测试（RPG 骨架）', () => {

  test('页面标题正确', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/社会学考研|知识大陆/);
  });

  test('核心结构：hero-bar + 世界地图 + 7 面板', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.hero-bar')).toBeAttached();
    const panels = ['panel-dashboard', 'panel-politics', 'panel-english',
                    'panel-theory', 'panel-methods', 'panel-mock-exam', 'panel-settings'];
    for (const id of panels) {
      await expect(page.locator(`#${id}`)).toBeAttached();
    }
  });

  test('世界地图渲染 5 领地卡片', async ({ page }) => {
    await enterWorld(page);
    const cards = await page.locator('#mapZones .zone').count();
    expect(cards).toBe(5);
  });

  test('无侧边栏（老导航已移除）', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.sidebar')).toHaveCount(0);
  });

  test('点击知识圣殿进入下钻视图', async ({ page }) => {
    await enterWorld(page);
    await page.evaluate(() => document.querySelector('#mapZones .zone.thr')!.click());
    await expect(page.locator('#panel-theory')).toBeVisible();
    await expect(page.locator('#thrBrowse .browse-item').first()).toBeVisible({ timeout: 5000 });
  });

  test('主城下钻：点击主城卡片显示概论', async ({ page }) => {
    await enterWorld(page);
    await page.evaluate(() => document.querySelector('#mapZones .zone.dash')!.click());
    await expect(page.locator('#dashBrowse .browse-item').first()).toBeVisible({ timeout: 5000 });
  });

  test('政治领地下钻：模块→题型→题', async ({ page }) => {
    await enterWorld(page);
    await page.evaluate(() => document.querySelector('#mapZones .zone.pol')!.click());
    await expect(page.locator('#polBrowse .browse-item').first()).toBeVisible({ timeout: 5000 });
    await page.locator('#polBrowse .browse-item').first().click();
    await page.locator('#polBrowse .browse-item').first().click();
    await expect(page.locator('#polBrowse .skill-card').first()).toBeVisible({ timeout: 5000 });
  });

  test('概念搜索（原功能保留）', async ({ page }) => {
    await enterWorld(page);
    await page.evaluate(() => document.querySelector('#mapZones .zone.thr')!.click());
    await page.locator('#thrTabs [data-sub="thr-concept"]').click();
    await page.fill('#conceptSearchShell', '涂尔干');
    await page.waitForTimeout(500);
    const count = await page.locator('#thrResultList > *').count();
    expect(count).toBeGreaterThan(0);
  });

  test('窄屏无横向溢出', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await enterWorld(page);
    await page.evaluate(() => document.querySelector('#mapZones .zone.thr')!.click());
    await page.waitForTimeout(600);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
    expect(overflow).toBe(false);
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
});
