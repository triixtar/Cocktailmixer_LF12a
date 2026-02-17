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
    const url = "http://127.0.0.1:5000/api/order";
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
    if (popup) {
        popup.classList.add("active");
    }
}

function closePopup() {
    const bgLayer = document.getElementById("bgLayer");
    const popups = bgLayer.querySelectorAll(".popup");

    popups.forEach(p => p.classList.remove("active"));
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
    const popup = document.getElementById("pinPopup");
    if (!popup) return;

    const dots = Array.from(popup.querySelectorAll('.dot'));
    const row = popup.querySelector('.numpad-row');
    let pin = "";
    let pinPurpose = null; // "alcohol" or "admin"
    let allCocktails = [];
    let currentFilter = null; //

    // === Backend-PINs ===
    const pins = { alcohol: null, admin: null };

    const update = () => {
        dots.forEach((d, i) => d.classList.toggle("filled", i < pin.length));
        if (pin.length === MAX) onPinComplete(pin);
    };

    const add = (d) => {
        if (pin.length >= MAX) return;
        pin += d;
        update();
    };

    const backspace = () => {
        if (pin) pin = pin.slice(0, -1);
        update();
    };

    row.addEventListener('click', (e) => {
        const btn = e.target.closest('.key');
        if (!btn) return;

        if (btn.classList.contains("back")) {
            backspace();
            return;
        }
        if (btn.classList.contains("close")) {
            return;
        }

        const d = btn.getAttribute('data-key');
        if (d) add(d);
    });

    function resetPinPopup() {
        pin = "";
        dots.forEach(d => d.classList.remove("filled"));
    }

    function showPinPopup(purpose) {
        pinPurpose = purpose;
        resetPinPopup();
        openPopup("pin");
    }

    async function onPinComplete(code) {
        try {
            const res = await fetch("http://127.0.0.1:5000/api/check-pin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pin: code, purpose: pinPurpose }) // <- wichtig
            });

            const data = await res.json();

            if (!data.valid) {
                notify({
                    title: "Zugriff verweigert",
                    message: "Der eingegebene PIN ist falsch.",
                    type: "error"
                });

                resetPinPopup();
                return;
            }

            if (pinPurpose === "alcohol") {
                closePopup();
                currentFilter = "alcoholic";
                renderCocktails();
                document.querySelectorAll('.selection').forEach(s => s.classList.remove('active'));
                document.querySelectorAll('.selection')[1].classList.add('active');
            } else if (pinPurpose === "admin") {
                window.location.href = "admin.html";
            }

        } catch (err) {
            console.error("PIN-Überprüfung fehlgeschlagen:", err.message);
            notify({
                title: "Serverfehler",
                message: "PIN konnte nicht überprüft werden.",
                type: "error"
            });
            resetPinPopup();
        }
    }


    // === Load Cocktails ===
    async function loadCocktails() {
        const url = "http://127.0.0.1:5000/api/cocktails";
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Response status: ${response.status}`);

            allCocktails = await response.json();
            renderCocktails();
        } catch (error) {
            console.error("Fehler beim Laden der Cocktails:", error.message);
        }
    }

    function renderCocktails() {
        const list = document.getElementById("cocktailList");
        list.innerHTML = "";

        if (!currentFilter) {
            list.innerHTML = `
            <div class="placeholder-message">
                <h1>Willkommen zum Cocktailmixer!</h1>
                <p>Bitte wähle eine Kategorie aus, um die Getränke anzuzeigen.</p>
            </div>
        `;
            return;
        }

        const filtered = allCocktails.filter(c => {
            if (currentFilter === "non-alcoholic") return !c.alkoholisch;
            if (currentFilter === "alcoholic") return c.alkoholisch;
            return true;
        });

        if (filtered.length === 0) {
            list.innerHTML = `<p style="text-align:center;color:#888;">Keine Getränke gefunden.</p>`;
            return;
        }

        filtered.forEach(cocktail => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.classList.add("drink-button");
            btn.onclick = () => openCocktailPopup(cocktail);

            btn.innerHTML = `
            <img class="drink-img" draggable="false"
                src="${cocktail.image_path || 'https://placehold.jp/3d4070/ffffff/128x128.png'}"
                alt="${cocktail.name}">
            <span>${cocktail.name}</span>
        `;
            list.appendChild(btn);
        });
    }

    document.querySelectorAll('.selection').forEach((sel, idx) => {
        sel.addEventListener('click', () => {
            document.querySelectorAll('.selection').forEach(s => s.classList.remove('active'));
            sel.classList.add('active');

            if (idx === 0) {
                currentFilter = "non-alcoholic";
                renderCocktails();
            } else {
                showPinPopup("alcohol");
            }
        });
    });

    document.querySelectorAll('.admin-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            showPinPopup("admin");
        });
    });

    function openCocktailPopup(cocktail) {
        const bgLayer = document.getElementById("bgLayer");
        const popup = bgLayer.querySelector(".popup-drink");

        popup.querySelector(".drink-img.big").src =
            cocktail.image_path || "https://placehold.jp/3d4070/ffffff/128x128.png";
        popup.querySelector(".drink-title").textContent = cocktail.name;
        popup.querySelector(".drink-description").textContent =
            cocktail.description || "Keine Beschreibung verfügbar.";

        const orderBtn = popup.querySelector("button[onclick]");
        orderBtn.onclick = () => orderCocktail(cocktail.id);

        openPopup("drink");
    }

    loadCocktails();
})();
