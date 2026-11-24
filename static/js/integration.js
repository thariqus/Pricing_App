document.addEventListener("DOMContentLoaded", function () {

    const API_URL    = "/api/items/integration_check";
    const DETAIL_URL = "/site-details/__CODE__";
    const STOP_URL   = "/api/stop_site";
    const START_URL  = "/api/start_site";
    const REFRESH_MS = 10 * 60 * 1000; // 10 minutes

    const linksEl    = document.getElementById("links");
    const stopAllBtn = document.getElementById("stop-all-btn");
    let loading = false;
    let reloadQueued = false;

    const ECG_PATH =
        "M0 15 H40 L45 12 L50 15 H56 L60 18 L65 3 L70 27 L74 15 H80 L86 11 L92 15 H120 L125 12 L130 15 H136 L140 18 L145 3 L150 27 L154 15 H160 L166 11 L172 15 H200";


    /* =====================================================
       RESPONSE ENVELOPE
       { response: { data, error, info, custom_fields, is_error } }

       If a reply has no "response" wrapper (an endpoint not yet
       migrated), the body itself is used, so both shapes work.
       ===================================================== */

    // Returns the inner "response" object, or the body itself if there's no wrapper
    function unwrapResponse(result) {
        return (result && result.response) ? result.response : (result || {});
    }

    // True when the reply should be treated as a failure
    function isFailed(ok, env) {
        return !ok || !!(env && env.is_error);
    }

    // Best human-readable error from an envelope
    function errorMessageOf(env, fallback) {
        const err = (env && env.error) || {};
        return err.error_message || err.error_details || (env && env.message) || fallback;
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

    // One site row
    function siteRow(ho, site) {
        const isActive  = Number(site.is_active ?? site.active) === 1;
        const rowStatus = isActive ? (site.status === "syncing" ? "syncing" : "connected") : "disconnected";
        const code      = esc(site.code);
        const detailUrl = DETAIL_URL.replace("__CODE__", encodeURIComponent(site.code));
        const action    = isActive ? "stop" : "start";

        return `
          <div class="link-row ${rowStatus}" data-code="${code}">
            <div class="node ho" title="${esc(ho.name)}">${esc(ho.code)}</div>

            <div class="site-title">
              <strong>${code}</strong>
            </div>

            <span class="flag-status">
              <svg class="flag" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path class="flag-pole" d="M5 3v18" />
                <path class="flag-cloth" d="M5 4h12l-2.5 4L17 12H5z" />
              </svg>
              <span class="flag-label">${isActive ? "Running" : "Stopped"}</span>
            </span>

            <a class="chevron" href="${detailUrl}" aria-label="Open site ${code}">&rsaquo;</a>

            <div class="wire ecg-wire">
              <svg class="ecg" viewBox="0 0 200 30" preserveAspectRatio="none" aria-hidden="true">
                <path class="ecg-base" pathLength="100" d="${ECG_PATH}" />
                <path class="ecg-pulse" pathLength="100" d="${ECG_PATH}" />
              </svg>
            </div>

            <div class="node site">${code}</div>

            <a class="info-btn" href="${detailUrl}" aria-label="Info for site ${code}">i</a>

            <button type="button" class="site-toggle ${action}"
                    data-action="${action}" data-code="${code}">
              <i class="fas fa-${isActive ? "stop" : "play"}"></i>
              ${isActive ? "Stop" : "Start"}
            </button>
          </div>`;
    }

    function render(data) {
        if (!data.sites || !data.sites.length) {
            linksEl.innerHTML = '<p class="loading-msg">No sites configured.</p>';
            updateStopAllBtn();
            return;
        }
        linksEl.innerHTML = data.sites.map(function (s) { return siteRow(data.head || {}, s); }).join("");
        updateStopAllBtn();
    }


    /* =====================================================
       STOP ALL / START ALL BUTTON
       Shows "Stop All" while any site is running,
       otherwise "Start All" when sites are stopped.
       ===================================================== */

    function updateStopAllBtn() {
        const runningCount = linksEl.querySelectorAll(".site-toggle.stop").length;
        const stoppedCount = linksEl.querySelectorAll(".site-toggle.start").length;
        const stopMode     = runningCount > 0;

        stopAllBtn.dataset.action = stopMode ? "stop" : "start";
        stopAllBtn.disabled       = runningCount + stoppedCount === 0;
        stopAllBtn.innerHTML = stopMode
            ? '<i class="fas fa-stop"></i> Stop All'
            : '<i class="fas fa-play"></i> Start All';
    }


    /* =====================================================
       LOAD
       ===================================================== */

    async function loadSites() {
        if (loading) {
            reloadQueued = true; // run again as soon as the current load finishes
            return;
        }
        loading = true;
        try {
            const res = await fetch(API_URL, { headers: { Accept: "application/json" } });

            let body = {};
            try {
                body = await res.json();
            } catch (e) {
                // no JSON body
            }

            const env = unwrapResponse(body);

            if (isFailed(res.ok, env)) {
                throw new Error(errorMessageOf(env, "HTTP " + res.status));
            }

            // head and sites are sent in custom_fields (see ho_to_store_integration).
            // Fall back to response.data, then to the flat shape.
            const custom = env.custom_fields || {};
            const data   = env.data || {};

            const payload =
                custom.sites !== undefined ? custom :
                (!Array.isArray(data) && data.sites !== undefined) ? data :
                env;

            render(payload);

        } catch (err) {
            console.error("Failed to load integration status:", err);
            // Keep the old rows if we have them; show an error only when nothing has loaded yet
            if (!linksEl.querySelector(".link-row")) {
                linksEl.innerHTML =
                    '<p class="loading-msg error">Could not load sites. Retrying in 10 minutes.</p>';
                updateStopAllBtn();
            }
        } finally {
            loading = false;
            if (reloadQueued) {
                reloadQueued = false;
                loadSites();
            }
        }
    }


    /* =====================================================
       START / STOP SITES
       ===================================================== */

    // Sends a list of site codes, e.g. ["2113", "2114"]
    async function setSitesActive(codes, action) {
        const url = action === "stop" ? STOP_URL : START_URL;

        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(codes)
        });

        let body = {};
        try {
            body = await res.json();
        } catch (e) {
            // no JSON body
        }

        const env = unwrapResponse(body);
        if (isFailed(res.ok, env)) {
            throw new Error(errorMessageOf(env, "HTTP " + res.status));
        }
    }

    // Single site: one row's button
    linksEl.addEventListener("click", async function (e) {
        const btn = e.target.closest(".site-toggle");
        if (!btn || btn.disabled) return;

        const code   = btn.dataset.code;
        const action = btn.dataset.action;

        btn.disabled = true;
        try {
            await setSitesActive([code], action);
            await loadSites(); // re-render so the button flips to the other state
        } catch (err) {
            console.error("Failed to " + action + " site " + code + ":", err);
            alert("Could not " + action + " site " + code + ": " + err.message);
            btn.disabled = false;
        }
    });

    // Stop All / Start All: acts on every site in the current state
    stopAllBtn.addEventListener("click", async function () {
        if (stopAllBtn.disabled) return;

        const action = stopAllBtn.dataset.action; // "stop" or "start"
        const codes  = Array.from(linksEl.querySelectorAll(".site-toggle." + action))
                            .map(function (b) { return b.dataset.code; });

        if (!codes.length) return;

        const verb = action === "stop" ? "Stop" : "Start";
        if (!confirm(verb + " all " + codes.length + " site(s)?")) return;

        stopAllBtn.disabled = true;
        try {
            await setSitesActive(codes, action);
            await loadSites(); // render() updates the button label and state
        } catch (err) {
            console.error("Failed to " + action + " all sites:", err);
            alert("Could not " + action + " all sites: " + err.message);
            stopAllBtn.disabled = false;
        }
    });


    loadSites();                        // once when the page opens
    setInterval(loadSites, REFRESH_MS); // then every 10 minutes, without reloading the page
});