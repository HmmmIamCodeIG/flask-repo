window.addEventListener("load", () => {
    document
        .getElementById("loaderOverlay")
        .classList.add("loader-hidden");
});

window.addEventListener("load", () => { 
    const 
    loader = document.getElementById("loaderOverlay"); // Adds the fade-out class loader.classList.add("loader-hidden"); 
    setTimeout(() => {
        loader.style.display = "none"; // Hides the loader after the fade-out transition
    }, 500); // Duration of the fade-out transition in milliseconds
});

window.addEventListener("DOMContentLoaded", () => {
    const loader = document.getElementById("loaderOverlay");

    setTimeout(() => {
        document.querySelector(".loader-overlay").classList.add("loader-hidden");
        document.querySelector(".loader-overlay").style.display = "block";
    }, 500);
});