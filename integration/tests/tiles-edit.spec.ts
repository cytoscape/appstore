import { expect, test } from './fixtures'

// Tiles show each platform an app is on, and editors manage each platform's releases (#155).
test.describe('Tiles and the edit page', () => {
  const tile = (page, name: string) => page.locator('.app_button', { hasText: name }).first()

  test('tiles have a sticker per platform and say downloads or installs', async ({ page }) => {
    await page.goto('/apps/all')
    const multi = tile(page, 'IT Multi')
    await expect(multi.locator('.cy-sticker-desktop')).toHaveCount(1)
    await expect(multi.locator('.cy-sticker-web')).toHaveCount(1)
    await expect(multi.locator('.cy-app-usage')).toHaveText(/\d+ downloads/)

    const web = tile(page, 'IT Web')
    await expect(web.locator('.cy-sticker-desktop')).toHaveCount(0)
    await expect(web.locator('.cy-sticker-web')).toHaveCount(1)
    await expect(web.locator('.cy-app-usage')).toHaveText(/\d+ installs/)
  })

  test("an editor's release notes go to the platform's release they were written for", async ({ asEditor }) => {
    await asEditor.goto('/apps/itedit/edit')
    await asEditor.getByRole('link', { name: 'Release History' }).click()
    await expect(asEditor.locator('.cy-release-platform')).toHaveText(['Cytoscape Desktop', 'Cytoscape Web', 'Service'])

    await asEditor.locator('.cy-release[data-platform="web"] .cy-release-notes').pressSequentially('Notes for the web bundle')
    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itedit$/)

    await asEditor.goto('/apps/itedit?platform=web')
    await expect(asEditor.locator('#cy-app-releases-web .cy-app-release-notes')).toContainText('Notes for the web bundle')
    await expect(asEditor.locator('#cy-app-releases-desktop .cy-app-release-notes')).toHaveCount(0)
  })

  test('deleting the last web release takes the app off the web platform', async ({ asEditor }) => {
    await asEditor.goto('/apps/itedit/edit')
    await asEditor.getByRole('link', { name: 'Release History' }).click()
    await asEditor.locator('.cy-release[data-platform="web"] .cy-release-delete').click()
    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itedit$/)

    await expect(asEditor.locator('.cy-app-platform-chip')).toHaveText(['Cytoscape Desktop', 'Service'])
    await asEditor.goto('/apps/platform/web/')
    await expect(tile(asEditor, 'IT Edit')).toHaveCount(0)
    await asEditor.goto('/apps/platform/desktop/')
    await expect(tile(asEditor, 'IT Edit')).toHaveCount(1)
  })
})
