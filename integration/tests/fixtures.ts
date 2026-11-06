import { test as base, expect, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

// Session keys the container's seed_integration_data wrote for its it-* users;
// make integration-test copies them out of the container before the run.
type Role = 'admin' | 'editor' | 'other'

function sessionKey(role: Role): string {
  const sessions = JSON.parse(readFileSync(join(__dirname, '..', '.auth', 'sessions.json'), 'utf8'))
  return sessions[role]
}

// Signs the page's browser in as 'role', in place of whoever it was signed in as.
// The asAdmin/asEditor/asOther fixtures share one page, so a spec that needs two users
// signs in as the second with this.
export async function signInAs(page: Page, role: Role, baseURL: string) {
  await page.context().clearCookies({ name: 'sessionid' })
  await page.context().addCookies([{ name: 'sessionid', value: sessionKey(role), url: baseURL }])
}

function signedIn(role: Role) {
  return async ({ page, baseURL }, use: (page: Page) => Promise<void>) => {
    await signInAs(page, role, baseURL!)
    await use(page)
  }
}

// Every page loads analytics and an icon stylesheet from the internet; a slow fetch of either
// holds up the page's load event, and the specs don't need them, so the browser never fetches them.
const INTERNET_ASSETS = /^https:\/\/(www\.googletagmanager\.com|www\.google-analytics\.com|cdnjs\.cloudflare\.com)\//

export const test = base.extend<{ asAdmin: Page; asEditor: Page; asOther: Page }>({
  context: async ({ context }, use) => {
    await context.route(INTERNET_ASSETS, (route) => route.abort())
    await use(context)
  },
  asAdmin: signedIn('admin'),
  asEditor: signedIn('editor'),
  asOther: signedIn('other'),
})

export { expect }
