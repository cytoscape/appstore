import { expect, test } from './fixtures'
import { fakeCyRest } from './support/fakeCyRest'

// IT Multi has a desktop jar and a service (#155): its page has two buttons that
// install into Cytoscape Desktop, each with its own state and its own CyREST commands.
test.describe('Install buttons for desktop and service together', () => {
  const desktopButton = (page) => page.locator('#cy-app-install-btn-desktop')
  const serviceButton = (page) => page.locator('#cy-app-install-btn-service')

  test('both buttons offer to install when Desktop has neither', async ({ page }) => {
    await fakeCyRest(page)
    await page.goto('/apps/itmulti')
    await expect(desktopButton(page).locator('h4')).toHaveText('Install')
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')
    await expect(desktopButton(page)).not.toHaveClass(/\bdisabled\b/)
    await expect(serviceButton(page)).not.toHaveClass(/\bdisabled\b/)
  })

  test('each button installs only its own app', async ({ page }) => {
    const cyrest = await fakeCyRest(page)
    await page.goto('/apps/itmulti')
    await expect(desktopButton(page).locator('h4')).toHaveText('Install')

    await desktopButton(page).click()
    await expect(desktopButton(page).locator('h4')).toHaveText('Installed')
    expect(cyrest.paths()).toContain('/v1/commands/apps/install')
    expect(cyrest.paths()).not.toContain('/v1/commands/serviceapps/install')
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')

    const beacon = page.waitForResponse((response) => /\/install\/itmulti\/1\.0\?client=desktop$/.test(response.url()))
    await serviceButton(page).click()
    expect((await beacon).status()).toBe(204)
    await expect(serviceButton(page).locator('h4')).toHaveText('Service app installed in Cytoscape Desktop')
    const installs = cyrest.paths().filter((path) => path.endsWith('/install'))
    expect(installs).toEqual(['/v1/commands/apps/install', '/v1/commands/serviceapps/install'])
    await expect(desktopButton(page).locator('h4')).toHaveText('Installed')
  })

  test('without Desktop running each button falls back on its own', async ({ page }) => {
    await fakeCyRest(page, { running: false })
    await page.goto('/apps/itmulti')
    await expect(serviceButton(page)).toHaveAttribute('title', 'Start Cytoscape Desktop 3.10 or later, then reload this page.')
    await expect(serviceButton(page)).toHaveClass(/\bdisabled\b/)
    await expect(desktopButton(page).locator('h4')).toHaveText('Download')
    await expect(desktopButton(page)).not.toHaveClass(/\bdisabled\b/)
  })

  test('an installed desktop app does not stop the service from installing', async ({ page }) => {
    await fakeCyRest(page, { installedApps: ['IT Multi'] })
    await page.goto('/apps/itmulti')
    await expect(desktopButton(page).locator('h4')).toHaveText('Installed')
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')
    await expect(serviceButton(page)).not.toHaveClass(/\bdisabled\b/)
  })

  test('accepting the license installs what the clicked button installs', async ({ page }) => {
    // IT Licensed needs its license accepted; the desktop and service buttons share one license dialog
    await page.route('https://example.org/**', (route) => route.fulfill({ body: '<p>IT Licensed license</p>', contentType: 'text/html' }))
    const cyrest = await fakeCyRest(page)
    const installs = () => cyrest.paths().filter((path) => path.endsWith('/install'))
    const accept = page.locator('#license_modal .btn-primary')
    await page.goto('/apps/itlicensed')
    await expect(desktopButton(page).locator('h4')).toHaveText('Install')
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')

    await desktopButton(page).click()
    await expect(accept).toBeVisible()
    await accept.click()
    await expect(desktopButton(page).locator('h4')).toHaveText('Installed')
    expect(installs()).toEqual(['/v1/commands/apps/install'])

    await expect(accept).toBeHidden()
    await serviceButton(page).click()
    await expect(accept).toBeVisible()
    await accept.click()
    await expect(serviceButton(page).locator('h4')).toHaveText('Service app installed in Cytoscape Desktop')
    expect(installs()).toEqual(['/v1/commands/apps/install', '/v1/commands/serviceapps/install'])
  })
})
