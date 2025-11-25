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
    // Add all elements with flip card to flip cards
    const flipCards = document.querySelectorAll('.flip-card');
    // For each flip card, add click event to toggle flipped class
    flipCards.forEach(card => {
        // On click, toggle flipped class
        card.addEventListener('click', function () {
            // flip the card
            card.classList.toggle('flipped');
        });
    });
});