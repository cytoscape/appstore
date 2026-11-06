import { expect, test } from './fixtures'

// An author's page lists the apps whose pages show that author, each once (#155).
test.describe('Author page', () => {
  const tiles = (page, fullname: string) => page.locator('h5', { hasText: new RegExp(`^${fullname}$`) })

  test('an app whose platforms share an author is listed once', async ({ page }) => {
    // IT Authors' own (Desktop) content and its Cytoscape Web content both name IT Shared Author
    await page.goto('/apps/with_author/IT Shared Author')
    // a tile shows the name twice (compact and full), so once listed is two
    await expect(tiles(page, 'IT Authors')).toHaveCount(2)

    for (const platform of ['desktop', 'web']) {
      await page.goto(`/apps/itauthors?platform=${platform}`)
      await expect(page.locator('#cy-app-authors')).toContainText('IT Shared Author')
    }
  })

  test('an app is not listed under an author none of its pages show', async ({ page, request }) => {
    // IT Replaced Authors is Web-only, and its Web authors replaced its own
    await page.goto('/apps/itreplacedauthors')
    await expect(page.locator('#cy-app-authors')).toContainText('IT Current Author')
    await expect(page.locator('#cy-app-authors')).not.toContainText('IT Former Author')

    expect((await request.get('/apps/with_author/IT Former Author')).status()).toBe(404)
    await page.goto('/apps/with_author/IT Current Author')
    await expect(tiles(page, 'IT Replaced Authors')).toHaveCount(2)
  })

  test("an app is listed under each platform's own author", async ({ page }) => {
    // IT Multi's Desktop page shows Desktop Author and its Cytoscape Web page Web Author
    for (const author of ['Desktop Author', 'Web Author']) {
      await page.goto(`/apps/with_author/${author}`)
      await expect(tiles(page, 'IT Multi')).toHaveCount(2)
    }
  })
})
