import { expect, test } from './fixtures'

// Platform pages list an app under every platform it is on, and 2.x-only
// plugins get a page of their own (#155).
test.describe('Browsing by platform', () => {
  const tile = (page, name: string) => page.locator('.app_button', { hasText: name })

  test('an app on three platforms is listed on all three platform pages', async ({ page }) => {
    for (const platform of ['desktop', 'web', 'service']) {
      await page.goto(`/apps/platform/${platform}/`)
      await expect(tile(page, 'IT Multi').first()).toBeVisible()
      await expect(tile(page, 'IT Legacy')).toHaveCount(0)
    }
  })

  test('2.x plugins are listed on their own page, reached from the nav panel', async ({ page }) => {
    await page.goto('/apps/all')
    await page.getByRole('link', { name: 'Cytoscape 2.x Plugins' }).click()
    await expect(page).toHaveURL(/\/apps\/cy2x_plugins$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Cytoscape 2.x Plugins' })).toBeVisible()
    await expect(tile(page, 'IT Legacy').first()).toBeVisible()
    await expect(tile(page, 'IT Multi')).toHaveCount(0)
  })

  test('an unknown platform is not found', async ({ request }) => {
    expect((await request.get('/apps/platform/bogus/')).status()).toBe(404)
  })

  test("Cytoscape Desktop's app feed lists only apps with desktop releases", async ({ request }) => {
    const apps = await (await request.get('/backend/all_apps')).json()
    const names = apps.map((app) => app.fullname)
    expect(names).toEqual(expect.arrayContaining(['IT Desktop', 'IT Multi']))
    expect(names).not.toContain('IT Web')
    expect(names).not.toContain('IT Service')
    const multi = apps.find((app) => app.fullname === 'IT Multi')
    expect(multi.releases.map((release) => release.version)).toEqual(['1.0'])
  })
})
