const divbutton = document.querySelector('.custom-button');

const transactionDialog = document.getElementById('detailTransaction');
const transactionOpenBtn = document.getElementById('openTransactionDetail');
const transactionClsBtn = document.getElementById('closeTransactionDetail');

transactionOpenBtn.addEventListener('click', () => {
  transactionDialog.showModal();
});

transactionClsBtn.addEventListener('click', () => {
  transactionDialog.close();
});

transactionDialog.addEventListener('click', (e) => {
  const dialogDimensions = transactionDialog.getBoundingClientRect();
  if (
    e.clientX < dialogDimensions.left ||
    e.clientX > dialogDimensions.right ||
    e.clientY < dialogDimensions.top ||
    e.clientY > dialogDimensions.bottom
  ) {
    transactionDialog.close();
  }
});