(function () {
    const host = document.getElementById("alertHost");
    const template = document.getElementById("alertTemplate");

    if (!host || !template) {
        console.warn("Alert Host oder Template fehlt.");
        return;
    }

    function mountAlert({ title, message, type = "info" }) {
        const node = template.content.cloneNode(true);
        const alertEl = node.querySelector(".app-alert");

        // type setzen
        alertEl.classList.remove("app-alert--info", "app-alert--success", "app-alert--warning", "app-alert--error");
        alertEl.classList.add(`app-alert--${type}`);

        node.querySelector(".app-alert__title").textContent = title;
        node.querySelector(".app-alert__message").textContent = message;

        host.appendChild(node);
        return alertEl;
    }

    // ===== Toast / Notify =====
    function notify({ title, message, type = "info", timeout = 4000 }) {
        const alertEl = mountAlert({ title, message, type });

        const remove = () => {
            alertEl.style.opacity = "0";
            alertEl.style.transform = "translateY(6px)";
            setTimeout(() => alertEl.remove(), 150);
        };

        alertEl.querySelector(".app-alert__close")?.addEventListener("click", remove);

        if (timeout) setTimeout(remove, timeout);
    }

    // ===== Confirm Dialog (Promise) =====
    function confirmDialog({
                               title,
                               message,
                               type = "warning",
                               confirmText = "Bestätigen",
                               cancelText = "Abbrechen",
                           }) {
        return new Promise((resolve) => {
            const alertEl = mountAlert({ title, message, type });

            // X entfernen, damit User explizit entscheidet
            alertEl.querySelector(".app-alert__close")?.remove();

            const content = alertEl.querySelector(".app-alert__content");

            const actions = document.createElement("div");
            actions.className = "app-alert__actions";

            const ok = document.createElement("button");
            ok.type = "button";
            ok.className = "save-btn";
            ok.textContent = confirmText;

            const cancel = document.createElement("button");
            cancel.type = "button";
            cancel.className = "sort-btn";
            cancel.textContent = cancelText;

            actions.appendChild(ok);
            actions.appendChild(cancel);
            content.appendChild(actions);

            const cleanup = () => alertEl.remove();

            ok.addEventListener("click", () => {
                cleanup();
                resolve(true);
            });
            cancel.addEventListener("click", () => {
                cleanup();
                resolve(false);
            });
        });
    }

    // ===== Number Prompt (Promise) =====
    function promptNumberDialog({
                                    title,
                                    message,
                                    type = "info",
                                    placeholder = "",
                                    confirmText = "OK",
                                    cancelText = "Abbrechen",
                                    min = null,
                                    max = null,
                                    allowDecimal = false,  // falls ihr später 12.5 braucht
                                    maxLen = 6             // z.B. 2000 -> reicht locker
                                }) {
        return new Promise((resolve) => {
            const alertEl = mountAlert({ title, message, type });

            // X entfernen (User soll bewusst OK/Abbrechen drücken)
            alertEl.querySelector(".app-alert__close")?.remove();

            const content = alertEl.querySelector(".app-alert__content");

            // Anzeige (anstatt input)
            const display = document.createElement("div");
            display.className = "app-alert__display";
            display.setAttribute("aria-label", "Eingabe");
            display.textContent = placeholder;

            // Numpad (look & feel wie PIN-Numpad)
            const pad = document.createElement("div");
            pad.className = "numpad-row"; // gleiche Klasse wie in eurer PIN UI :contentReference[oaicite:2]{index=2}
            pad.setAttribute("role", "group");
            pad.setAttribute("aria-label", "Ziffernblock");

            // Buttons (1-9)
            const keys = ["1","2","3","4","5","6","7","8","9"];
            keys.forEach(k => {
                const b = document.createElement("button");
                b.type = "button";
                b.className = "key";
                b.dataset.key = k;
                b.textContent = k;
                pad.appendChild(b);
            });

            // optional decimal
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = "key";
            dot.dataset.key = ".";
            dot.textContent = ".";
            dot.style.opacity = allowDecimal ? "1" : "0";
            dot.style.pointerEvents = allowDecimal ? "auto" : "none";

            // 0
            const zero = document.createElement("button");
            zero.type = "button";
            zero.className = "key";
            zero.dataset.key = "0";
            zero.textContent = "0";

            // backspace (wie bei PIN "back")
            const back = document.createElement("button");
            back.type = "button";
            back.className = "key back";
            back.textContent = "←";

            pad.appendChild(dot);
            pad.appendChild(zero);
            pad.appendChild(back);

            // Action Buttons (OK / Abbrechen) im selben Stil wie eure Admin Buttons
            const actions = document.createElement("div");
            actions.className = "app-alert__actions";

            const ok = document.createElement("button");
            ok.type = "button";
            ok.className = "save-btn";
            ok.textContent = confirmText;

            const cancel = document.createElement("button");
            cancel.type = "button";
            cancel.className = "sort-btn";
            cancel.textContent = cancelText;

            actions.appendChild(ok);
            actions.appendChild(cancel);

            content.appendChild(display);
            content.appendChild(pad);
            content.appendChild(actions);

            let valueStr = "";

            const render = () => {
                display.textContent = valueStr || placeholder || " ";
                display.classList.toggle("is-empty", !valueStr);
            };

            const addChar = (c) => {
                if (valueStr.length >= maxLen) return;

                // Decimal-Regeln
                if (c === ".") {
                    if (!allowDecimal) return;
                    if (valueStr.includes(".")) return;
                    if (valueStr === "") valueStr = "0";
                }

                valueStr += c;
                render();
            };

            const backspace = () => {
                valueStr = valueStr.slice(0, -1);
                render();
            };

            pad.addEventListener("click", (e) => {
                const btn = e.target.closest(".key");
                if (!btn) return;

                if (btn.classList.contains("back")) {
                    backspace();
                    return;
                }

                const k = btn.dataset.key;
                if (k) addChar(k);
            });

            const cleanup = () => alertEl.remove();

            const submit = () => {
                const n = allowDecimal ? Number(valueStr) : parseInt(valueStr, 10);

                if (!valueStr || Number.isNaN(n)) {
                    notify({ title: "Ungültige Eingabe", message: "Bitte eine Zahl eingeben.", type: "error" });
                    return;
                }
                if (min !== null && n < min) {
                    notify({ title: "Zu klein", message: `Bitte mindestens ${min} eingeben.`, type: "error" });
                    return;
                }
                if (max !== null && n > max) {
                    notify({ title: "Zu groß", message: `Bitte maximal ${max} eingeben.`, type: "error" });
                    return;
                }

                cleanup();
                resolve(n);
            };

            ok.addEventListener("click", submit);
            cancel.addEventListener("click", () => {
                cleanup();
                resolve(null);
            });

            render();
        });
    }


    // Global verfügbar
    window.notify = notify;
    window.confirmDialog = confirmDialog;
    window.promptNumberDialog = promptNumberDialog;
})();
