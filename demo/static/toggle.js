document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.delete-form');
  if (!form) return;

  // Elements
  const radios = form.querySelectorAll('input[type="radio"][name="quiz_id"]');
  const deleteBtn = document.getElementById('delete-btn');
  const checkbox = document.getElementById('delete-toggle-checkbox');
  const statusEl = document.getElementById('delete-mode-status');

  // function to toggle delete mode
  function setDeleteMode(on) {
    form.classList.toggle('delete-on', on);
    // Enable/disable radio buttons and delete button
    radios.forEach(r => {
      r.disabled = !on;
      if (!on) r.checked = false;
    });
    // Enable/disable delete button
    if (deleteBtn) deleteBtn.disabled = !on;
    // Update status text
    if (statusEl) statusEl.textContent = on ? 'Delete mode is ON' : 'Delete mode is OFF';
  }

  // Initialise state from checkbox
  setDeleteMode(checkbox?.checked ?? false);

  // Listen for toggle changes
  checkbox?.addEventListener('change', () => setDeleteMode(checkbox.checked));
});