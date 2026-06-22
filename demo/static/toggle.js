document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.delete-form');
  if (!form) return;

  // elements
  const radios = form.querySelectorAll('input[type="radio"][name="quiz_id"]');
  const deleteBtn = document.getElementById('delete-btn');
  const checkbox = document.getElementById('delete-toggle-checkbox');
  const statusEl = document.getElementById('delete-mode-status');
  const cards = form.querySelectorAll('.quiz-card');

  // function to set delete mode
  function setDeleteMode(on) {
    form.classList.toggle('delete-on', on);
    radios.forEach(r => {
      r.disabled = !on; // enable only in delete mode
      if (!on) r.checked = false;
    });
    deleteBtn.disabled = !on;
    statusEl.textContent = on ? 'Delete mode is ON' : 'Delete mode is OFF';
  }

  // card click behavior
  cards.forEach(card => {
    card.addEventListener('click', e => {
      const radio = card.querySelector('input[type="radio"][name="quiz_id"]');
      if (!radio) return;
      if (form.classList.contains('delete-on')) {
        // select for deletion
        radio.checked = true;
      } else {
        // navigate to take the quiz
        const id = radio.value;
        if (id) {
          window.location.href = `/quizzes?quiz_id=${id}`;
        }
      }
    });
  });

  setDeleteMode(checkbox?.checked ?? false);
  checkbox?.addEventListener('change', () => setDeleteMode(checkbox.checked));
});
