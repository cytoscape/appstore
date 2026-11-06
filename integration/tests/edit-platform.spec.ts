import { expect, signInAs, test } from './fixtures'

// The edit page edits one platform's content at a time (#155). IT Content and
// IT Switch are seeded for these specs, so editing them leaves other specs' apps alone.
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGM8EaDBgA0wYRUdtBIA/ygBUMG5Z0IAAAAASUVORK5CYII=',
  'base64')

test.describe('Editing per platform', () => {
  const selected = (page) => page.locator('.cy-app-platform-chip[aria-current="true"]')
  const description = (page) => page.locator('#app-name').locator('xpath=following-sibling::b')

  test("Edit this page opens the edit page on the platform being viewed", async ({ asEditor }) => {
    await asEditor.goto('/apps/itcontent?platform=web')
    await asEditor.getByText('Editor Actions').click()
    await asEditor.getByRole('link', { name: 'Edit this page' }).click()
    await expect(asEditor).toHaveURL(/\/apps\/itcontent\/edit\?platform=web$/)
    await expect(selected(asEditor)).toHaveText('Cytoscape Web')
  })

  test("every kind of content edited for Cytoscape Web shows only on its web page", async ({ asEditor, request }) => {
    await asEditor.goto('/apps/itcontent/edit?platform=web')
    // Cytoscape Web starts empty: nothing of Desktop's is shown or copied
    await expect(asEditor.locator('#cy-app-description')).toHaveValue('')
    await expect(asEditor.locator('#cy-app-details')).toHaveValue('')
    await expect(asEditor.locator('#cy-app-tags-list .cy-app-tag')).toHaveCount(0)
    await expect(asEditor.locator('#cy-app-authors .cy-author-row')).toHaveCount(0)
    await expect(asEditor.locator('#cy-app-screenshots img')).toHaveCount(0)
    await expect(asEditor.locator('#cy-app-website input')).toHaveValue('')

    await asEditor.locator('#cy-app-description').fill('IT Content in the browser')
    await asEditor.locator('#cy-app-details').fill('IT Content web details')
    await asEditor.locator('#cy-app-website input').fill('https://example.org/content-web')
    await asEditor.locator('#cy-app-details').press('End') // the page notices typed changes
    await asEditor.locator('#cy-app-description').press('End')
    await asEditor.locator('#cy-app-website input').press('End')

    await asEditor.locator('#cy-app-tag-add-btn').click()
    await asEditor.locator('#cy-tag-add-popover input').pressSequentially('it-content-web')
    await asEditor.locator('#cy-tag-add-popover button').click()
    await expect(asEditor.locator('#cy-app-tags-list .cy-app-tag')).toHaveText([/it-content-web/])

    await asEditor.locator('#cy-app-author-add').click()
    await asEditor.locator('.cy-app-author-name').first().pressSequentially('Web Editor Author')

    await asEditor.locator('#cy-app-screenshot-file-chooser').setInputFiles({ name: 'content-web.png', mimeType: 'image/png', buffer: PNG })
    await expect(asEditor.locator('#cy-app-screenshots img')).toHaveCount(1)

    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itcontent\?platform=web$/)
    await expect(description(asEditor)).toHaveText('IT Content in the browser')
    await expect(asEditor.locator('#cy-app-details-md')).toHaveText('IT Content web details')
    await expect(asEditor.locator('#cy-app-categories')).toContainText('it-content-web')
    await expect(asEditor.locator('#cy-app-categories')).not.toContainText('it-content-desktop')
    await expect(asEditor.locator('#cy-app-authors')).toContainText('Web Editor Author')
    await expect(asEditor.locator('#cy-app-authors')).not.toContainText('Content Desktop Author')
    await expect(asEditor.locator('#cy-app-screenshots img')).toHaveCount(1)
    await expect(asEditor.getByRole('link', { name: 'Website' })).toHaveAttribute('href', 'https://example.org/content-web')

    await asEditor.goto('/apps/itcontent?platform=desktop')
    await expect(description(asEditor)).toHaveText('IT Content, seeded for the integration tests')
    await expect(asEditor.locator('#cy-app-details-md')).toHaveText('IT Content desktop details')
    await expect(asEditor.locator('#cy-app-categories')).toContainText('it-content-desktop')
    await expect(asEditor.locator('#cy-app-categories')).not.toContainText('it-content-web')
    await expect(asEditor.locator('#cy-app-authors')).toContainText('Content Desktop Author')
    await expect(asEditor.locator('#cy-app-authors')).not.toContainText('Web Editor Author')
    await expect(asEditor.locator('#cy-app-screenshots img')).toHaveCount(1)
    await expect(asEditor.getByRole('link', { name: 'Website' })).toHaveAttribute('href', 'https://example.org/content-desktop')

    await asEditor.goto('/apps/itcontent/edit?platform=desktop')
    await expect(asEditor.locator('#cy-app-description')).toHaveValue('IT Content, seeded for the integration tests')
    await expect(asEditor.locator('#cy-app-details')).toHaveValue('IT Content desktop details')

    // Cytoscape Desktop's App Manager feed still gives the desktop content
    const feed = await (await request.get('/backend/all_apps')).json()
    const entry = feed.find((app) => app.fullname === 'IT Content')
    expect(entry.description).toBe('IT Content, seeded for the integration tests')
    expect(entry.tags).toEqual(['it-content-desktop'])
  })

  test('editors added from one platform can edit every platform', async ({ asEditor, baseURL }) => {
    await asEditor.goto('/apps/itcontent/edit?platform=web')
    await asEditor.locator('#cy-app-editor-add').click()
    await asEditor.locator('#cy-editor-add-popover input').pressSequentially('it-other@example.org')
    await asEditor.locator('#cy-editor-add-popover button').click()
    await expect(asEditor.locator('#editors-list')).toContainText('it-other@example.org')
    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itcontent\?platform=web$/)

    await signInAs(asEditor, 'other', baseURL!)
    await asEditor.goto('/apps/itcontent?platform=desktop')
    await expect(asEditor.getByText('Editor Actions')).toBeVisible()
    await asEditor.goto('/apps/itcontent/edit?platform=desktop')
    await expect(asEditor.locator('#save-btn')).toBeVisible()
  })

  test("release notes are edited on their platform's edit page", async ({ asEditor }) => {
    await asEditor.goto('/apps/itcontent/edit?platform=web')
    await asEditor.getByRole('link', { name: 'Release History' }).click()
    await expect(asEditor.locator('.cy-app-releases-heading')).toHaveText('Cytoscape Web releases')
    await expect(asEditor.locator('.cy-release')).toHaveCount(1)
    await expect(asEditor.locator('.cy-release[data-platform="desktop"]')).toHaveCount(0)
    await asEditor.locator('.cy-release[data-platform="web"] .cy-release-notes').pressSequentially('IT Content web notes')
    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itcontent\?platform=web$/)

    await asEditor.goto('/apps/itcontent?platform=web#releases')
    await expect(asEditor.locator('#cy-app-releases-web .cy-app-release-notes')).toContainText('IT Content web notes')
    await asEditor.goto('/apps/itcontent?platform=desktop#releases')
    await expect(asEditor.locator('.cy-app-release-notes')).toHaveCount(0)
  })

  test('the Cytoscape 2 fields are edited only with Desktop selected', async ({ asEditor }) => {
    await asEditor.goto('/apps/itcy2/edit?platform=desktop')
    await expect(asEditor.getByText('Cytoscape 2.x Plugin')).toBeVisible()
    await asEditor.goto('/apps/itcy2/edit?platform=web')
    await expect(asEditor.getByText('Cytoscape 2.x Plugin')).toHaveCount(0)
  })
})

test.describe('Switching platform on the edit page', () => {
  const details = (page) => page.locator('#cy-app-details')
  const dialog = (page) => page.locator('#switch-modal')
  const chip = (page, name: string) => page.locator('.cy-app-platform-chip', { hasText: name })

  test('without unsaved changes it switches straight away', async ({ asEditor }) => {
    await asEditor.goto('/apps/itswitch/edit?platform=web')
    await chip(asEditor, 'Cytoscape Desktop').click()
    await expect(asEditor).toHaveURL(/\/apps\/itswitch\/edit\?platform=desktop$/)
    await expect(dialog(asEditor)).toBeHidden()
  })

  test('Stay keeps the unsaved changes, which Save then saves', async ({ asEditor }) => {
    await asEditor.goto('/apps/itswitch/edit?platform=web')
    await details(asEditor).fill('IT Switch details stayed')
    await details(asEditor).press('End') // the page notices typed changes
    await chip(asEditor, 'Cytoscape Desktop').click()
    await expect(dialog(asEditor)).toBeVisible()
    await asEditor.locator('#switch-stay-btn').click()
    await expect(dialog(asEditor)).toBeHidden()
    await expect(asEditor).toHaveURL(/\/apps\/itswitch\/edit\?platform=web$/)
    await expect(details(asEditor)).toHaveValue('IT Switch details stayed')

    await asEditor.locator('#save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itswitch\?platform=web$/)
    await expect(asEditor.locator('#cy-app-details-md')).toHaveText('IT Switch details stayed')
  })

  test('Save and switch saves this platform, then edits the other', async ({ asEditor }) => {
    await asEditor.goto('/apps/itswitch/edit?platform=web')
    await details(asEditor).fill('')
    await details(asEditor).pressSequentially('IT Switch web details')
    await chip(asEditor, 'Cytoscape Desktop').click()
    await asEditor.locator('#switch-save-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itswitch\/edit\?platform=desktop$/)
    await expect(details(asEditor)).toHaveValue('IT Switch details')

    await asEditor.goto('/apps/itswitch?platform=web')
    await expect(asEditor.locator('#cy-app-details-md')).toHaveText('IT Switch web details')
    await asEditor.goto('/apps/itswitch?platform=desktop')
    await expect(asEditor.locator('#cy-app-details-md')).toHaveText('IT Switch details')
  })

  test('Discard and switch saves nothing', async ({ asEditor }) => {
    await asEditor.goto('/apps/itswitch/edit?platform=desktop')
    const website = asEditor.locator('#cy-app-website input')
    await website.fill('')
    await website.pressSequentially('https://example.org/discarded')
    await chip(asEditor, 'Cytoscape Web').click()
    await asEditor.locator('#switch-discard-btn').click()
    await expect(asEditor).toHaveURL(/\/apps\/itswitch\/edit\?platform=web$/)

    await asEditor.goto('/apps/itswitch?platform=desktop')
    await expect(asEditor.getByRole('link', { name: 'Website' })).toHaveAttribute('href', 'https://example.org/switch')
  })
})
