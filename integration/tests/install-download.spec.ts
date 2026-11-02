import { expect, test } from './fixtures'

// IT Multi has version 1.0 on desktop, web and service (#155): install URLs
// name the platform, and the bare URL keeps installing the service.
test.describe('Install and download', () => {
  const install = '/apps/itmulti/install/1.0'

  test('install URLs install the platform they name', async ({ request }) => {
    const web = await request.get(`${install}?platform=web`, { maxRedirects: 0 })
    expect(web.status()).toBe(302)
    expect(web.headers()['location']).toContain(encodeURIComponent('/web/itmulti/1.0/manifest.json'))

    const service = await request.get(`${install}?platform=service`, { maxRedirects: 0 })
    expect(service.status()).toBe(302)
    expect(service.headers()['location']).toContain(encodeURIComponent('https://service.example.org/itmulti'))

    const bare = await request.get(install, { maxRedirects: 0 })
    expect(bare.headers()['location']).toBe(service.headers()['location'])

    expect((await request.get(`${install}?platform=bogus`, { maxRedirects: 0 })).status()).toBe(404)
  })

  test('the desktop download serves the jar', async ({ request }) => {
    const download = await request.get('/apps/itmulti/download/1.0', { maxRedirects: 0 })
    expect(download.status()).toBe(302)
    const jar = download.headers()['location']
    expect(jar).toMatch(/\/media\/itmulti\/releases\/1\.0\/itmulti-1\.0\.jar$/)
    expect((await request.get(jar)).status()).toBe(200)
  })

  test('the stats timeline keeps the history of releases that were deleted', async ({ request }) => {
    // IT Retired's only release is inactive; its downloads are still reported, as before #155
    const timeline = await request.get('/download/stats/itretired/timeline')
    expect(await timeline.json()).toEqual({ '1.0': [['2026-01-15', 3]] })
  })

  test("the stats timeline has a series per platform's release", async ({ request }) => {
    const timeline = await request.get('/download/stats/itmulti/timeline')
    expect(Object.keys(await timeline.json()).sort()).toEqual(['desktop 1.0', 'service 1.0', 'web 1.0'])
  })
})
