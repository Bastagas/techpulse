const { test, expect } = require('@playwright/test');

test.describe('TechPulse — smoke tests', () => {

    test('Home page — hero + stats + offer cards render', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/TechPulse/);
        await expect(page.getByRole('heading', { level: 1 })).toContainText(/marché de l'emploi tech/i);
        // Stats countup should eventually show a number
        const total = page.locator('[data-countup]').first();
        await expect(total).toBeVisible();
        // At least one offer card
        await expect(page.locator('.compare-checkbox').first()).toBeVisible({ timeout: 10_000 });
    });

    test('Search — keyword filter triggers backend query (no 500)', async ({ page }) => {
        await page.goto('/search.php?keyword=python');
        await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
        // Must not render an error page
        await expect(page.locator('body')).not.toContainText('Fatal error');
        await expect(page.locator('body')).not.toContainText('SQLSTATE');
    });

    test('Simulator — submits profile and shows salary prediction', async ({ page }) => {
        await page.goto('/simulator.php');
        await page.locator('input[list="cities-dl"]').fill('Paris');
        await page.locator('select').filter({ hasText: /—|CDI/ }).first().selectOption({ label: 'CDI' }).catch(() => {});
        // Click a tech pill (first available)
        const firstTech = page.locator('button').filter({ hasText: /\d+/ }).first();
        if (await firstTech.count()) await firstTech.click();
        // Submit
        await page.getByRole('button', { name: /Prédire/i }).click();
        // Result card appears with a gradient number
        await expect(page.locator('.gradient-accent').filter({ hasText: /k€/ }).first()).toBeVisible({ timeout: 8_000 });
    });

    test('Dashboard — calendar heatmap renders', async ({ page }) => {
        await page.goto('/dashboard.php');
        await expect(page.locator('#calendar-heatmap')).toBeVisible();
        // Calendar cells should have been injected by JS
        await expect(page.locator('#calendar-heatmap .cal-cell').first()).toBeVisible({ timeout: 5_000 });
    });

    test('Command palette — ⌘K button opens modal with results', async ({ page }) => {
        await page.goto('/');
        // Click the ⌘K indicator button in the nav (sm+ viewport)
        await page.locator('button[aria-label="Ouvrir le menu rapide"]').click();
        await expect(page.locator('.cmdk-modal')).toBeVisible({ timeout: 3_000 });
        await page.locator('.cmdk-input').fill('dashboard');
        await expect(page.locator('.cmdk-hit').first()).toBeVisible();
    });
});
