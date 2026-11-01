import { expect, test } from './fixtures'
import { desktopJar, webBundle } from './support/archives'

// A submission's name picks its app on every platform (#155): IT Desktop's name is taken
// by its editors, who can add a Cytoscape Web version under the same name.
test.describe('Submission identity', () => {
  test('a non-editor cannot submit a web bundle under an existing app name', async ({ asOther }) => {
    await asOther.goto('/submit/submit_web_bundle')
    await asOther.locator('input[name="bundle"]').setInputFiles(webBundle('IT Desktop', '2.0'))
    await asOther.getByRole('button', { name: 'Submit' }).click()
    await expect(asOther.getByText('An app named IT Desktop already exists and you are not one of its editors')).toBeVisible()
  })

  test("an editor's web bundle under their desktop app's name adds Cytoscape Web to it", async ({ asEditor }) => {
    await asEditor.goto('/submit/submit_web_bundle')
    await asEditor.locator('input[name="bundle"]').setInputFiles(webBundle('IT Desktop', '2.0'))
    await asEditor.getByRole('button', { name: 'Submit' }).click()
    await expect(asEditor).toHaveURL(/\/submit\/confirm_web_bundle\/\d+$/)
    await expect(asEditor.getByText('this adds Cytoscape Web to the existing app IT Desktop')).toBeVisible()
  })

  test('a desktop jar repeating an existing version is refused', async ({ asEditor }) => {
    await asEditor.goto('/submit/submit_desktop_app')
    await asEditor.locator('input[name="file"]').setInputFiles(desktopJar('IT Desktop', '1.0'))
    await asEditor.getByRole('button', { name: 'Submit' }).click()
    await expect(asEditor.getByText('already has a release with version 1.0')).toBeVisible()
  })
})
