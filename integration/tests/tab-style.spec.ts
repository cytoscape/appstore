import { expect, test } from './fixtures'
import type { Locator, Page } from '@playwright/test'

// The app page and its edit page open on the first platform button and the Details tab, and the
// Details / Release History tabs look like the platform buttons: the selected one solid blue,
// the others white with a border (#155).

const LOOK = ['background-color', 'background-image', 'color', 'border-top-color', 'border-bottom-color']

const look = (locator: Locator) =>
  locator.evaluate((el, props) => {
    const style = getComputedStyle(el)
    return Object.fromEntries(props.map((prop) => [prop, style.getPropertyValue(prop)]))
  }, LOOK)

const chips = (page: Page) => page.locator('.cy-app-platform-chip')
const selectedChip = (page: Page) => page.locator('.cy-app-platform-chip[aria-current="true"]')
const tab = (page: Page, name: string) => page.locator('#cy-app-info-tabs > li > a', { hasText: name })

async function expectFirstPlatformAndDetails(page: Page) {
  await expect(selectedChip(page)).toHaveText('Cytoscape Desktop')
  // the selected button is the first, leftmost one
  const boxes = await Promise.all((await chips(page).all()).map((chip) => chip.boundingBox()))
  expect((await selectedChip(page).boundingBox())!.x).toBe(Math.min(...boxes.map((box) => box!.x)))
  await expect(page.locator('#cy-app-info-tabs > li.active')).toHaveText('Details')
  await expect(page.locator('#cy-app-details-tab')).toBeVisible()
  await expect(page.locator('#cy-app-releases-tab')).toBeHidden()
}

async function expectTabsLookLikeButtons(page: Page, selectedTab: string, otherTab: string) {
  const selectedButton = await look(selectedChip(page))
  const otherButton = await look(page.locator('.cy-app-platform-chip:not([aria-current])').first())
  expect(selectedButton).not.toEqual(otherButton)
  expect(await look(tab(page, selectedTab))).toEqual(selectedButton)
  expect(await look(tab(page, otherTab))).toEqual(otherButton)
}

for (const [where, url] of [['app page', '/apps/itmulti'], ['edit page', '/apps/itmulti/edit']]) {
  test.describe(`The ${where}`, () => {
    test('opens on the first platform and the Details tab', async ({ asEditor: page }) => {
      await page.goto(url)
      await expectFirstPlatformAndDetails(page)
    })

    test('styles the selected and unselected tabs like the platform buttons', async ({ asEditor: page }) => {
      await page.goto(url)
      await expectTabsLookLikeButtons(page, 'Details', 'Release History')

      await tab(page, 'Release History').click()
      await expect(page.locator('#cy-app-info-tabs > li.active')).toHaveText('Release History')
      await page.mouse.move(0, 0) // a hovered tab is shaded
      await expectTabsLookLikeButtons(page, 'Release History', 'Details')
    })
  })
}

test('reloading the app page opens Details again', async ({ page }) => {
  await page.goto('/apps/itmulti')
  await tab(page, 'Release History').click()
  await expect(page.locator('#cy-app-releases-tab')).toBeVisible()
  await expect(page).toHaveURL(/\/apps\/itmulti$/)
  await page.reload()
  await expectFirstPlatformAndDetails(page)
})
