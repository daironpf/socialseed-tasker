import { test, expect } from '@playwright/test'
import { m, numberMessage, useEnglishLocale } from './helpers'

test.describe('policy sandbox', () => {
  test.beforeEach(async ({ page }) => {
    await useEnglishLocale(page)
  })

  test('runs a simulation from the rules list and shows the result', async ({ page }) => {
    await page.goto('/sandbox')
    await expect(page.getByRole('main').getByRole('heading', { name: m('sandbox.title') })).toBeVisible()

    await page.getByLabel(m('sandbox.simulate')).first().click()

    await expect(page.getByRole('heading', { name: m('sandbox.simulationResult') })).toBeVisible()
    await expect(page.getByText(numberMessage('sandbox.edgesChecked'))).toBeVisible()
    await expect(page.getByText(numberMessage('sandbox.violationsFound'))).toBeVisible()
  })
})
