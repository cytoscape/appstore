import { expect, test } from './fixtures'
import type { Page, Response } from '@playwright/test'

// The CSS and JS files that 2.1.0 changed are fetched with ?v=<the version in the footer>, so
// each deploy changes their URLs and browsers don't reuse a cached copy from an older release.

const VERSIONED = /\/static\/(common\/css\/base\.css|apps\/css\/app_page(_edit)?\.css|apps\/js\/app_page(_edit)?\.js)(\?|$)/

async function versionedResponses(page: Page, url: string) {
  const responses: Response[] = []
  page.on('response', (response) => { if (VERSIONED.test(response.url())) responses.push(response) })
  await page.goto(url)
  await page.waitForLoadState('load')
  const footer = (await page.locator('#cy-app-version').textContent())!.replace('Version:', '').trim()
  expect(footer).not.toBe('')
  return { responses, footer }
}

function expectVersioned(responses: Response[], footer: string, files: string[]) {
  for (const file of files) {
    const matching = responses.filter((response) => new URL(response.url()).pathname === `/static/${file}`)
    expect(matching, file).not.toHaveLength(0)
    for (const response of matching) {
      expect(new URL(response.url()).searchParams.get('v'), file).toBe(footer)
      expect(response.status(), file).toBeLessThan(400)
    }
  }
}

test('the app page fetches its changed CSS and JS with the running version', async ({ page }) => {
  const { responses, footer } = await versionedResponses(page, '/apps/itmulti')
  expectVersioned(responses, footer, ['common/css/base.css', 'apps/css/app_page.css', 'apps/js/app_page.js'])
  // and app_page.js runs: the platform buttons are set up
  await expect(page.locator('.cy-app-platform-chip[aria-current="true"]')).toBeVisible()
})

test('the edit page fetches its changed CSS and JS with the running version', async ({ asEditor: page }) => {
  const { responses, footer } = await versionedResponses(page, '/apps/itmulti/edit')
  expectVersioned(responses, footer, ['common/css/base.css', 'apps/css/app_page_edit.css', 'apps/js/app_page_edit.js'])
})
