import { expect, test } from './fixtures'
import { desktopJar, webBundle } from './support/archives'

// A submission's name picks its app on every platform (#155): IT Service's name is taken
// by its editors, who can add a Cytoscape Web version under the same name.
// (IT Desktop's Web version is admin-accept.spec.ts's, so these specs leave it alone.)
test.describe('Submission identity', () => {
  test('a non-editor cannot submit a web bundle under an existing app name', async ({ asOther }) => {
    await asOther.goto('/submit/submit_web_bundle')
    await asOther.locator('input[name="bundle"]').setInputFiles(webBundle('IT Service', '1.0'))
    await asOther.getByRole('button', { name: 'Submit' }).click()
    await expect(asOther.getByText('An app named IT Service already exists and you are not one of its editors')).toBeVisible()
  })

  test("an editor's web bundle under their service app's name adds Cytoscape Web to it", async ({ asEditor }) => {
    await asEditor.goto('/submit/submit_web_bundle')
    await asEditor.locator('input[name="bundle"]').setInputFiles(webBundle('IT Service', '1.0'))
    await asEditor.getByRole('button', { name: 'Submit' }).click()
    await expect(asEditor).toHaveURL(/\/submit\/confirm_web_bundle\/\d+$/)
    await expect(asEditor.getByText('this adds Cytoscape Web to the existing app IT Service')).toBeVisible()
  })

  test('a desktop jar repeating an existing version is refused', async ({ asEditor }) => {
    await asEditor.goto('/submit/submit_desktop_app')
    await asEditor.locator('input[name="file"]').setInputFiles(desktopJar('IT Desktop', '1.0'))
    // choosing a file slides the instructions open above the Submit button; click once it has settled
    await asEditor.waitForFunction(() => !(window as any).$('#instructions').is(':animated'))
    await Promise.all([
      asEditor.waitForResponse((response) => response.url().endsWith('/submit/submit_desktop_app') && response.request().method() === 'POST'),
      asEditor.getByRole('button', { name: 'Submit' }).click(),
    ])
    await expect(asEditor.getByText('already has a release with version 1.0')).toBeVisible()
  })
})
