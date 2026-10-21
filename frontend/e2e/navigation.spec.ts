import { test, expect } from '@playwright/test'
import { m, useEnglishLocale } from './helpers'

test.describe('navigation', () => {
  test.beforeEach(async ({ page }) => {
    await useEnglishLocale(page)
  })

  test('redirects / to the board dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/board$/)
    await expect(page.getByText(m('boardSections.overview'), { exact: true })).toBeVisible()
  })

  test('navigates to the Kanban board from the sidebar', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: m('nav.kanban'), exact: true }).click()
    await expect(page).toHaveURL(/\/kanban$/)
    await expect(page.getByRole('main').getByRole('heading', { name: m('header.kanban') })).toBeVisible()
  })

  test('renders the policy sandbox page', async ({ page }) => {
    await page.goto('/sandbox')
    await expect(page.getByRole('main').getByRole('heading', { name: m('sandbox.title') })).toBeVisible()
  })

  test('shows the not found page for unknown routes', async ({ page }) => {
    await page.goto('/this-route-does-not-exist')
    await expect(page.getByText(m('header.notFound'))).toBeVisible()
  })
})
