document.addEventListener("DOMContentLoaded", function () {

    const modal     = document.getElementById("msgModal");
    const msgText   = document.getElementById("msgText");
    const msgTitle  = document.getElementById("msgTitle");
    const msgIcon   = document.getElementById("msgIcon");
    const msgCancel = document.getElementById("msgCancel");
    const msgOk     = document.getElementById("msgOk");

    const ICONS = {
        success: "fa-circle-check",
        error:   "fa-circle-xmark",
        warning: "fa-triangle-exclamation",
        info:    "fa-circle-info"
    };

    function showMessage(message, type, title, onOk) {

        type = type || "info";

        modal.classList.remove("msg-success", "msg-error", "msg-warning", "msg-info");
        modal.classList.add("msg-" + type);

        msgTitle.textContent = title || "Notice";
        msgText.textContent  = message;
        msgIcon.className    = "fas " + (ICONS[type] || ICONS.info);

        msgCancel.style.display = "none";
        msgOk.style.display     = "inline-flex";

        msgOk.onclick = function () {
            closeMessage();
            if (onOk) {
                onOk();
            }
        };

        modal.classList.add("show");
        document.body.classList.add("message-modal-open");
        msgOk.focus();
    }

    function closeMessage() {
        modal.classList.remove("show");
        document.body.classList.remove("message-modal-open");
    }

    // Esc or clicking the dark backdrop closes the message
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modal.classList.contains("show")) {
            closeMessage();
        }
    });

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeMessage();
        }
    });


    /* ---- retry a failed row ---- */

    document.addEventListener("click", async function (event) {

        const btn = event.target.closest(".retry-btn");

        if (!btn) {
            return;
        }

        btn.disabled = true;
        btn.classList.add("loading");

        try {
            const item = JSON.parse(btn.dataset.item);

            const res = await fetch("/api/items/create_singel_item_price", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(item)
            });

            const data = await res.json();

            if (res.ok) {
                showMessage(
                    data.message || "Price created successfully.",
                    "success",
                    "Success",
                    function () { location.reload(); }
                );
                return;
            }

            showMessage(data.message || "Retry failed. Please try again.", "error", "Retry Failed");

        } catch (err) {
            console.error("Retry error:", err);
            showMessage("Could not reach the server. Please try again.", "error", "Connection Error");
        }

        btn.disabled = false;
        btn.classList.remove("loading");
    });
});