document.addEventListener("DOMContentLoaded", function () {

    const API_URL    = "/api/items/integration_check";
    const DETAIL_URL = "/site-details/__CODE__";
    const REFRESH_MS = 10 * 60 * 1000; // 10 minutes

    const linksEl = document.getElementById("links");
    let loading = false;

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
        const stopped   = site.status === "disconnected";
        const code      = esc(site.code);
        const detailUrl = DETAIL_URL.replace("__CODE__", encodeURIComponent(site.code));

        return `
          <div class="link-row ${esc(site.status)}" data-code="${code}">
            <div class="node ho" title="${esc(ho.name)}">${esc(ho.code)}</div>

            <div class="site-title">
              <strong>${code}</strong>
            </div>

            <span class="flag-status">
              <svg class="flag" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path class="flag-pole" d="M5 3v18" />
                <path class="flag-cloth" d="M5 4h12l-2.5 4L17 12H5z" />
              </svg>
              <span class="flag-label">${stopped ? "Stopped" : "Running"}</span>
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
          </div>`;
    }

    function render(data) {
        if (!data.sites || !data.sites.length) {
            linksEl.innerHTML = '<p class="loading-msg">No sites configured.</p>';
            return;
        }
        linksEl.innerHTML = data.sites.map(function (s) { return siteRow(data.head || {}, s); }).join("");
    }


    /* =====================================================
       LOAD
       ===================================================== */

    async function loadSites() {
        if (loading) return; // skip if the previous call is still running
        loading = true;
        try {
            const res = await fetch(API_URL, { headers: { Accept: "application/json" } });

            // read the body first: an error reply still carries error details
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
            }
        } finally {
            loading = false;
        }
    }

    loadSites();                        // once when the page opens
    setInterval(loadSites, REFRESH_MS); // then every 10 minutes, without reloading the page
});