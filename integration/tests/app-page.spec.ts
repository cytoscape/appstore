import { expect, test } from './fixtures'

// One page per app, showing every platform it is on (#155).
test.describe('App page', () => {
  const panelOrder = (page) =>
    page.locator('.cy-app-platform-panel').evaluateAll((panels) => panels.map((panel) => panel.dataset.platform))

  test('an app on three platforms shows a chip and a panel for each, without script errors', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (error) => errors.push(error.message))
    await page.goto('/apps/itmulti')

    await expect(page.locator('.cy-app-platform-chip')).toHaveText(['Cytoscape Desktop', 'Cytoscape Web', 'Service'])
    expect(await panelOrder(page)).toEqual(['desktop', 'web', 'service'])
    await expect(page.locator('#cy-app-panel-desktop').getByRole('heading', { name: 'CYTOSCAPE 3' })).toBeVisible()
    await expect(page.locator('#cy-app-panel-web').getByRole('link', { name: 'Install in Cytoscape Web' })).toBeVisible()
    await expect(page.locator('#cy-app-panel-service').getByRole('link', { name: 'Open in Cytoscape Web' })).toBeVisible()
    expect(errors).toEqual([])
  })

  test("a platform chip puts that platform's panel first", async ({ page }) => {
    await page.goto('/apps/itmulti')
    await page.locator('.cy-app-platform-chip', { hasText: 'Service' }).click()
    await expect(page).toHaveURL(/\?platform=service$/)
    expect(await panelOrder(page)).toEqual(['service', 'desktop', 'web'])
    await expect(page.locator('.cy-app-platform-chip.label-info')).toHaveText('Service')
  })

  test('release history switches between platforms', async ({ page }) => {
    await page.goto('/apps/itmulti')
    await page.getByRole('link', { name: 'Release History' }).click()
    await expect(page.locator('#cy-app-releases-desktop')).toBeVisible()
    await expect(page.locator('#cy-app-releases-web')).toBeHidden()

    await page.locator('#cy-app-release-platforms').getByRole('link', { name: 'Cytoscape Web' }).click()
    await expect(page.locator('#cy-app-releases-web')).toBeVisible()
    await expect(page.locator('#cy-app-releases-desktop')).toBeHidden()
    await expect(page.locator('#cy-app-releases-web .cy-app-url-copy input')).toHaveValue(/\/web\/itmulti\/1\.0\/manifest\.json$/)
  })

  test('editors can submit a release for any platform', async ({ asEditor }) => {
    await asEditor.goto('/apps/itmulti')
    await asEditor.getByText('Editor Actions').click()
    for (const name of ['Submit a desktop release', 'Submit a Cytoscape Web bundle', 'Submit a service release']) {
      await expect(asEditor.getByRole('link', { name })).toBeVisible()
    }
    await asEditor.getByRole('link', { name: 'Submit a service release' }).click()
    await expect(asEditor).toHaveURL(/\/submit\/submit_service_app\?expect_app_name=IT(\+|%20)Multi$/)
  })

  test('non-editors get no submit links', async ({ asOther }) => {
    await asOther.goto('/apps/itmulti')
    await expect(asOther.getByRole('link', { name: /^Submit a / })).toHaveCount(0)
  })

  test('single-platform apps show one chip and one panel', async ({ page }) => {
    for (const [name, platform] of [['itweb', 'web'], ['itservice', 'service']]) {
      await page.goto(`/apps/${name}`)
      expect(await panelOrder(page)).toEqual([platform])
      await expect(page.locator('.cy-app-platform-chip')).toHaveCount(1)
    }
  })

  test('a 2.x plugin shows its Cytoscape 2 panel and no platforms', async ({ page }) => {
    await page.goto('/apps/itlegacy')
    await expect(page.locator('#cy-app-panel-cy2x').getByRole('heading', { name: 'CYTOSCAPE 2' })).toBeVisible()
    expect(await panelOrder(page)).toEqual([])
    await expect(page.locator('#cy-app-platforms')).toHaveCount(0)
  })

  test('install buttons keep their spacing and inline label', async ({ page }) => {
    const styles = (selector: string) =>
      page.locator(selector).evaluate((button) => {
        const own = getComputedStyle(button)
        return {
          marginPx: parseFloat(own.marginBottom),
          marginEm: parseFloat(own.marginBottom) / parseFloat(own.fontSize),
          labelDisplay: getComputedStyle(button.querySelector('h4')!).display,
        }
      })
    await page.goto('/apps/itmulti')
    const desktop = await styles('#cy-app-install-btn-desktop')
    expect(desktop.marginEm).toBeCloseTo(0.7, 2)
    expect(desktop.labelDisplay).toBe('inline')
    // the service button has always set its own 15px spacing in the page
    const service = await styles('#cy-app-install-btn-service')
    expect(service.marginPx).toBe(15)
    expect(service.labelDisplay).toBe('inline')
    await page.goto('/apps/itlegacy')
    const legacy = await styles('#cy-app-2x-download-btn')
    expect(legacy.marginEm).toBeCloseTo(0.7, 2)
    expect(legacy.labelDisplay).toBe('inline')
  })
})
