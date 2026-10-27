document.addEventListener("DOMContentLoaded", function () {

    const form            = document.getElementById("settings-form");
    const centralCheckbox = document.getElementById("is_central_box");
    const sitesCard       = document.getElementById("sites-card");
    const sitesBody       = document.getElementById("sites-body");
    const newRowTemplate  = document.getElementById("site-row");       // empty row (not in DB yet)
    const dbRowTemplate   = document.getElementById("site-row-db");    // row loaded from DB
    const addRowButton    = document.getElementById("add-row-btn");
    const saveButton      = document.getElementById("save-btn");
    const messageBox      = document.getElementById("settings-msg");

    // edit modal
    const modal           = document.getElementById("site-edit-modal");
    const editLocation    = document.getElementById("edit-location");
    const editIp          = document.getElementById("edit-ip");
    const editActive      = document.getElementById("edit-active");
    const editError       = document.getElementById("edit-error");
    const editSaveButton  = document.getElementById("edit-save");
    const editCancelBtn   = document.getElementById("edit-cancel");
    const editCloseBtn    = document.getElementById("edit-close");

    // change these to your real Flask routes
    const SAVE_URL   = "/api/add_site_settings";       // POST   { sites: [...] }
    const GET_URL    = "/api/get_all_sites";           // GET    -> { sites: [...] }
    const UPDATE_URL = "/api/update_site/";            // PUT    + id
    const DELETE_URL = "/api/delete_site/";            // DELETE + id

    let editingRow   = null;
    let messageTimer = null;


    /* =====================================================
       HELPERS
       ===================================================== */

    function isCentral() {
        return centralCheckbox.value === "1";
    }

    function toBool(value) {
        return value === true || value === 1 || value === "1" || value === "true";
    }

    // maps a database row ({site_location, site_ip, ...}) to what the page uses
    function normalizeSite(row) {
        return {
            id:       row.id,
            location: row.site_location !== undefined ? row.site_location : row.location,
            ip:       row.site_ip !== undefined ? row.site_ip : row.ip,
            active:   row.active
        };
    }

    async function api(url, options) {
        const response = await fetch(url, options);
        let data = {};
        try {
            data = await response.json();
        } catch (e) {
            // response had no JSON body
        }
        return { ok: response.ok, data: data };
    }

    function showMessage(text, isError) {
        messageBox.textContent = text;
        messageBox.hidden = false;
        messageBox.classList.toggle("error", !!isError);
        messageBox.classList.toggle("ok", !isError);

        clearTimeout(messageTimer);
        if (!isError) {
            messageTimer = setTimeout(function () {
                messageBox.hidden = true;
            }, 4000);
        }
    }

    // pressing Enter inside an input must not submit / reload the page
    form.addEventListener("submit", function (event) {
        event.preventDefault();
    });


    /* ---- show Sites only for the central app ---- */

    function toggleSites() {
        sitesCard.hidden = !isCentral();
    }


    /* ---- Sl No ---- */

    function renumber() {
        sitesBody.querySelectorAll("tr").forEach(function (row, index) {
            row.querySelector(".sl").textContent = index + 1;
        });
    }


    /* ---- always keep at least one row on screen ---- */

    function ensureOneRow() {
        if (sitesBody.children.length === 0) {
            addRow(false);
        }
        renumber();
    }


    /* =====================================================
       ROWS
       ===================================================== */

    /* ---- new (unsaved) row: inputs + delete icon only ---- */

    function addRow(focus) {
        const row = newRowTemplate.content.firstElementChild.cloneNode(true);
        sitesBody.appendChild(row);
        renumber();
        if (focus) {
            row.querySelector(".site-location").focus();
        }
    }

    addRowButton.addEventListener("click", function () {
        addRow(true);
    });


    /* ---- saved row (from database): text + edit & delete icons ---- */

    function fillDbRow(row, site) {
        row.dataset.id       = site.id;
        row.dataset.location = site.location;
        row.dataset.ip       = site.ip;
        row.dataset.active   = toBool(site.active) ? "1" : "0";

        row.querySelector(".view-location").textContent = site.location;
        row.querySelector(".view-ip").textContent       = site.ip;
        row.querySelector(".view-active").checked       = toBool(site.active);
    }

    function createDbRow(site) {
        const row = dbRowTemplate.content.firstElementChild.cloneNode(true);
        fillDbRow(row, site);
        return row;
    }


    /* ---- load every site from the database ---- */

    async function loadSites() {

        if (!isCentral()) {
            return;
        }

        try {
            const res = await api(GET_URL);

            if (!res.ok) {
                showMessage(res.data.message || "Could not load sites.", true);
            }

            const raw  = Array.isArray(res.data) ? res.data : (res.data.data || res.data.sites || []);
            const list = raw.map(normalizeSite);

            sitesBody.innerHTML = "";

            list.forEach(function (site) {
                sitesBody.appendChild(createDbRow(site));
            });

        } catch (err) {
            console.error(err);
            showMessage("Could not reach the server.", true);
        }

        // no data -> behave like before: one empty row to type into
        ensureOneRow();
    }


    /* =====================================================
       ROW BUTTONS (remove / delete / edit)
       ===================================================== */

    sitesBody.addEventListener("click", function (event) {

        const removeBtn = event.target.closest(".remove-row-btn");   // new row -> just remove from screen
        const deleteBtn = event.target.closest(".delete-site-btn");  // saved row -> delete from DB
        const editBtn   = event.target.closest(".edit-site-btn");    // saved row -> open modal

        if (removeBtn) {
            removeBtn.closest("tr").remove();
            ensureOneRow();
            return;
        }

        if (deleteBtn) {
            deleteSite(deleteBtn.closest("tr"));
            return;
        }

        if (editBtn) {
            openEditModal(editBtn.closest("tr"));
        }
    });


    /* ---- delete from database ---- */

    async function deleteSite(row) {

        if (!confirm("Delete this site from the database?")) {
            return;
        }

        try {
            const res = await api(DELETE_URL + encodeURIComponent(row.dataset.id), {
                method: "DELETE"
            });

            if (res.ok) {
                row.remove();
                ensureOneRow();
                showMessage(res.data.message || "Site deleted.", false);
            } else {
                showMessage(res.data.message || "Delete failed.", true);
            }

        } catch (err) {
            console.error(err);
            showMessage("Could not reach the server.", true);
        }
    }


    /* =====================================================
       EDIT MODAL
       ===================================================== */

    function openEditModal(row) {
        editingRow = row;

        editLocation.value = row.dataset.location;
        editIp.value       = row.dataset.ip;
        editActive.checked = row.dataset.active === "1";

        editError.hidden = true;
        modal.hidden = false;
        editLocation.focus();
    }

    function closeEditModal() {
        modal.hidden = true;
        editingRow = null;
    }

    editCancelBtn.addEventListener("click", closeEditModal);
    editCloseBtn.addEventListener("click", closeEditModal);

    // click on the dark backdrop closes it
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeEditModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !modal.hidden) {
            closeEditModal();
        }
    });

    function showEditError(text) {
        editError.textContent = text;
        editError.hidden = false;
    }

    editSaveButton.addEventListener("click", async function () {

        if (!editingRow) {
            return;
        }

        const site = {
            id:       editingRow.dataset.id,
            location: editLocation.value.trim(),
            ip:       editIp.value.trim(),
            active:   editActive.checked
        };

        if (!site.location || !site.ip) {
            showEditError("Location and IP are both required.");
            return;
        }

        editSaveButton.disabled = true;

        try {
            const res = await api(UPDATE_URL + encodeURIComponent(site.id), {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    location: site.location,
                    ip:       site.ip,
                    active:   site.active
                })
            });

            if (res.ok) {
                fillDbRow(editingRow, site);
                closeEditModal();
                showMessage(res.data.message || "Site updated.", false);
            } else {
                showEditError(res.data.message || "Update failed.");
            }

        } catch (err) {
            console.error(err);
            showEditError("Could not reach the server.");

        } finally {
            editSaveButton.disabled = false;
        }
    });


    /* =====================================================
       SAVE NEW ROWS
       ===================================================== */

    /* ---- collect only the NEW rows (rows already in DB have data-id) ---- */

    function collectSites() {
        const sites = [];

        sitesBody.querySelectorAll("tr:not([data-id])").forEach(function (row) {
            const location = row.querySelector(".site-location").value.trim();
            const ip       = row.querySelector(".site-ip").value.trim();
            const active   = row.querySelector(".site-active").checked;

            // skip rows where nothing was entered
            if (!location && !ip) {
                return;
            }

            sites.push({
                location: location,
                ip:       ip,
                active:   active
            });
        });

        return sites;
    }

    saveButton.addEventListener("click", async function () {

        // sites are only available for the central app
        if (!isCentral()) {
            showMessage("Sites can only be saved from the central app.", true);
            return;
        }

        const sites = collectSites();

        if (sites.length === 0) {
            showMessage("Please enter at least one new site.", true);
            return;
        }

        const incomplete = sites.find(function (s) {
            return !s.location || !s.ip;
        });

        if (incomplete) {
            showMessage("Each site needs both a location and an IP.", true);
            return;
        }

        saveButton.disabled = true;

        try {
            const res = await api(SAVE_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sites: sites })
            });

            if (res.ok) {
                showMessage(res.data.message || "Sites saved.", false);
                await loadSites();          // refresh: saved rows now show edit/delete icons
            } else {
                showMessage(res.data.message || "Save failed.", true);
            }

        } catch (err) {
            console.error(err);
            showMessage("Could not reach the server.", true);

        } finally {
            saveButton.disabled = false;
        }
    });


    /* =====================================================
       BOOT
       ===================================================== */

    toggleSites();
    loadSites();
});