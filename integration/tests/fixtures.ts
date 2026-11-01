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

function signedIn(role: Role) {
  return async ({ context, page, baseURL }, use: (page: Page) => Promise<void>) => {
    await context.addCookies([{ name: 'sessionid', value: sessionKey(role), url: baseURL! }])
    await use(page)
  }
}

export const test = base.extend<{ asAdmin: Page; asEditor: Page; asOther: Page }>({
  asAdmin: signedIn('admin'),
  asEditor: signedIn('editor'),
  asOther: signedIn('other'),
})

export { expect }
