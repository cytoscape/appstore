import { expect, test } from './fixtures'
import { fakeCyRest } from './support/fakeCyRest'

// IT Multi has a desktop jar and a service (#155): its page has two buttons that
// install into Cytoscape Desktop, each with its own state and its own CyREST commands.
// The greyed-out service button's info icon and tooltip say what Cytoscape Desktop needs (#154)
const NOT_RUNNING = 'To install this service app, Cytoscape Desktop 3.10 or later must be running and have the ' +
  'Desktop Service App installed. Start Cytoscape Desktop, then reload this page.'
const SERVICE_APP_MISSING = 'Cytoscape Desktop was detected, but the Desktop Service App is missing. ' +
  'Install it first to install service apps.'

// The button's info icon is in its upper-left corner
async function expectInfoIconInCorner(button) {
  const icon = button.locator('i')
  await expect(icon).toHaveClass('icon-info-sign')
  const iconBox = (await icon.boundingBox())!
  const buttonBox = (await button.boundingBox())!
  expect(iconBox.x + iconBox.width).toBeLessThanOrEqual(buttonBox.x + buttonBox.width / 2)
  expect(iconBox.y + iconBox.height).toBeLessThanOrEqual(buttonBox.y + buttonBox.height / 2)
}

test.describe('Install buttons for desktop and service together', () => {
  const desktopButton = (page) => page.locator('#cy-app-install-btn-desktop')
  const serviceButton = (page) => page.locator('#cy-app-install-btn-service')

  test('without the Desktop Service App, the service button says what Desktop needs', async ({ page }) => {
    await fakeCyRest(page, { serviceApp: false })
    await page.goto('/apps/itmulti')
    await expect(serviceButton(page)).toHaveAttribute('title', SERVICE_APP_MISSING)
    await expect(serviceButton(page)).toHaveClass(/\bdisabled\b/)
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')
    await expectInfoIconInCorner(serviceButton(page))
    // the desktop app's button is unaffected
    await expect(desktopButton(page).locator('h4')).toHaveText('Install')
    await expect(desktopButton(page)).not.toHaveClass(/\bdisabled\b/)
  })

  test('the tooltip is only on the greyed-out state', async ({ page }) => {
    await fakeCyRest(page)
    await page.goto('/apps/itmulti')
    await expect(serviceButton(page)).not.toHaveClass(/\bdisabled\b/)
    await expect(serviceButton(page)).not.toHaveAttribute('title', /.*/)
    await expect(serviceButton(page).locator('i')).not.toHaveClass(/icon-info-sign/)
  })

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
    await expect(serviceButton(page)).toHaveAttribute('title', NOT_RUNNING)
    await expect(serviceButton(page)).toHaveClass(/\bdisabled\b/)
    await expectInfoIconInCorner(serviceButton(page))
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

  test("each install button asks for its own platform's license, and accepting installs what it installs", async ({ page }) => {
    // IT Licensed's desktop version and its service version each have a license to accept
    await page.route('https://example.org/**', (route) => route.fulfill({ body: '<p>IT Licensed license</p>', contentType: 'text/html' }))
    const cyrest = await fakeCyRest(page)
    const installs = () => cyrest.paths().filter((path) => path.endsWith('/install'))
    const dialog = (platform: string) => page.locator(`#license_modal_${platform}`)
    await page.goto('/apps/itlicensed')
    await expect(desktopButton(page).locator('h4')).toHaveText('Install')
    await expect(serviceButton(page).locator('h4')).toHaveText('Install service app in Cytoscape Desktop')
    await expect(page.locator('#cy-app-panel-desktop .cy-app-license a')).toHaveAttribute('href', 'https://example.org/it-licensed-license')
    await expect(page.locator('#cy-app-panel-service .cy-app-license a')).toHaveAttribute('href', 'https://example.org/it-licensed-service-license')

    await desktopButton(page).click()
    await expect(dialog('desktop')).toBeVisible()
    await expect(dialog('desktop').locator('iframe')).toHaveAttribute('src', 'https://example.org/it-licensed-license')
    await expect(dialog('service')).toBeHidden()
    await dialog('desktop').locator('.btn-primary').click()
    await expect(desktopButton(page).locator('h4')).toHaveText('Installed')
    expect(installs()).toEqual(['/v1/commands/apps/install'])

    await expect(dialog('desktop')).toBeHidden()
    await serviceButton(page).click()
    await expect(dialog('service')).toBeVisible()
    await expect(dialog('service').locator('iframe')).toHaveAttribute('src', 'https://example.org/it-licensed-service-license')
    await dialog('service').locator('.btn-primary').click()
    await expect(serviceButton(page).locator('h4')).toHaveText('Service app installed in Cytoscape Desktop')
    expect(installs()).toEqual(['/v1/commands/apps/install', '/v1/commands/serviceapps/install'])
  })
})
