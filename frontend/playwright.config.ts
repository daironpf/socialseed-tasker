import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'npm run dev -- --host --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
      // Never reuse a running dev server: it proxies /mock-api to the demo
      // instance on 8001 (docker compose), which points at the real dataset.
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        MOCK_API_TARGET: 'http://127.0.0.1:8011',
      },
    },
    {
      command: 'python -m uvicorn server:app --app-dir ../mock-api --host 127.0.0.1 --port 8011',
      url: 'http://127.0.0.1:8011/openapi.json',
      // Always boot a dedicated mock-api on 8011 (the demo stack owns 8001
      // and points at the real dataset) writing to .e2e-data only.
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        DATA_DIR: path.join(frontendDir, '.e2e-data'),
      },
    },
  ],
})
