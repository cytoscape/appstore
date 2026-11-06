import { expect, test } from './fixtures'
import type { Page } from '@playwright/test'

// Each platform shows only its own content (#155). Before #155 every app was on one platform,
// whose content is the app's own; a platform that joins later starts empty, and nothing of one
// platform's content ever shows on another's page.
//
// The seed has, for each platform, an IT Only app that is only read, and an IT Grow app whose
// editor submitted the two other platforms; these specs accept those, one at a time.

type Platform = 'desktop' | 'web' | 'service'
const NAMES: Record<Platform, string> = { desktop: 'Desktop', web: 'Web', service: 'Service' }
const BUTTONS: Record<Platform, string> = { desktop: 'Cytoscape Desktop', web: 'Cytoscape Web', service: 'Service' }
const QUEUE_ROWS: Record<Platform, string> = { desktop: 'desktop', web: 'web-bundle', service: 'service' }
const FIXED_RESOURCES = ['Ask a question', 'Search BioStars']

// Everything a platform's page shows of that platform's content
async function pageContent(page: Page, app: string, platform: Platform) {
  await page.goto(`/apps/${app}?platform=${platform}`)
  await expect(page.locator('.cy-app-platform-chip[aria-current="true"]')).toHaveText(BUTTONS[platform])
  const texts = async (selector: string) => (await page.locator(selector).allInnerTexts()).map((t) => t.trim())
  const attrs = (selector: string, name: string) =>
    page.locator(selector).evaluateAll((els, name) => els.map((el) => el.getAttribute(name)), name)
  const resources = await page.locator('.alert .nav-list a').evaluateAll((links) =>
    links.map((link) => `${link.textContent!.trim()} ${link.getAttribute('href')}`))
  return {
    description: await texts('#app-name ~ b'),
    details: await texts('#cy-app-details-md'),
    categories: await texts('#cy-app-categories a'),
    authors: await texts('#cy-app-authors'),
    screenshots: await attrs('#cy-app-screenshots img', 'src'),
    resources: resources.filter((link) => !FIXED_RESOURCES.some((fixed) => link.startsWith(fixed))),
    licence: await attrs(`#cy-app-panel-${platform} .cy-app-license a`, 'href'),
  }
}

const EMPTY = { description: [], details: [], categories: [], authors: [], screenshots: [], resources: [], licence: [] }

// What the seed gave 'fullname' as its own content, on the platform it was on
function seeded(fullname: string) {
  const name = fullname.toLowerCase().replace(/ /g, '')
  return {
    description: [`${fullname}, seeded for the integration tests`],
    details: [`${fullname} details`],
    categories: [`${name} category`],
    authors: [expect.stringContaining(`${fullname} Author`)],
    screenshots: [expect.stringContaining(`thumb-${name}`)],
    resources: [`Website https://example.org/${name}`, `Tutorial https://example.org/${name}-tutorial`,
                `Code Repository https://example.org/${name}-code`, `E-mail mailto:${name}@example.org`],
    licence: [`https://example.org/${name}-license`],
  }
}

async function releaseVersions(page: Page, app: string, platform: Platform) {
  await page.goto(`/apps/${app}?platform=${platform}`)
  await page.getByRole('link', { name: 'Release History' }).click()
  const releases = page.locator(`#cy-app-releases-${platform}`)
  await expect(releases).toBeVisible()
  return (await releases.locator('h4').allInnerTexts()).map((text) => text.trim().split(/\s/)[0])
}

test.describe('Apps on one platform', () => {
  for (const platform of ['desktop', 'web', 'service'] as Platform[]) {
    const fullname = `IT Only ${NAMES[platform]}`
    const app = `itonly${platform}`

    test(`an app only on ${BUTTONS[platform]} shows all its content as before`, async ({ page, request }) => {
      expect(await pageContent(page, app, platform)).toEqual(seeded(fullname))
      await expect(page.locator('.cy-app-platform-chip')).toHaveText([BUTTONS[platform]])
      // Details is the open tab
      await expect(page.locator('#cy-app-details-tab')).toBeVisible()
      expect(await releaseVersions(page, app, platform)).toEqual(['1.0'])

      // its tile on its platform's listing
      await page.goto(`/apps/platform/${platform}/`)
      await expect(page.locator(`.app_button[fullname="${fullname}"]`))
        .toContainText(`${fullname}, seeded for the integration tests`)

      // and Cytoscape Desktop's feed gives its content as before, with releases only for a Desktop app
      const entry = (await (await request.get('/backend/all_apps')).json()).find((a) => a.fullname === fullname)
      expect(entry.description).toBe(`${fullname}, seeded for the integration tests`)
      expect(entry.tags).toEqual([`${app} category`])
      expect(entry.releases.length).toBe(platform === 'desktop' ? 1 : 0)
    })
  }
})

test.describe('Adding platforms to an app', () => {
  async function accept(page: Page, fullname: string, platform: Platform) {
    await page.goto('/submit/pending')
    const row = page.locator(`tr[pending_platform="${QUEUE_ROWS[platform]}"]`, { hasText: fullname })
    await expect(row.locator('.cy-pending-type')).toHaveText(new RegExp(`New platform → ${fullname}`))
    await row.locator('.cy-accept').click()
    await expect(row).toHaveCount(0)
  }

  // each IT Grow app's original platform, then the platforms its editor submitted, in the order accepted
  const ORDERS: Platform[][] = [['desktop', 'web', 'service'], ['web', 'desktop', 'service'], ['service', 'web', 'desktop']]

  for (const [original, second, third] of ORDERS) {
    const fullname = `IT Grow ${NAMES[original]}`
    const app = `itgrow${original}`

    test(`${BUTTONS[original]} app: ${BUTTONS[second]} then ${BUTTONS[third]} join it empty, and ${BUTTONS[original]} is unchanged`,
      async ({ asAdmin: page, request }) => {
        const before = await pageContent(page, app, original)
        expect(before).toEqual(seeded(fullname))
        const name = (await page.locator('#app-name').innerText()).trim()
        const icon = await page.locator('img').first().getAttribute('src')

        const joined: Platform[] = [original]
        for (const platform of [second, third]) {
          await accept(page, fullname, platform)
          joined.push(platform)

          // every platform the app is on has a button, in the page's order
          await page.goto(`/apps/${app}`)
          const order: Platform[] = ['desktop', 'web', 'service']
          await expect(page.locator('.cy-app-platform-chip'))
            .toHaveText(order.filter((p) => joined.includes(p)).map((p) => BUTTONS[p]))

          // the original platform is unchanged, and every platform that joined is empty
          expect(await pageContent(page, app, original)).toEqual(before)
          for (const other of joined.slice(1)) {
            expect(await pageContent(page, app, other), other).toEqual(EMPTY)
            // the name and icon are shared
            expect((await page.locator('#app-name').innerText()).trim()).toBe(name)
            expect(await page.locator('img').first().getAttribute('src')).toBe(icon)
          }

          // each platform's Release History has only its own releases
          expect(await releaseVersions(page, app, original)).toEqual(['1.0'])
          expect(await releaseVersions(page, app, platform)).toEqual(['2.0'])
        }

        // Cytoscape Desktop's feed shows nothing of another platform's content
        const entry = (await (await request.get('/backend/all_apps')).json()).find((a) => a.fullname === fullname)
        if (original === 'desktop') {
          expect(entry.description).toBe(`${fullname}, seeded for the integration tests`)
          expect(entry.tags).toEqual([`${app} category`])
        } else {
          expect(entry.description ?? '').toBe('')
          expect(entry.tags).toEqual([])
        }

        // the newest platform's first edit saves, and shows on its page only
        await page.goto(`/apps/${app}/edit?platform=${third}`)
        await expect(page.locator('#cy-app-details')).toHaveValue('')
        await page.locator('#cy-app-details').fill(`${fullname} on ${third}`)
        await page.locator('#cy-app-details').press('End') // the page notices typed changes
        await page.locator('#save-btn').click()
        await expect(page).toHaveURL(new RegExp(`/apps/${app}\\?platform=${third}$`))
        await expect(page.locator('#cy-app-details-md')).toHaveText(`${fullname} on ${third}`)
        expect(await pageContent(page, app, original)).toEqual(before)
        expect(await pageContent(page, app, second)).toEqual(EMPTY)
      })
  }
})
