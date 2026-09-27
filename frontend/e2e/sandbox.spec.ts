import { test, expect } from '@playwright/test'

test.describe('policy sandbox', () => {
  test('runs a simulation from the rules list and shows the result', async ({ page }) => {
    await page.goto('/sandbox')
    await expect(page.getByRole('main').getByRole('heading', { name: 'Policy Sandbox' })).toBeVisible()

    await page.getByLabel('Simulate').first().click()

    await expect(page.getByRole('heading', { name: 'Simulation Result' })).toBeVisible()
    await expect(page.getByText(/\d+\s+edges checked/)).toBeVisible()
    await expect(page.getByText(/\d+\s+violations found/)).toBeVisible()
  })
})
