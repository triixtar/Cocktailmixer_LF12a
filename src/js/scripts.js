document.querySelectorAll("button[data-action]").forEach(button => {
    button.addEventListener("click", () => {
        const action = button.dataset.action; // "drinkPopup" | "adminPopup"
        switch (action) {
            case "drinkPopup":
                openPopup("drink");
                break;
            case "adminPopup":
                openPopup("pin");
                break;
            default:
                console.warn("Unbekannte Action:", action);
        }
    });
});

async function getData() {
    const url = "http://127.0.0.1:5000/api/ingredients";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        console.log(result);
    } catch (error) {
        console.error(error.message);
    }
}
getData()

function openPopup(type) {
    const bgLayer = document.getElementById("bgLayer");
    const popups = bgLayer.querySelectorAll(".popup");
    popups.forEach(p => p.classList.remove("active"));
    bgLayer.classList.add("active");

    const popup = bgLayer.querySelector(`.popup-${type}`);
    if (popup) popup.classList.add("active");
}

function closePopup() {
    const bgLayer = document.getElementById("bgLayer");
    bgLayer.classList.remove("active");
}

const bgLayer = document.getElementById("bgLayer");
bgLayer.addEventListener("click", (event) => {
    if (event.target === bgLayer) {
        closePopup();
    }
});
