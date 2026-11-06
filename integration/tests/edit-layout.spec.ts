import { expect, test } from './fixtures'
import type { Locator, Page } from '@playwright/test'

// The edit page's Details tab: the details first, then categories, screenshots and authors, each
// with its title and buttons on one line (title 70%, buttons left-aligned in the other 30%), its
// content below, and a line between sections. And the space between the platform buttons and
// the tabs is the same as on the app page (#155).

const box = async (locator: Locator) => (await locator.boundingBox())!

// The gap between the bottom of the platform buttons' row and the top of the tabs, measured
// at once after the page has loaded (images loading in the header move both)
async function gapAboveTabs(page: Page) {
  await page.waitForLoadState('load')
  return page.evaluate(() => {
    const buttons = document.querySelector('#cy-app-platforms')!.getBoundingClientRect()
    const tabs = document.querySelector('#cy-app-info-tabs')!.getBoundingClientRect()
    return tabs.top - buttons.bottom
  })
}

test('the edit page has the same space between the platform buttons and the tabs as the app page', async ({ asEditor: page }) => {
  await page.goto('/apps/itmulti')
  const view = await gapAboveTabs(page)
  await page.goto('/apps/itmulti/edit')
  const edit = await gapAboveTabs(page)
  expect(view).toBeGreaterThanOrEqual(10)
  expect(Math.abs(edit - view)).toBeLessThanOrEqual(1)
})

test('the Details tab lists details, then categories, screenshots and authors, each titled with its buttons beside it',
  async ({ asEditor: page }) => {
    await page.goto('/apps/itmulti/edit?platform=web')
    const sections = ['details', 'categories', 'screenshots', 'authors'].map((name) => page.locator(`#cy-edit-section-${name}`))

    // in this order, one under the other, with a line between each two
    const boxes = await Promise.all(sections.map(box))
    const lines = await Promise.all((await page.locator('#cy-app-details-tab > hr.cy-edit-section-divider').all()).map(box))
    expect(lines).toHaveLength(3)
    for (let i = 0; i < 3; i++) {
      expect(boxes[i].y + boxes[i].height).toBeLessThanOrEqual(lines[i].y)
      expect(lines[i].y).toBeLessThanOrEqual(boxes[i + 1].y)
    }
    await expect(sections[0].locator('h6').first()).toHaveText('DETAILS')
    await expect(sections[0].locator('#cy-app-details')).toBeVisible()

    const headings = { categories: 'CATEGORIES', screenshots: 'SCREENSHOTS', authors: 'AUTHORS' }
    const buttonXs: number[] = []
    for (const [i, [name, heading]] of Object.entries(headings).entries()) {
      const section = sections[i + 1]
      const head = section.locator('.cy-edit-section-head')
      const title = await box(head.locator('h6'))
      const actions = await box(head.locator('.cy-edit-section-actions'))
      const first = await box(head.locator('.cy-edit-section-actions .btn').first())
      const headBox = await box(head)
      await expect(head.locator('h6')).toHaveText(heading)

      // the title takes 70% and the buttons the other 30%, starting at its left edge, on one line
      expect(Math.abs(title.width - 0.7 * headBox.width)).toBeLessThanOrEqual(2)
      expect(Math.abs(actions.x - (headBox.x + 0.7 * headBox.width))).toBeLessThanOrEqual(2)
      expect(Math.abs(first.x - actions.x)).toBeLessThanOrEqual(1)
      expect(Math.abs((first.y + first.height / 2) - (title.y + title.height / 2))).toBeLessThanOrEqual(4)
      buttonXs.push(first.x)

      // the section's content is under its title line
      const content = { categories: '#cy-app-tags-list', screenshots: '#cy-app-screenshots', authors: '#cy-app-authors' }[name]
      expect((await box(section.locator(content))).y).toBeGreaterThanOrEqual(headBox.y + headBox.height)
    }
    // the three sections' buttons line up
    expect(Math.max(...buttonXs) - Math.min(...buttonXs)).toBeLessThanOrEqual(1)
    await expect(sections[2].locator('#cy-app-screenshot-delete-btn')).toBeVisible()

    // the buttons still work: adding an author adds a row under the title
    const authors = await page.locator('#cy-app-authors .cy-author-row').count()
    await page.locator('#cy-app-author-add').click()
    await expect(page.locator('#cy-app-authors .cy-author-row')).toHaveCount(authors + 1)
  })
