import { expect, test } from './fixtures'

// One page per app, showing every platform it is on (#155).
test.describe('App page', () => {
  const panelOrder = (page) =>
    page.locator('.cy-app-platform-panel').evaluateAll((panels) => panels.map((panel) => panel.dataset.platform))

  test('an app on three platforms shows a button and a panel for each, without script errors', async ({ page }) => {
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

  test('the Available on buttons are large and mark the selected platform', async ({ page }) => {
    const selected = page.locator('.cy-app-platform-chip[aria-current="true"]')
    await page.goto('/apps/itmulti')
    for (const button of await page.locator('.cy-app-platform-chip').all()) {
      expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(30)
    }
    // the primary platform when none is chosen, or an unknown one is
    await expect(selected).toHaveText('Cytoscape Desktop')
    await page.goto('/apps/itmulti?platform=bogus')
    await expect(selected).toHaveText('Cytoscape Desktop')

    await page.locator('.cy-app-platform-chip', { hasText: 'Service' }).click()
    await expect(page).toHaveURL(/\?platform=service$/)
    await expect(selected).toHaveText('Service')
    await expect(page.locator('.cy-app-platform-chip.btn-primary')).toHaveCount(1)
    expect(await panelOrder(page)).toEqual(['service', 'desktop', 'web'])
  })

  test('release history lists only the selected platform, with no second set of buttons', async ({ page }) => {
    const releases = page.locator('#cy-app-releases-tab')
    for (const [platform, heading] of [['desktop', 'Cytoscape Desktop releases'], ['web', 'Cytoscape Web releases'],
                                       ['service', 'Service releases']]) {
      await page.goto(`/apps/itmulti?platform=${platform}`)
      await page.getByRole('link', { name: 'Release History' }).click()
      await expect(releases.locator('.cy-app-releases-heading')).toHaveText(heading)
      await expect(releases.locator('.cy-app-platform-releases')).toHaveCount(1)
      await expect(releases.locator(`#cy-app-releases-${platform}`)).toBeVisible()
      await expect(page.locator('#cy-app-release-platforms')).toHaveCount(0)
      await expect(releases.locator('.cy-app-platform-chip')).toHaveCount(0)
    }

    await page.goto('/apps/itmulti?platform=desktop#releases')
    await expect(releases.locator('h4 a[href*="/itmulti/"][href$="/1.0"]')).toBeVisible()
    await expect(releases.locator('.cy-app-url-copy')).toHaveCount(0)
    await page.goto('/apps/itmulti?platform=web#releases')
    await expect(releases.locator('.cy-app-url-copy input')).toHaveValue(/\/web\/itmulti\/1\.0\/manifest\.json$/)
    await page.goto('/apps/itmulti?platform=service#releases')
    await expect(releases.getByText('Service URL', { exact: true })).toBeVisible()
    await expect(releases.locator('.cy-app-url-copy input')).toHaveValue('https://service.example.org/itmulti')
  })

  test('switching platform keeps the open tab', async ({ page }) => {
    await page.goto('/apps/itmulti')
    await page.getByRole('link', { name: 'Release History' }).click()
    await page.locator('.cy-app-platform-chip', { hasText: 'Cytoscape Web' }).click()
    await expect(page).toHaveURL(/\?platform=web#releases$/)
    await expect(page.locator('#cy-app-releases-tab')).toHaveClass(/active/)
    await expect(page.locator('#cy-app-releases-web')).toBeVisible()
    await expect(page.locator('.cy-app-platform-chip[aria-current="true"]')).toHaveText('Cytoscape Web')

    await page.getByRole('link', { name: 'Details' }).click()
    await page.locator('.cy-app-platform-chip', { hasText: 'Service' }).click()
    await expect(page).toHaveURL(/\?platform=service$/)
    await expect(page.locator('#cy-app-details-tab')).toHaveClass(/active/)
    await expect(page.locator('#cy-app-releases-tab')).not.toHaveClass(/active/)
  })

  test("each platform shows its own details, categories, authors, screenshots and links", async ({ page }) => {
    const details = page.locator('#cy-app-details-md')
    const website = page.getByRole('link', { name: 'Website' })
    const expected = {
      web: { description: 'IT Multi in the browser', details: 'IT Multi for the web', tag: 'it-web-only',
             author: 'Web Author', website: 'https://example.org/web', screenshot: /itmulti-web/ },
      desktop: { description: 'IT Multi, seeded for the integration tests', details: 'IT Multi for the desktop',
                 tag: 'it-desktop', author: 'Desktop Author', website: 'https://example.org/desktop',
                 screenshot: /itmulti-desktop/ },
    }
    for (const [platform, other] of [['web', 'desktop'], ['desktop', 'web']]) {
      const own = expected[platform], theirs = expected[other]
      await page.goto(`/apps/itmulti?platform=${platform}`)
      await expect(page.locator('#app-name').locator('xpath=following-sibling::b')).toHaveText(own.description)
      await expect(details).toHaveText(own.details)
      await expect(page.locator('#cy-app-categories')).toContainText(own.tag)
      await expect(page.locator('#cy-app-categories')).not.toContainText(theirs.tag)
      await expect(page.locator('#cy-app-authors')).toContainText(own.author)
      await expect(page.locator('#cy-app-authors')).not.toContainText(theirs.author)
      await expect(page.locator('#cy-app-screenshots img')).toHaveCount(1)
      await expect(page.locator('#cy-app-screenshots img')).toHaveAttribute('src', own.screenshot)
      await expect(website).toHaveAttribute('href', own.website)
      await expect(page.getByText(theirs.details)).toHaveCount(0)
    }
    await page.goto('/apps/itmulti?platform=web')
    await expect(page.getByRole('link', { name: 'E-mail' })).toHaveAttribute('href', 'mailto:it-multi-web@example.org')
    await page.goto('/apps/itmulti?platform=desktop')
    await expect(page.getByRole('link', { name: 'E-mail' })).toHaveCount(0)
  })

  test('a platform without content of its own shows the app\'s, even beside one that has its own', async ({ page }) => {
    await page.goto('/apps/itmulti?platform=service')
    await expect(page.locator('#cy-app-details-md')).toHaveText('IT Multi for the desktop')
    await expect(page.locator('#cy-app-categories')).toContainText('it-desktop')
    await expect(page.locator('#cy-app-authors')).toContainText('Desktop Author')
    await expect(page.getByText('IT Multi for the web')).toHaveCount(0)
    await expect(page.locator('#cy-app-categories')).not.toContainText('it-web-only')

    // an app with no per-platform content at all is shown as before
    await page.goto('/apps/itweb')
    await expect(page.locator('#app-name').locator('xpath=following-sibling::b')).toHaveText('IT Web, seeded for the integration tests')
  })

  test('the name, icon and download count are shared by every platform', async ({ page }) => {
    const shared = async () => ({
      name: (await page.locator('#app-name').innerText()).trim(),
      icon: await page.locator('img').first().getAttribute('src'),
      usage: (await page.locator('#app-usage-info a[href*="/stats/"]').first().innerText()).trim(),
    })
    await page.goto('/apps/itmulti?platform=desktop')
    const desktop = await shared()
    expect(desktop.name).toBe('IT Multi')
    for (const platform of ['web', 'service']) {
      await page.goto(`/apps/itmulti?platform=${platform}`)
      expect(await shared()).toEqual(desktop)
    }
  })

  test('the Cytoscape 2 panel shows only with Desktop selected', async ({ page }) => {
    await page.goto('/apps/itcy2?platform=desktop')
    await expect(page.locator('#cy-app-panel-cy2x')).toBeVisible()
    await page.goto('/apps/itcy2?platform=web')
    await expect(page.locator('#cy-app-panel-cy2x')).toHaveCount(0)
  })

  test("the selected platform's content stays while switching tabs", async ({ page }) => {
    await page.goto('/apps/itmulti?platform=web')
    await page.getByRole('link', { name: 'Release History' }).click()
    await expect(page.locator('#cy-app-releases-web')).toBeVisible()
    await page.getByRole('link', { name: 'Details' }).click()
    await expect(page.locator('#cy-app-details-md')).toHaveText('IT Multi for the web')
    await expect(page.locator('.cy-app-platform-chip[aria-current="true"]')).toHaveText('Cytoscape Web')
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

  test('single-platform apps show one selected button, one panel and their releases', async ({ page }) => {
    for (const [name, platform] of [['itweb', 'web'], ['itservice', 'service']]) {
      await page.goto(`/apps/${name}`)
      expect(await panelOrder(page)).toEqual([platform])
      await expect(page.locator('.cy-app-platform-chip')).toHaveCount(1)
      await expect(page.locator('.cy-app-platform-chip[aria-current="true"]')).toHaveCount(1)
      await page.getByRole('link', { name: 'Release History' }).click()
      await expect(page.locator(`#cy-app-releases-${platform}`)).toBeVisible()
      await expect(page.locator('#cy-app-release-platforms')).toHaveCount(0)
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
