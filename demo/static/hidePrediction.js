document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".js-toggle-prediction").forEach((button) => {
        button.addEventListener("click", () => {
            const predictionBlock = button.previousElementSibling;

            if (!predictionBlock) {
                return;
            }

            const isHidden = predictionBlock.hasAttribute("hidden");

            if (isHidden) {
                predictionBlock.removeAttribute("hidden");
                button.textContent = "Hide Prediction";
                button.setAttribute("aria-expanded", "true");
            } else {
                predictionBlock.setAttribute("hidden", "");
                button.textContent = "Show Prediction";
                button.setAttribute("aria-expanded", "false");
            }
        });
    });
});