import type { Page, Route } from '@playwright/test'

// A fake of Cytoscape Desktop's CyREST on 127.0.0.1:1234, served to the page through
// Playwright routing. It answers what the app page asks: whether Desktop is running,
// the desktop App Manager's apps commands, and the Desktop Service App's serviceapps commands.
export type FakeCyRestState = {
  running?: boolean
  installedApps?: string[] // desktop apps, by full name
  updatableApps?: string[]
  installedServiceApps?: { name: string; version: string; url: string; reachable?: boolean }[]
  serviceApp?: boolean // whether Desktop has the Desktop Service App, which adds the serviceapps commands
}

export type FakeCyRest = { requests: URL[]; paths: () => string[] }

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'origin, content-type, accept, authorization',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, HEAD',
}

export async function fakeCyRest(page: Page, state: FakeCyRestState = {}): Promise<FakeCyRest> {
  const { running = true, installedApps = [], updatableApps = [], installedServiceApps = [], serviceApp = true } = state
  const requests: URL[] = []

  const reply = (route: Route, status: number, body: string, contentType = 'text/plain') =>
    route.fulfill({ status, body, contentType, headers: CORS })

  await page.route('http://127.0.0.1:1234/**', async (route) => {
    const url = new URL(route.request().url())
    requests.push(url)
    if (!running) return route.abort('connectionrefused')
    if (route.request().method() === 'OPTIONS') return reply(route, 204, '')
    if (!serviceApp && url.pathname.startsWith('/v1/commands/serviceapps/'))
      return reply(route, 404, "Error: no such namespace: 'serviceapps'")

    switch (url.pathname) {
      case '/v1':
        return reply(route, 200, '{"availableApiVersions":["v1"]}', 'application/json')
      case '/v1/version':
        return reply(route, 200, '{"apiVersion":"v1","cytoscapeVersion":"3.10.3"}', 'application/json')
      case '/v1/commands/apps/list%20installed':
      case '/v1/commands/apps/list installed':
        return reply(route, 200, installedApps.map((name) => `app name: ${name}, version: 1.0, status: Installed`).join('\n') + '\nFinished\n')
      case '/v1/commands/apps/list%20updates':
      case '/v1/commands/apps/list updates':
        return reply(route, 200, updatableApps.map((name) => `app name: ${name}`).join('\n') + '\nFinished\n')
      case '/v1/commands/apps/install':
        return reply(route, 200, `app ${url.searchParams.get('app')} installed\nFinished\n`)
      case '/v1/commands/serviceapps/list':
        return reply(route, 200, JSON.stringify(installedServiceApps) + '\nFinished\n')
      case '/v1/commands/serviceapps/install':
        return reply(route, 200, `installed ${url.searchParams.get('name')} ${url.searchParams.get('version')}\nFinished\n`)
      default:
        return reply(route, 404, 'Not found')
    }
  })

  return { requests, paths: () => requests.map((url) => decodeURIComponent(url.pathname)) }
}
