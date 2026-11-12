(function () {
    const tbody = document.getElementById("logTbody");
    const totalCount = document.getElementById("totalCount");
    const visibleCount = document.getElementById("visibleCount");
    const endpoint = tbody.dataset.endpoint;
    const COLSPAN = 11;

    function esc(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (c) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[c];
        });
    }

    function flag(on, kind) {
        if (!on) {
            return '<span class="flag-badge off">No</span>';
        }
        const icon = kind === "error" ? "fa-circle-xmark" : "fa-circle-info";
        return `<span class="flag-badge ${kind}"><i class="fas ${icon}"></i> Yes</span>`;
    }

    function rowHtml(log) {
        return `
            <tr class="${log.error ? "row-error" : ""}">
                <td class="id-cell">${esc(log.id)}</td>
                <td class="message-cell">${esc(log.custom_message)}</td>
                <td class="message-cell">${esc(log.response_message)}</td>
                <td>${esc(log.source)}</td>
                <td>${esc(log.type)}</td>
                <td>${esc(log.site_details)}</td>
                <td><span class="code-badge">${esc(log.message_code)}</span></td>
                <td><span class="status-badge">${esc(log.log_status)}</span></td>
                <td class="flag-cell">${flag(log.info, "info")}</td>
                <td class="flag-cell">${flag(log.error, "error")}</td>
                <td class="date-cell">${esc(log.created_at)}</td>
            </tr>`;
    }

    function showStatus(text) {
        tbody.innerHTML = `<tr><td colspan="${COLSPAN}" class="empty-message">${esc(text)}</td></tr>`;
    }

    function render(logs) {
        totalCount.textContent = logs.length;
        visibleCount.textContent = logs.length;

        if (logs.length === 0) {
            showStatus("No log messages found.");
            return;
        }
        tbody.innerHTML = logs.map(rowHtml).join("");
    }

    async function loadLogs() {
        showStatus("Loading...");
        try {
            const response = await fetch(endpoint, {
                headers: { "Accept": "application/json" }
            });
            const body = await response.json();
            const result = body.response;

            if (!response.ok || !result || result.is_error) {
                const err = (result && result.error) || {};
                const detail = err.error_details ? ` (${err.error_details})` : "";
                throw new Error((err.error_message || `HTTP ${response.status}`) + detail);
            }

            render(result.data);
        } catch (err) {
            showStatus(`Failed to load logs: ${err.message}`);
        }
    }

    loadLogs();
})();