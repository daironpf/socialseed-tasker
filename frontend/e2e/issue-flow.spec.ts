import { test, expect } from '@playwright/test'

test.describe('issue flow', () => {
  test('creates an issue, opens it from the Kanban board and closes the detail panel', async ({ page }) => {
    await page.goto('/kanban')
    await expect(page.getByRole('main').getByRole('heading', { name: 'Kanban Board' })).toBeVisible()

    const title = `E2E test issue ${Date.now()}`
    await page.getByRole('button', { name: '+ New Issue' }).click()
    await expect(page.getByRole('heading', { name: 'Create Issue' })).toBeVisible()

    const form = page.locator('form')
    await form.locator('input').first().fill(title)
    await form.locator('select').nth(1).selectOption({ index: 1 })
    await form.getByRole('button', { name: 'Create', exact: true }).click()

    await expect(page.getByRole('heading', { name: 'Create Issue' })).toBeHidden()
    const card = page.getByText(title, { exact: true })
    await expect(card).toBeVisible()

    await card.click()
    const closeDetail = page.getByLabel('Close')
    await expect(closeDetail).toBeVisible()
    const detailPanel = page.locator('.fixed.inset-y-0.right-0')
    await expect(detailPanel.locator('input').first()).toHaveValue(title)

    await closeDetail.click()
    await expect(closeDetail).toBeHidden()
    await expect(card).toBeVisible()
  })

  test('lists existing issues on the board overview', async ({ page }) => {
    await page.goto('/board')
    await expect(page.getByText('Overview', { exact: true })).toBeVisible()
    await expect(page.getByRole('main')).toContainText(/\d/)
  })

  test('moves an issue between Kanban columns with drag and drop', async ({ page }) => {
    await page.goto('/kanban')
    await expect(page.getByRole('main').getByRole('heading', { name: 'Kanban Board' })).toBeVisible()

    const column = (name: string) =>
      page.getByRole('main').getByRole('heading', { name, exact: true }).locator('xpath=../..')
    const openColumn = column('Open')
    const blockedColumn = column('Blocked')

    const openBefore = await openColumn.locator('[draggable="true"]').count()
    const blockedBefore = await blockedColumn.locator('[draggable="true"]').count()
    expect(openBefore).toBeGreaterThan(0)

    const card = openColumn.locator('[draggable="true"]').first()
    await card.dragTo(blockedColumn)

    await expect(openColumn.locator('[draggable="true"]')).toHaveCount(openBefore - 1)
    await expect(blockedColumn.locator('[draggable="true"]')).toHaveCount(blockedBefore + 1)
  })
})
