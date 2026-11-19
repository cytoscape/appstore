import { expect, test } from './fixtures'
import type { Page } from '@playwright/test'

// Each of an app's platforms has its own authors (#155), so the same author can be on several of
// them. On apps.cytoscape.org's database, adding an author already on another platform's page gave
// a 500 (#160); the suite's database is put in that state before the deploy's migrate. IT Author
// Platforms is seeded for this spec, on Cytoscape Desktop and Web, with no authors.
const NAME = 'IT Platforms Author'
const INSTITUTION = 'IT University'

async function addAuthorOn(page: Page, platform: 'desktop' | 'web') {
  await page.goto(`/apps/itauthorplatforms/edit?platform=${platform}`)
  await expect(page.locator('#cy-app-authors .cy-author-row')).toHaveCount(0)
  await page.locator('#cy-app-author-add').click()
  await page.locator('.cy-app-author-name').first().pressSequentially(NAME)
  await page.locator('.cy-app-author-institution').first().pressSequentially(INSTITUTION)
  await page.locator('#save-btn').click()
  // a failed save stays on the edit page and says so
  await expect(page).toHaveURL(new RegExp(`/apps/itauthorplatforms\\?platform=${platform}$`))
}

test.describe('Editing authors', () => {
  test('the same author added on two platforms of one app is allowed and shown once on each screen (#160)', async ({ asEditor }) => {
    await addAuthorOn(asEditor, 'desktop')
    // the save that was a 500 on apps.cytoscape.org
    await addAuthorOn(asEditor, 'web')

    for (const platform of ['desktop', 'web']) {
      // the app's page for the platform lists the author once
      await asEditor.goto(`/apps/itauthorplatforms?platform=${platform}`)
      const listed = asEditor.locator('#cy-app-authors li')
      await expect(listed).toHaveCount(1)
      await expect(listed).toHaveText(`${NAME} (${INSTITUTION})`)

      // its edit page has the author as one editable row
      await asEditor.goto(`/apps/itauthorplatforms/edit?platform=${platform}`)
      const rows = asEditor.locator('#cy-app-authors .cy-author-row')
      await expect(rows).toHaveCount(1)
      const name = rows.locator('.cy-app-author-name')
      const institution = rows.locator('.cy-app-author-institution')
      await expect(name).toHaveValue(NAME)
      await expect(institution).toHaveValue(INSTITUTION)
      await expect(name).toBeEditable()
      await expect(institution).toBeEditable()
    }

    // the author's page lists the app once, although it links the author once per platform
    await asEditor.goto(`/apps/with_author/${NAME}`)
    await expect(asEditor.locator('h5', { hasText: /^IT Author Platforms$/ })).toHaveCount(2) // compact and full tile
  })
})
