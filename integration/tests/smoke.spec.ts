import { expect, test } from './fixtures'

test.describe('App Store container', () => {
  test('home and all-apps pages load with the seeded apps and their stylesheet', async ({ page, request }) => {
    const home = await page.goto('/')
    expect(home?.status()).toBe(200)

    await page.goto('/apps/all')
    for (const name of ['IT Desktop', 'IT Web', 'IT Service']) {
      await expect(page.locator('.app_button', { hasText: name }).first()).toBeVisible()
    }

    const css = await page.locator('link[rel="stylesheet"][href*="/static/"]').first().getAttribute('href')
    expect((await request.get(css!)).status()).toBe(200)
  })

  test('each single-platform app page shows its own install panel', async ({ page }) => {
    await page.goto('/apps/itdesktop')
    await expect(page.getByRole('heading', { name: 'IT Desktop' })).toBeVisible()
    await expect(page.locator('h6', { hasText: 'CYTOSCAPE 3' })).toBeVisible()

    await page.goto('/apps/itweb')
    await expect(page.getByRole('link', { name: 'Install in Cytoscape Web' })).toBeVisible()

    await page.goto('/apps/itservice')
    await expect(page.getByRole('link', { name: 'Open in Cytoscape Web' })).toBeVisible()
  })

  test('an editor of the app gets the editor menu', async ({ asEditor }) => {
    await asEditor.goto('/apps/itdesktop')
    await expect(asEditor.getByText('Editor Actions')).toBeVisible()
  })

  test('a signed-in non-editor gets no editor menu', async ({ asOther }) => {
    await asOther.goto('/apps/itdesktop')
    await expect(asOther.getByRole('heading', { name: 'IT Desktop' })).toBeVisible()
    await expect(asOther.getByText('Editor Actions')).toHaveCount(0)
  })

  test('only staff reach the pending apps queue', async ({ asAdmin, request }) => {
    await asAdmin.goto('/submit/pending')
    await expect(asAdmin.getByRole('heading', { name: 'Pending Apps' })).toBeVisible()

    const anonymous = await request.get('/submit/pending', { maxRedirects: 0 })
    expect(anonymous.status()).toBe(302)
    expect(anonymous.headers()['location']).toContain('/login')
  })

  test('footer shows the running version', async ({ page, asAdmin }) => {
    // the image leaves out .git (.dockerignore), so git can't tell the version: 'develop'
    const check = async (p, url: string) => {
      await p.goto(url)
      const footer = p.locator('footer')
      const version = footer.locator('#cy-app-version')
      await expect(version).toBeVisible()
      await expect(version).toHaveText(/^Version: \S+$/)
      await expect(version).toHaveText('Version: develop')
      const text = await footer.innerText()
      expect(text.indexOf('Contact Us')).toBeLessThan(text.indexOf('Version: develop'))
      expect(text.indexOf('Version: develop')).toBeLessThan(text.indexOf('Wall of Apps'))
    }
    for (const url of ['/', '/apps/itmulti', '/apps/cy2x_plugins']) {
      await check(page, url)
    }
    await check(asAdmin, '/submit/pending')
  })
})
