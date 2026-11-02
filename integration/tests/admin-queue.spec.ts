import { expect, test } from './fixtures'

// The admin queue tells new apps from new platforms of existing apps (#155).
test.describe('Admin queue', () => {
  test('rows say whether a submission is a new app or a new platform', async ({ asAdmin }) => {
    await asAdmin.goto('/submit/pending')

    const newApp = asAdmin.locator('tr[pending_platform="desktop"]', { hasText: 'IT Brand New' })
    await expect(newApp.locator('.cy-pending-type')).toHaveText('New app')

    const newPlatform = asAdmin.locator('tr[pending_platform="service"]', { hasText: 'IT Desktop' })
    await expect(newPlatform.locator('.cy-pending-type')).toHaveText(/New platform → IT Desktop/)
    await newPlatform.locator('.cy-pending-type').getByRole('link', { name: 'IT Desktop' }).click()
    await expect(asAdmin).toHaveURL(/\/apps\/itdesktop$/)
  })

  test("a submission under someone else's app name cannot be accepted", async ({ asAdmin }) => {
    await asAdmin.goto('/submit/pending')
    const row = asAdmin.locator('tr[pending_platform="desktop"]', { hasText: 'IT Web' })
    await expect(row.locator('.cy-pending-type')).toHaveText(/Name taken by IT Web/)

    await row.locator('.cy-accept').click()
    await expect(asAdmin.locator('#cy-alerts')).toContainText('IT Web already exists and it-other is not one of its editors')
    await asAdmin.reload()
    await expect(row).toHaveCount(1)

    await asAdmin.goto('/apps/itweb')
    await expect(asAdmin.locator('#cy-app-panel-desktop')).toHaveCount(0)
  })

  test('a GitHub-URL web app cannot be accepted yet, and can be declined', async ({ asAdmin }) => {
    await asAdmin.goto('/submit/pending')
    const row = asAdmin.locator('tr[pending_platform="web-url"]', { hasText: 'IT Url App' })

    await row.locator('.cy-accept').click()
    await expect(asAdmin.locator('#cy-alerts')).toContainText('Approving GitHub-URL web submissions is not supported yet')
    await expect(row.locator('.cy-decline')).toBeVisible()
    await asAdmin.reload()
    await expect(row).toHaveCount(1)

    await row.locator('.cy-decline').click()
    await expect(row).toHaveCount(0)
    await asAdmin.reload()
    await expect(row).toHaveCount(0)
  })
})
