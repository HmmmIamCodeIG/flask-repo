document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".js-toggle-prediction").forEach(button => {
        button.addEventListener("click", () => {
            const card = button.closest(".textbubble-dashboard");

            const prediction = card.querySelector(".dashboard-ml-prediction");
            const momentum = card.querySelector(".dashboard-momentum-rate");

            const isHidden = prediction?.hidden ?? true;

            if (prediction) {
                prediction.hidden = !isHidden;
            }

            if (momentum) {
                momentum.hidden = !isHidden;
            }

            button.textContent = isHidden
                ? "Hide Prediction"
                : "Show Prediction";

            button.setAttribute("aria-expanded", isHidden);
        });
    });
});