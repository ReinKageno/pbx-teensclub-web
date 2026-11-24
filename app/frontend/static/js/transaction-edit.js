(() => {
  const dialog = document.querySelector('.transaction-dialog');
  if (!dialog) return;

  const details = dialog.querySelector('.detail-grid');
  const viewActions = dialog.querySelector('#transaction-view-actions');
  const form = dialog.querySelector('#transaction-edit-form');
  const errorMessage = form.querySelector('.edit-error');
  const issuerInput = form.elements.issuer;
  const issuerAccountNote = form.querySelector('.issuer-account-note');
  const amountInput = form.elements.amount;
  const descriptionInput = form.elements.description;
  const paymentMethodInput = form.elements.payment_method;
  const typeInput = form.elements.type;
  const statusInput = form.elements.status;

  const selectRow = (row) => {
    dialog.dataset.transactionId = row.dataset.id;
    issuerInput.value = row.dataset.issuer || '';
    const issuerIsLinked = row.dataset.issuerEditable === 'false';
    issuerInput.disabled = issuerIsLinked;
    issuerAccountNote.hidden = !issuerIsLinked;
    amountInput.value = row.dataset.amountRaw || '';
    descriptionInput.value = row.dataset.description || '';
    paymentMethodInput.value = row.dataset.payment || '';
    typeInput.value = (row.dataset.type || 'income').toLowerCase();
    statusInput.value = (row.dataset.status || 'pending').toLowerCase();
    errorMessage.textContent = '';
  };

  // Capture row activation before the details handler opens the dialog.
  document.addEventListener('click', (event) => {
    const row = event.target.closest?.('.transaction-row');
    if (row) selectRow(row);
  }, true);
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const row = event.target.closest?.('.transaction-row');
    if (row) selectRow(row);
  }, true);

  dialog.querySelector('#edit-transaction-button').addEventListener('click', () => {
    viewActions.hidden = true;
    details.hidden = true;
    form.hidden = false;
    issuerInput.focus();
  });

  dialog.querySelector('#cancel-transaction-edit').addEventListener('click', () => {
    form.hidden = true;
    details.hidden = false;
    viewActions.hidden = false;
  });
  dialog.addEventListener('close', () => {
    form.hidden = true;
    details.hidden = false;
    viewActions.hidden = false;
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const saveButton = form.querySelector('[type="submit"]');
    saveButton.disabled = true;
    errorMessage.textContent = '';
    try {
      const response = await fetch(`/donation/${encodeURIComponent(dialog.dataset.transactionId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: Number(amountInput.value),
          description: descriptionInput.value,
          payment_method: paymentMethodInput.value.trim(),
          type: typeInput.value,
          status: statusInput.value,
          ...(!issuerInput.disabled ? { issuer: issuerInput.value.trim() } : {}),
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Unable to save transaction changes.');
      }
      window.location.reload();
    } catch (error) {
      errorMessage.textContent = error.message;
    } finally {
      saveButton.disabled = false;
    }
  });
})();
