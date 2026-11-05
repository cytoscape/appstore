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

  // Cytoscape Desktop's App Manager shows only apps with a compatible release in this
  // feed, so service and web apps stay listed with no releases, as they were before #155
  test("Cytoscape Desktop's app feed carries only desktop releases", async ({ request }) => {
    const apps = await (await request.get('/backend/all_apps')).json()
    const releases = Object.fromEntries(apps.map((app) => [app.fullname, app.releases]))
    expect(releases['IT Web']).toEqual([])
    expect(releases['IT Service']).toEqual([])
    expect(releases['IT Desktop'].map((release) => release.release_download_url)).toEqual(['/download/itdesktop/1.0'])
    expect(releases['IT Multi'].map((release) => release.release_download_url)).toEqual(['/download/itmulti/1.0'])
  })

  test("a platform's listing describes each app as that platform's page does", async ({ page }) => {
    const description = (name: string) => tile(page, name).first().locator('.description').first()
    await page.goto('/apps/platform/web/')
    await expect(description('IT Multi')).toHaveText('IT Multi in the browser')
    for (const url of ['/apps/platform/desktop/', '/apps/all']) {
      await page.goto(url)
      await expect(description('IT Multi')).toHaveText('IT Multi, seeded for the integration tests')
    }
  })

  test('category pages and counts include categories on any platform', async ({ page }) => {
    await page.goto('/apps/with_tag/itwebonly')
    await expect(tile(page, 'IT Multi').first()).toBeVisible()
    await page.goto('/apps/with_tag/itdesktop')
    await expect(tile(page, 'IT Multi').first()).toBeVisible()

    // on two apps, and on IT Multi only through its web content; the side menu lists categories of 3 or more
    await page.goto('/apps/all')
    const shared = page.locator('#cy-tag-list li', { hasText: 'it-shared-category' })
    await expect(shared.locator('.count')).toHaveText('(3)')
    await shared.getByRole('link').click()
    for (const name of ['IT Desktop', 'IT Web', 'IT Multi']) {
      await expect(tile(page, name).first()).toBeVisible()
    }
  })

  test('search finds an app by words only in its web content', async ({ page }) => {
    await page.goto('/search?q=browser')
    await expect(tile(page, 'IT Multi').first()).toBeVisible()
  })

  test("Cytoscape Desktop's feed gives the app's desktop content", async ({ request }) => {
    const feed = await (await request.get('/backend/all_apps')).json()
    const multi = feed.find((app) => app.fullname === 'IT Multi')
    expect(multi.description).toBe('IT Multi, seeded for the integration tests')
    expect(multi.tags).toEqual(['it-desktop'])
  })
})
