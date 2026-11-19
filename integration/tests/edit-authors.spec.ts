import { expect, test } from './fixtures'
import type { Page } from '@playwright/test'

// Each of an app's platforms has its own authors (#155), so the same author can be on several of
// them. On apps.cytoscape.org's database, adding an author already on another platform's page gave
// a 500 (#160); the suite's database is put in that state before the deploy's migrate. IT Author
// Platforms is seeded for this spec, on Cytoscape Desktop and Web, with no authors. The tests run
// in order, each on what the one before saved.
const NAME = 'IT Platforms Author'
const INSTITUTION = 'IT University'
const PLATFORMS = ['desktop', 'web'] as const
type Platform = (typeof PLATFORMS)[number]

// adds an author row with 'name' and 'institution' on 'platform''s edit page, and saves
async function addAuthorRow(page: Page, platform: Platform, name: string, institution: string) {
  await page.goto(`/apps/itauthorplatforms/edit?platform=${platform}`)
  const rows = page.locator('#cy-app-authors .cy-author-row')
  const before = await rows.count()
  await page.locator('#cy-app-author-add').click()
  await expect(rows).toHaveCount(before + 1)
  await rows.nth(before).locator('.cy-app-author-name').pressSequentially(name)
  await rows.nth(before).locator('.cy-app-author-institution').pressSequentially(institution)
  await page.locator('#save-btn').click()
  // a failed save stays on the edit page and says so
  await expect(page).toHaveURL(new RegExp(`/apps/itauthorplatforms\\?platform=${platform}$`))
}

// 'platform''s page lists the author once, and its edit page has the author as one editable row
async function expectAuthorOnce(page: Page, platform: Platform) {
  await page.goto(`/apps/itauthorplatforms?platform=${platform}`)
  const listed = page.locator('#cy-app-authors li')
  await expect(listed).toHaveCount(1)
  await expect(listed).toHaveText(`${NAME} (${INSTITUTION})`)

  await page.goto(`/apps/itauthorplatforms/edit?platform=${platform}`)
  const rows = page.locator('#cy-app-authors .cy-author-row')
  await expect(rows).toHaveCount(1)
  const name = rows.locator('.cy-app-author-name')
  const institution = rows.locator('.cy-app-author-institution')
  await expect(name).toHaveValue(NAME)
  await expect(institution).toHaveValue(INSTITUTION)
  await expect(name).toBeEditable()
  await expect(institution).toBeEditable()
}

test.describe('Editing authors', () => {
  test('the same author added on two platforms of one app is allowed and shown once on each screen (#160)', async ({ asEditor }) => {
    await addAuthorRow(asEditor, 'desktop', NAME, INSTITUTION)
    // the save that was a 500 on apps.cytoscape.org
    await addAuthorRow(asEditor, 'web', NAME, INSTITUTION)

    for (const platform of PLATFORMS) {
      await expectAuthorOnce(asEditor, platform)
    }

    // the author's page lists the app once, although it links the author once per platform
    await asEditor.goto(`/apps/with_author/${NAME}`)
    await expect(asEditor.locator('h5', { hasText: /^IT Author Platforms$/ })).toHaveCount(2) // compact and full tile
  })

  // the second row is the same author in other capitals, which MariaDB's collation matches to it
  for (const platform of PLATFORMS) {
    test(`an author entered twice on the ${platform} page is listed once there and on the other platform`, async ({ asEditor }) => {
      await addAuthorRow(asEditor, platform, NAME.toLowerCase(), INSTITUTION.toLowerCase())
      for (const shown of PLATFORMS) {
        await expectAuthorOnce(asEditor, shown)
      }
    })
  }
})
