import {defineConfig} from '@playwright/test';

// run-ux-browser-check.py builds an isolated copy before starting this server.
export default defineConfig({
  testDir: './e2e',
  testMatch: ['ux-plan.spec.ts', 'ux-walk.spec.ts'],
  workers: 1,
  timeout: 20000,
  use: {baseURL: 'http://127.0.0.1:3040', browserName: 'chromium', headless: true},
  reporter: 'list',
  webServer: {
    command: 'npx next start --hostname 127.0.0.1 --port 3040',
    url: 'http://127.0.0.1:3040',
    reuseExistingServer: false,
    timeout: 120000,
    env: {NEXT_PUBLIC_API_BASE_URL: 'http://127.0.0.1:8140'},
  },
});
