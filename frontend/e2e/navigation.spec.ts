import { test, expect } from '@playwright/test'

test.describe('navigation', () => {
  test('redirects / to the board dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/board$/)
    await expect(page.getByText('Overview', { exact: true })).toBeVisible()
  })

  test('navigates to the Kanban board from the sidebar', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Kanban', exact: true }).click()
    await expect(page).toHaveURL(/\/kanban$/)
    await expect(page.getByRole('main').getByRole('heading', { name: 'Kanban Board' })).toBeVisible()
  })

  test('renders the policy sandbox page', async ({ page }) => {
    await page.goto('/sandbox')
    await expect(page.getByRole('main').getByRole('heading', { name: 'Policy Sandbox' })).toBeVisible()
  })

  test('shows the not found page for unknown routes', async ({ page }) => {
    await page.goto('/this-route-does-not-exist')
    await expect(page.getByText('Not Found')).toBeVisible()
  })
})
