import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('shows READY evidence and UNBOUND binding without preselected decision', async ({ page }) => {
  const writeMethods: string[] = [];
  page.on('request', (request) => {
    if (!['GET', 'HEAD'].includes(request.method())) writeMethods.push(request.method());
  });

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Verifica associazione schema di armatura' })).toBeVisible();
  await expect(page.getByText('Geometria verificata')).toBeVisible();
  await expect(page.getByText('Non determinato', { exact: true })).toBeVisible();
  await expect(page.getByText('Fonte verificata')).toBeVisible();

  const radios = page.getByRole('radio');
  await expect(radios).toHaveCount(5);
  for (let i = 0; i < 5; i += 1) await expect(radios.nth(i)).not.toBeChecked();

  await page.getByRole('button', { name: 'Provenienza tecnica' }).click();
  await expect(page.getByText('CEW-N12-REG-T6A-G03')).toBeVisible();

  expect(writeMethods).toEqual([]);
});

test('creates only a non-promotive receipt proposal', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('radio', { name: /Associazione non determinabile/ }).click();
  await page.getByLabel('Revisore').fill('Revisore tecnico');
  await page.getByLabel('Osservazione tecnica').fill('La fonte è leggibile ma non consente un binding strutturale affidabile.');
  await page.getByRole('button', { name: 'Prepara ricevuta di decisione' }).click();

  const preview = page.getByTestId('proposal-preview');
  await expect(preview).toContainText('NON_PROMOTIVE_HUMAN_DECISION_PROPOSAL');
  await expect(preview).toContainText('"canonical_write": false');
  await expect(preview).toContainText('"outcome": "UNBOUND"');
});

test('has no serious accessibility violations in the verified review state', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .disableRules(['color-contrast'])
    .analyze();
  expect(results.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''))).toEqual([]);
});
