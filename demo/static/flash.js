let count = 1;
// Add new flashcard entry
document.getElementById('add-flashcard-btn').onclick = function() {
    count++;
    // add a new container div with question and answer inputs
    const container = document.getElementById('flashcards-container');
    // enter the new div before the add button
    const entry = document.createElement('div');
    entry.className = 'flashcard-entry';
    entry.innerHTML = `
        <label>Question ${count}:</label>
        <input type="text" name="questions[]" required>
        <label>Answer ${count}:</label>
        <input type="text" name="answers[]" required>
    `;
    container.appendChild(entry);
};

// Flip flashcard on click
document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('.flashcard-sets').addEventListener('click', function (e) {
        const card = e.target.closest('.flip-card');
        if (card) {
            card.classList.toggle('flipped');
        }
    });
});