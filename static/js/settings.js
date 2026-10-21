document.addEventListener("DOMContentLoaded", function () {

    const centralCheckbox = document.querySelector('input[name="is_central"]');
    const sitesCard       = document.getElementById("sites-card");
    const sitesBody       = document.getElementById("sites-body");
    const rowTemplate     = document.getElementById("site-row");
    const addRowButton    = document.getElementById("add-row-btn");


    /* ---- show Sites only for the central app ---- */

    function toggleSites() {
        sitesCard.hidden = !centralCheckbox.checked;
    }

    centralCheckbox.addEventListener("change", toggleSites);


    /* ---- Sl No ---- */

    function renumber() {
        sitesBody.querySelectorAll("tr").forEach(function (row, index) {
            row.querySelector(".sl").textContent = index + 1;
        });
    }


    /* ---- add row ---- */

    function addRow() {
        const row = rowTemplate.content.firstElementChild.cloneNode(true);
        sitesBody.appendChild(row);
        renumber();
        row.querySelector(".site-location").focus();
    }

    addRowButton.addEventListener("click", addRow);


    /* ---- remove row ---- */

    sitesBody.addEventListener("click", function (event) {

        const button = event.target.closest(".remove-row-btn");

        if (!button) {
            return;
        }

        button.closest("tr").remove();

        // keep at least one empty row to type into
        if (sitesBody.children.length === 0) {
            addRow();
            return;
        }

        renumber();
    });


    /* ---- boot ---- */

    if (sitesBody.children.length === 0) {
        addRow();
    }

    renumber();
    toggleSites();
});