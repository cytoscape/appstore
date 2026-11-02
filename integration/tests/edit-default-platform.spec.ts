import { expect, test } from './fixtures'

// The edit page's release edits name their platform. An edit without one applies to
// the app's one released platform, as edits did before apps had several platforms;
// an app with releases on several platforms must name the platform.
test.describe('Release edits without a platform', () => {
  const releaseId = async (page, app: string, platform: string) => {
    await page.goto(`/apps/${app}/edit`)
    return page.locator(`.cy-release[data-platform="${platform}"]`).first().getAttribute('release_id')
  }

  const saveNotes = (page, app: string, id: string, notes: string) =>
    page.request.post(`/apps/${app}/edit`, {
      form: { action: 'save_release_notes', release_count: '1', release_id_0: id, notes_0: notes },
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })

  test("default to the app's one released platform", async ({ asEditor }) => {
    const id = await releaseId(asEditor, 'itweb', 'web')
    expect((await saveNotes(asEditor, 'itweb', id!, 'Saved without a platform')).status()).toBe(200)

    await asEditor.goto('/apps/itweb')
    await expect(asEditor.locator('#cy-app-releases-web .cy-app-release-notes')).toContainText('Saved without a platform')
  })

  test('are refused for an app with releases on several platforms', async ({ asEditor }) => {
    const id = await releaseId(asEditor, 'itmulti', 'web')
    const response = await saveNotes(asEditor, 'itmulti', id!, 'Ambiguous')
    expect(response.status()).toBe(400)
    expect(await response.text()).toContain('platform is required when an app has releases on more than one platform')
  })
})
