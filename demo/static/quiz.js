document.addEventListener("DOMContentLoaded", () => {
    const radios = document.querySelectorAll('input[type="radio"]');

    radios.forEach(radio => {
        radio.addEventListener("click", (event) => {
            // Find parent .question-block
            let questionBlock = radio.closest(".question-block");
            // Get all radios in this question block
            let groupRadios = questionBlock.querySelectorAll('input[type="radio"]');
            // If this radio was already checked, uncheck it
            if (radio.dataset.waschecked === "true") {
                radio.checked = false;
                radio.dataset.waschecked = "false";
                radio.classList.add("temp-unchecked");
                return;
            }
            //  Else, mark this as checked and others as unchecked
            groupRadios.forEach(r => {
                r.dataset.waschecked = "false";
                r.classList.remove("temp-unchecked");
            });
            radio.dataset.waschecked = "true";
        });
    });
});
