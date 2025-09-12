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
async function orderCocktail(cocktailId) {
    const url = "http://127.0.0.1:5000/order";
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ cocktail_id: cocktailId })
        });

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Order Response:", result);

    } catch (error) {
        console.error("Order failed:", error.message);
    }
}

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

// PIN Logik
(function () {
    const MAX = 4;
    const popup = document.getElementById('pinPopup');
    if (!popup) return;

    const dots = Array.from(popup.querySelectorAll('.dot'));
    const input = popup.querySelector('#pinInput');
    const row = popup.querySelector('.numpad-row');

    let pin = '';

    const update = () => {
        dots.forEach((d, i) => d.classList.toggle('filled', i < pin.length));
        if (input) input.value = pin;
        if (pin.length === MAX) onPinComplete(pin);
    };

    const add = (d) => {
        if (pin.length >= MAX) return;
        pin += d;
        update();
    };

    // optional „Korrigieren“: auf die Punkte tippen = ein Zeichen löschen
    const backspace = () => { if (pin) { pin = pin.slice(0, -1); update(); } };
    popup.querySelector('.pin-dots')?.addEventListener('click', backspace);

    row.addEventListener('click', (e) => {
        const btn = e.target.closest('.key');
        if (!btn) return;
        const d = btn.getAttribute('data-key');
        if (d) add(d);
    });

    // Hook: hier definierst du, was nach 4 Ziffern passieren soll
    function onPinComplete(code) {
        // TODO: prüfe hier gegen Backend / Konfiguration
        console.log('PIN eingegeben:', code);
        // Beispiel: Popups schließen + weiter
        // closePopup();
        // doSomething();
    }
})();

