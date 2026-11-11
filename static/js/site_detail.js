document.addEventListener("DOMContentLoaded", function () {

    const container  = document.getElementById("detail");
    const SITE_CODE  = container.dataset.site;

    const API_LOAD   = "/api/items/site_details/";
    const API_SAVE   = "/api/items/create_singel_item_price";

    const tableBody  = document.getElementById("detailBody");
    const totalEl    = document.getElementById("totalCount");
    const failedEl   = document.getElementById("failedCount");

    const modal      = document.getElementById("msgModal");
    const msgText    = document.getElementById("msgText");
    const msgTitle   = document.getElementById("msgTitle");
    const msgIcon    = document.getElementById("msgIcon");
    const msgCancel  = document.getElementById("msgCancel");
    const msgOk      = document.getElementById("msgOk");

    const COLUMN_COUNT = 28;

    // Data keys for the columns between "Sl No" and "Status", in header order
    const FIELDS = [
        "item_no", "condition_type", "active", "change_type",
        "customer", "customer_grp", "customer_hierarchy",
        "distribution_channel_code", "location_code", "currency",
        "sales_price", "uom", "minimum_quantity", "priority",
        "starting_date", "ending_date", "lower_limit", "upper_limit",
        "map", "offer_article", "price_with_tax", "tax_percent",
        "transportation_zone_code", "updated_from_sap", "created", "updated"
    ];

    const FAILED_STATUSES = ["failed", "faild", "fail"];

    const ICONS = {
        success: "fa-circle-check",
        error:   "fa-circle-xmark",
        warning: "fa-triangle-exclamation",
        info:    "fa-circle-info"
    };

    let rows = [];   // records from the last load, used by the retry button


    /* =====================================================
       RESPONSE ENVELOPE
       { response: { data, error, info, custom_fields, is_error } }

       If a reply has no "response" wrapper, the body itself is used.
       ===================================================== */

    function unwrapResponse(body) {
        return (body && body.response) ? body.response : (body || {});
    }

    function isFailed(ok, env) {
        return !ok || !!(env && env.is_error);
    }

    function errorMessageOf(env, fallback) {
        const err = (env && env.error) || {};
        return err.error_message || err.error_details || (env && env.message) || fallback;
    }

    function successMessageOf(env, fallback) {
        const info = (env && env.info) || {};
        return info.success_message || (env && env.message) || fallback;
    }

    // Calls the server and resolves with { ok, env }
    async function callApi(url, options) {
        const response = await fetch(url, options);
        let env = {};
        try {
            env = unwrapResponse(await response.json());
        } catch (e) {
            // no JSON body
        }
        return { ok: response.ok, env: env };
    }


    /* =====================================================
       HELPERS
       ===================================================== */

    // Escape text before putting it into HTML
    function esc(value) {
        const d = document.createElement("div");
        d.textContent = value ?? "";
        return d.innerHTML;
    }

    function isRowFailed(item) {
        return FAILED_STATUSES.indexOf(String(item.status ?? "").toLowerCase()) !== -1;
    }

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


    /* =====================================================
       RENDER
       ===================================================== */

    function rowHtml(item, index) {

        const failed = isRowFailed(item);

        let html = '<tr class="' + (failed ? "failed" : "") + '">';

        html += "<td>" + (index + 1) + "</td>";

        FIELDS.forEach(function (key) {
            html += "<td>" + esc(item[key]) + "</td>";
        });

        html +=
            "<td>" +
                '<div class="status-cell">' +
                    '<span class="badge">' + esc(item.status) + "</span>" +
                    (failed
                        ? '<button type="button" class="retry-btn" data-index="' + index + '">' +
                              '<i class="fas fa-rotate-right"></i> Retry' +
                          "</button>"
                        : "") +
                "</div>" +
            "</td>";

        html += "</tr>";

        return html;
    }

    function showStateRow(text, isError) {
        tableBody.innerHTML =
            '<tr><td colspan="' + COLUMN_COUNT + '" class="empty"' +
            (isError ? ' style="color:#c0392b;"' : "") + ">" +
            esc(text) + "</td></tr>";
    }

    function renderRows() {

        totalEl.textContent  = rows.length;
        failedEl.textContent = rows.filter(isRowFailed).length;

        if (rows.length === 0) {
            showStateRow("No records found.", false);
            return;
        }

        tableBody.innerHTML = rows.map(rowHtml).join("");
    }


    /* =====================================================
       LOAD
       ===================================================== */

    async function loadItems() {

        showStateRow("Loading…", false);

        try {
            const res = await callApi(API_LOAD + encodeURIComponent(SITE_CODE));

            if (isFailed(res.ok, res.env)) {
                const message = errorMessageOf(res.env, "Could not load records.");
                showStateRow(message, true);
                return;
            }

            rows = res.env.data || [];
            renderRows();

        } catch (err) {
            console.error("Load error:", err);
            showStateRow("Could not reach the server.", true);
        }
    }


    /* =====================================================
       RETRY A FAILED ROW
       ===================================================== */

    tableBody.addEventListener("click", async function (event) {

        const btn = event.target.closest(".retry-btn");

        if (!btn) {
            return;
        }

        const item = rows[Number(btn.dataset.index)];

        if (!item) {
            return;
        }

        btn.disabled = true;
        btn.classList.add("loading");

        try {
            const res = await callApi(API_SAVE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(item)
            });

            if (isFailed(res.ok, res.env)) {
                showMessage(
                    errorMessageOf(res.env, "Retry failed. Please try again."),
                    "error",
                    "Retry Failed"
                );
                btn.disabled = false;
                btn.classList.remove("loading");
                return;
            }

            showMessage(
                successMessageOf(res.env, "Price created successfully."),
                "success",
                "Success",
                function () { loadItems(); }
            );

        } catch (err) {
            console.error("Retry error:", err);
            showMessage("Could not reach the server. Please try again.", "error", "Connection Error");
            btn.disabled = false;
            btn.classList.remove("loading");
        }
    });


    /* =====================================================
       BOOT
       ===================================================== */

    loadItems();
});