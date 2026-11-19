import { defineConfig, devices } from '@playwright/test'

// make integration-test runs this suite in the e2e container of docker/compose.yml, which shares the
// App Store container's network, and points APPSTORE_URL at it on localhost.
// Tests run one at a time: they share one seeded database, and some of them change it.
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.APPSTORE_URL ?? 'http://localhost:8000',
    headless: true,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
})
