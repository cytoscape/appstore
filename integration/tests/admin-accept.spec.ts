import { expect, test } from './fixtures'

// The seed has a pending Cytoscape Web bundle for IT Desktop, a desktop app (#155).
// Accepting it must add Web to IT Desktop instead of failing to create a second app.
test('accepting a new-platform submission adds the platform to the existing app', async ({ asAdmin, request }) => {
  await asAdmin.goto('/submit/pending')
  const row = asAdmin.locator('tr[pending_platform="web-bundle"]', { hasText: 'IT Desktop' })
    .filter({ has: asAdmin.locator('.cy-web-app-version', { hasText: /^1\.0$/ }) })
  await expect(row).toHaveCount(1)
  await row.getByRole('button', { name: 'Accept' }).click()
  await expect(row).toHaveCount(0)

  await asAdmin.reload()
  await expect(asAdmin.locator('tr[pending_platform="web-bundle"]', { hasText: 'IT Desktop' })).toHaveCount(0)

  const appPage = await asAdmin.goto('/apps/itdesktop')
  expect(appPage?.status()).toBe(200)
  await expect(asAdmin.locator('h6', { hasText: 'CYTOSCAPE 3' })).toBeVisible()

  // the bundle was published under the existing app's name
  const manifest = await request.get('/web/itdesktop/1.0/manifest.json')
  expect(manifest.status()).toBe(200)
  expect(await manifest.json()).toEqual([expect.objectContaining({ id: 'itdesktop', name: 'IT Desktop', version: '1.0' })])
})
