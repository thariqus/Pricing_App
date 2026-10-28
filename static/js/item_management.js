document.addEventListener("DOMContentLoaded", function () {

/* =========================================================
   COLUMN DEFINITIONS

   Single source of truth. The header, the fetched rows, the
   Add Item row, the editors, the CSV export and the save
   payload are all generated from this array.

   type:     text | number | datetime | select
   editable: inline-editable on an existing (fetched) row
   ========================================================= */
const UOM_OPTIONS = ["PAC", "EA", "CAR"];
const LOCATION_OPTIONS = ["2112", "2113", "2132"];
const CURRENCY_OPTIONS = ["AED","USD", "EUR", "GBP", "JPY", "CAD", "AUD"];
const PRIORITY_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10","11"];

const COLUMNS = [
    { key: "active",               label: "Active",               type: "active"                    },
    { key: "condition_type",       label: "Condition Type",       type: "text"                      },
    { key: "item_no",              label: "Item No",              type: "text"                      },
    { key: "customer",             label: "Customer",             type: "text"                      },
    { key: "customer_grp",         label: "Customer Grp",         type: "text"                      },
    { key: "customer_hierarchy",   label: "Customer Hierarchy",   type: "text"                      },
    { key: "distribution_channel", label: "Distribution Channel", type: "text"                      },
    { key: "location_code",        label: "Location Code",        type: "select",   options: LOCATION_OPTIONS, editable: true },
    { key: "priority",             label: "Priority",             type: "select",   options: PRIORITY_OPTIONS, editable: true  },
    { key: "currency",             label: "Currency",             type: "select",   options: CURRENCY_OPTIONS, editable: true  },
    { key: "sales_price",          label: "Sales Price",          type: "number",   editable: true  },
    { key: "uom",                  label: "UOM",                  type: "select",   options: UOM_OPTIONS, editable: true  },
    { key: "min_qty",              label: "Min Qty",              type: "number",   editable: true  },
    { key: "starting_date",        label: "Starting Date",        type: "datetime", editable: true  },
    { key: "ending_date",          label: "Ending Date",          type: "datetime", editable: true  },
    { key: "lower_limit",          label: "Lower Limit",          type: "number",   editable: true  },
    { key: "upper_limit",          label: "Upper Limit",          type: "number",   editable: true  },
    { key: "zone_code",            label: "Zone Code",            type: "text",     editable: true  },
    { key: "offer_article",        label: "Offer Article",        type: "text",     editable: true  }
];


const API = {
    fetch:     "/api/items/fetch_all_item_prices",
    save:      "/api/items/create_singel_item_price",
    remove:    "/api/item-management/delete",
    sampleCsv: "/api/items/central_app",
    import:    "/api/items/central_app",
    filter:    "/api/items/filter_item_prices",
    upDate:    "/api/items/update_item_prices/"
};

/* =========================================================
   JS FIELD  ->  MySQL COLUMN
   ========================================================= */

const DB_COLUMNS = {
    active:               "active",
    condition_type:       "condition_type",
    item_no:              "item_no",
    customer:             "customer",
    customer_grp:         "customer_grp",
    customer_hierarchy:   "customer_hierarchy",
    distribution_channel: "distribution_channel_code",
    location_code:        "location_code",
    priority:             "priority",
    currency:             "currency",
    sales_price:          "sales_price",
    uom:                  "uom",
    min_qty:              "minimum_quantity",
    starting_date:        "starting_date",
    ending_date:          "ending_date",
    lower_limit:          "lower_limit",
    upper_limit:          "upper_limit",
    zone_code:            "transportation_zone_code",
    offer_article:        "offer_article"
};

/* Columns MySQL declares as INT / FLOAT — blanks are sent as null */
const NUMERIC_COLUMNS = new Set([
    "customer_grp",
    "customer_hierarchy",
    "distribution_channel_code",
    "location_code",
    "priority",
    "sales_price",
    "minimum_quantity",
    "lower_limit",
    "upper_limit"
]);

/* Columns MySQL declares as BOOLEAN / TINYINT(1) */
const BOOLEAN_COLUMNS = new Set([
    "active",
    "offer_article",
    "updated_from_sap"
]);

/* Columns MySQL declares as DATE / DATETIME */
const DATE_COLUMNS = new Set(["starting_date", "ending_date"]);


function toDbPayload(data) {

    const payload = {};

    Object.keys(data).forEach(function (key) {

        if (key === "id") {
            payload.id = data[key];
            return;
        }

        const column = DB_COLUMNS[key];

        if (!column) {
            return;
        }

        if (BOOLEAN_COLUMNS.has(column)) {

            let value = data[key];

            if (typeof value === "string") {
                value = value.trim().toLowerCase();
            }

            if (value === "" || value === null || value === undefined) {
                payload[column] = 0;
                return;
            }

            payload[column] =
                (value === true || value === "true" || value === "1" || value === 1)
                    ? 1 : 0;

            return;
        }

        let value = data[key];

        if (typeof value === "string") {
            value = value.trim();
        }

        // Blank -> NULL for anything MySQL types as a number or date
        if (
            value === "" &&
            (NUMERIC_COLUMNS.has(column) || DATE_COLUMNS.has(column))
        ) {
            payload[column] = null;
            return;
        }

        if (value !== "" && NUMERIC_COLUMNS.has(column)) {
            const number = Number(value);
            payload[column] = isNaN(number) ? null : number;
            return;
        }

        payload[column] = value;
    });

    return payload;
}

/* =========================================================
   MySQL COLUMN  ->  JS FIELD  (reverse of DB_COLUMNS)
   ========================================================= */

const UI_FIELDS = {};

Object.keys(DB_COLUMNS).forEach(function (uiKey) {
    UI_FIELDS[DB_COLUMNS[uiKey]] = uiKey;
});

function fromDbRow(row) {

    const item = {};

    Object.keys(row).forEach(function (key) {
        item[UI_FIELDS[key] || key] = row[key];
    });

    return item;
}

const PAGE_SIZE = 500;


/* =========================================================
   STATE
   ========================================================= */

let items       = [];          // rows returned by the last fetch
let currentPage = 1;
let totalPages  = 1;
let totalRows   = 0;

// Pending edits to existing rows, keyed by row id
const pendingUpdates = new Map();

const tableHead  = document.getElementById("itemPriceTableHead");
const tableBody  = document.getElementById("itemPriceTableBody");
const saveButton = document.getElementById("saveUpdateBtn");
const pagination = document.getElementById("paginationControls");


/* =========================================================
   HELPERS
   ========================================================= */

function rowId(item) {
    return item.id ?? item.condition_id ?? item.unique_key ?? null;
}

function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/* =========================================================
   MESSAGE MODAL  (replaces alert / confirm)

   showAlert(message, { type, title })
   showConfirm(message, { type, title, confirmText, cancelText, danger })
       -> Promise<boolean>
   type: "success" | "error" | "warning" | "info"
   ========================================================= */

const msgModal  = document.getElementById("msgModal");
const msgIcon   = document.getElementById("msgIcon");
const msgTitle  = document.getElementById("msgTitle");
const msgText   = document.getElementById("msgText");
const msgOk     = document.getElementById("msgOk");
const msgCancel = document.getElementById("msgCancel");

const MSG_ICONS = {
    success: "fa-circle-check",
    error:   "fa-circle-xmark",
    warning: "fa-triangle-exclamation",
    info:    "fa-circle-info"
};

const MSG_TITLES = {
    success: "Success",
    error:   "Error",
    warning: "Warning",
    info:    "Notice"
};

let msgResolve = null;   // resolver of the dialog currently open

function openDialog(message, options, isConfirm) {

    options = options || {};

    // A new dialog replaces any open one (counts as "cancelled")
    if (msgResolve) {
        msgResolve(false);
        msgResolve = null;
    }

    const type = options.type || (isConfirm ? "warning" : "info");

    msgModal.className = "modal msg-" + type;
    msgIcon.className  = "fas " + MSG_ICONS[type];
    msgTitle.textContent = options.title || (isConfirm ? "Please confirm" : MSG_TITLES[type]);
    msgText.textContent  = message;

    msgOk.textContent     = options.confirmText || "OK";
    msgOk.className       = "btn " + (options.danger ? "btn-danger" : "btn-primary");
    msgCancel.textContent = options.cancelText || "Cancel";
    msgCancel.style.display = isConfirm ? "" : "none";

    msgModal.style.display = "block";
    msgOk.focus();

    return new Promise(function (resolve) {

        function close(result) {
            msgModal.style.display = "none";
            msgResolve = null;
            resolve(result);
        }

        msgResolve = close;

        msgOk.onclick     = function () { close(true); };
        msgCancel.onclick = function () { close(false); };

        // Click on the dark backdrop = cancel
        msgModal.onclick = function (event) {
            if (event.target === msgModal) {
                close(false);
            }
        };
    });
}

function showAlert(message, options) {
    return openDialog(message, options, false);
}

function showConfirm(message, options) {
    return openDialog(message, options, true);
}

// Esc closes the dialog
document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && msgResolve) {
        msgResolve(false);
    }
});

function toBackendDateTime(value) {

    if (!value) {
        return "";
    }

    let text = String(value).trim().replace("T", " ");

    // 2026-08-21 23:59  ->  2026-08-21 23:59:00
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(text)) {
        text += ":00";
    }

    return text;
}

// CSV wants US-style dates; the table holds YYYY-MM-DD HH:MM:SS
function csvDate(value) {

    if (!value) {
        return "";
    }

    const parsed = new Date(String(value).replace(" ", "T"));

    if (isNaN(parsed)) {
        return value;
    }

    return String(parsed.getMonth() + 1).padStart(2, "0") + "/" +
           String(parsed.getDate()).padStart(2, "0") + "/" +
           parsed.getFullYear();
}

function toInputDateTime(value) {

    // Backend sends "2026-08-21 23:59:59"; datetime-local needs a T.
    return String(value ?? "").trim().replace(" ", "T");
}

function nowForInput() {

    const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
    return now.toISOString().slice(0, 19);
}

function endOfTodayForInput() {

    const now = new Date();

    return now.getFullYear() + "-" +
        String(now.getMonth() + 1).padStart(2, "0") + "-" +
        String(now.getDate()).padStart(2, "0") + "T23:59:59";
}


/* =========================================================
   VALIDATION
   ========================================================= */

const PRIORITY_CONFIG = [
    ["distribution_channel", "customer",         "location_code", "item_no", "uom"],
    ["distribution_channel", "customer_grp",     "location_code", "item_no", "uom"],
    ["distribution_channel", "customer",         "item_no", "uom"],
    ["distribution_channel", "customer_grp",     "item_no", "uom"],
    ["customer_grp",         "item_no",          "uom"],
    ["customer_hierarchy",   "location_code",    "item_no", "uom"],
    ["customer_hierarchy",   "item_no",          "uom"],
    ["distribution_channel", "location_code",    "item_no", "zone_code", "uom"],
    ["distribution_channel", "location_code",    "item_no", "uom"],
    ["distribution_channel", "item_no",          "uom"],
    ["item_no",              "uom"]
];

const FIELD_LABELS = {
    sales_organization:   "Sales Organization",
    distribution_channel: "Distribution Channel",
    customer:             "Customer No",
    customer_grp:         "Customer Group",
    customer_hierarchy:   "Customer Hierarchy",
    location_code:        "Location Code",
    item_no:              "Item No",
    uom:                  "Unit of Measure",
    zone_code:            "Transportation Zone Code",
    condition_type:       "Condition Type",
    sales_price:          "Sales Price",
    starting_date:        "Starting Date",
    ending_date:          "Ending Date",
    lower_limit:          "Lower Limit",
    upper_limit:          "Upper Limit",
    priority:             "Priority",
    currency:             "Currency"
};

const REQUIRED_FIELDS = [
    "condition_type",
    "sales_price",
    "starting_date",
    "ending_date",
    "lower_limit",
    "upper_limit",
    "priority",
    "currency"
];

const FREE_FIELDS = new Set([
    "min_qty",
    "offer_article",
    "active",
    "id",
    "sales_organization"
]);


function validateItem(data, mode) {

    const errors   = [];
    const isUpdate = mode === "update";

    const lower = data.lower_limit !== undefined && data.lower_limit !== ""
        ? Number(data.lower_limit) : undefined;

    const upper = data.upper_limit !== undefined && data.upper_limit !== ""
        ? Number(data.upper_limit) : undefined;

    const sales = data.sales_price !== undefined && data.sales_price !== ""
        ? Number(data.sales_price) : undefined;


    /* ---- numeric ---- */

    ["sales_price", "lower_limit", "upper_limit", "min_qty", "priority"].forEach(function (field) {

        if (
            data[field] !== undefined &&
            data[field] !== "" &&
            isNaN(Number(data[field]))
        ) {
            errors.push((FIELD_LABELS[field] || field) + " must be a number");
        }
    });


    /* ---- positive values ---- */

    if (lower !== undefined && !isNaN(lower) && lower <= 0) {
        errors.push("Lower Limit must be greater than 0");
    }

    if (upper !== undefined && !isNaN(upper) && upper <= 0) {
        errors.push("Upper Limit must be greater than 0");
    }

    if (sales !== undefined && !isNaN(sales) && sales <= 0) {
        errors.push("Sales Price must be greater than 0");
    }


    /* ---- relations ---- */

    if (lower !== undefined && upper !== undefined && !isNaN(lower) && !isNaN(upper) && lower > upper) {
        errors.push("Lower Limit cannot be greater than Upper Limit");
    }

    if (sales !== undefined && lower !== undefined && !isNaN(sales) && !isNaN(lower) && sales < lower) {
        errors.push("Sales Price cannot be less than Lower Limit");
    }

    if (sales !== undefined && upper !== undefined && !isNaN(sales) && !isNaN(upper) && sales > upper) {
        errors.push("Sales Price cannot be greater than Upper Limit");
    }


    /* ---- dates ---- */

    const dateRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;

    ["starting_date", "ending_date"].forEach(function (field) {

        if (data[field]) {

            data[field] = toBackendDateTime(data[field]);

            if (!dateRegex.test(data[field])) {
                errors.push((FIELD_LABELS[field] || field) + " must be YYYY-MM-DD HH:mm:ss");
            }
        }
    });

    if (
        data.starting_date &&
        data.ending_date &&
        dateRegex.test(data.starting_date) &&
        dateRegex.test(data.ending_date) &&
        data.starting_date > data.ending_date
    ) {
        errors.push("Starting Date cannot be after Ending Date");
    }


    /* ---- priority ---- */

    const hasPriority =
        data.priority !== undefined &&
        data.priority !== null &&
        data.priority !== "";

    const priority = hasPriority ? Number(data.priority) : null;

    if (isUpdate) {

        // On update, only check priority when it's being changed.
        if (hasPriority && (isNaN(priority) || priority < 1 || priority > PRIORITY_CONFIG.length)) {

            errors.push(
                "Invalid priority value: " + data.priority +
                ". Valid values are 1 to " + PRIORITY_CONFIG.length
            );
        }

    } else {

        REQUIRED_FIELDS.forEach(function (field) {

            if (
                data[field] === undefined ||
                data[field] === null ||
                String(data[field]).trim() === ""
            ) {
                errors.push((FIELD_LABELS[field] || field) + " is required");
            }
        });

        if (!hasPriority || isNaN(priority)) {

            errors.push("Priority is required");

        } else if (priority < 1 || priority > PRIORITY_CONFIG.length) {

            errors.push(
                "Invalid priority value: " + data.priority +
                ". Valid values are 1 to " + PRIORITY_CONFIG.length
            );

        } else {

            const mandatory = PRIORITY_CONFIG[priority - 1];

            mandatory.forEach(function (field) {

                if (
                    data[field] === undefined ||
                    data[field] === null ||
                    String(data[field]).trim() === ""
                ) {

                    errors.push(
                        (FIELD_LABELS[field] || field) +
                        " is required for priority " + priority
                    );
                }
            });


            // Fields that must stay empty for this priority
            Object.keys(data).forEach(function (field) {

                if (
                    REQUIRED_FIELDS.indexOf(field) === -1 &&
                    mandatory.indexOf(field) === -1 &&
                    !FREE_FIELDS.has(field) &&
                    data[field] !== undefined &&
                    data[field] !== null &&
                    String(data[field]).trim() !== ""
                ) {

                    errors.push(
                        "'" + (FIELD_LABELS[field] || field) +
                        "' must be empty for priority " + priority
                    );
                }
            });
        }
    }


    if (errors.length > 0) {
        showAlert(errors.join("\n"), { type: "error", title: "Validation failed" });
        return false;
    }

    return true;
}


/* =========================================================
   HEADER
   ========================================================= */

function renderHead() {

    let html = "";

    COLUMNS.forEach(function (column) {
        html += "<th>" + escapeHtml(column.label) + "</th>";
    });

    html += '<th class="fixed-action-column action-col">Action</th>';
    tableHead.innerHTML = html;
    initColumnResize(); 
}

/* =========================================================
   RESIZABLE COLUMNS (Excel-style)
   ========================================================= */

    const COL_WIDTH_KEY = "item_mgmt_col_widths_v1";
    const MIN_COL_WIDTH = 30;

    function applyColumnWidths(widths) {

        const table = tableHead.closest("table");
        const ths   = Array.from(tableHead.children);

        ths.forEach(function (th, i) {
            th.style.width = widths[i] + "px";
        });

        table.style.width = widths.reduce(function (a, b) { return a + b; }, 0) + "px";
    }

    function freezeColumnWidths() {

        // Convert the current % widths to px so each column can move independently
        const widths = Array.from(tableHead.children).map(function (th) {
            return th.getBoundingClientRect().width;
        });

        applyColumnWidths(widths);
        return widths;
    }

    function resetColumnWidths() {

        const table = tableHead.closest("table");

        Array.from(tableHead.children).forEach(function (th) { th.style.width = ""; });
        table.style.width = "";

        try { localStorage.removeItem(COL_WIDTH_KEY); } catch (e) {}
    }

    function initColumnResize() {

        const ths = Array.from(tableHead.children);

        // Restore saved widths
        try {
            const saved = JSON.parse(localStorage.getItem(COL_WIDTH_KEY) || "null");

            if (Array.isArray(saved) && saved.length === ths.length) {
                applyColumnWidths(saved);
            }
        } catch (e) {}

        ths.forEach(function (th, index) {

            // The sticky Action column keeps its fixed size
            if (index === ths.length - 1) {
                return;
            }

            const handle = document.createElement("div");

            handle.className = "col-resizer";
            handle.title = "Drag to resize · double-click to reset all";

            th.appendChild(handle);

            handle.addEventListener("dblclick", function (event) {
                event.stopPropagation();
                resetColumnWidths();
            });

            handle.addEventListener("pointerdown", function (event) {

                event.preventDefault();
                event.stopPropagation();

                const widths      = freezeColumnWidths();
                const startX      = event.clientX;
                const startWidth  = widths[index];

                handle.setPointerCapture(event.pointerId);
                handle.classList.add("resizing");
                document.body.classList.add("col-resizing");

                function onMove(e) {
                    widths[index] = Math.max(MIN_COL_WIDTH, startWidth + (e.clientX - startX));
                    applyColumnWidths(widths);
                }

                function onUp() {

                    handle.removeEventListener("pointermove", onMove);
                    handle.removeEventListener("pointerup", onUp);
                    handle.removeEventListener("pointercancel", onUp);

                    handle.classList.remove("resizing");
                    document.body.classList.remove("col-resizing");

                    try { localStorage.setItem(COL_WIDTH_KEY, JSON.stringify(widths)); } catch (e) {}
                }

                handle.addEventListener("pointermove", onMove);
                handle.addEventListener("pointerup", onUp);
                handle.addEventListener("pointercancel", onUp);
            });
        });
    }


/* =========================================================
   SAVE BUTTON STATE
   ========================================================= */

function hasPendingNewRows() {

    return Array.from(tableBody.querySelectorAll(".new-item-row")).some(function (row) {

        const input = row.querySelector('[data-field="item_no"]');
        return input && input.value.trim() !== "";
    });
}

function refreshSaveButtonState() {

    saveButton.disabled = pendingUpdates.size === 0 && !hasPendingNewRows();

    // Show the Action column only while there are unsaved new rows
    const table = tableBody.closest("table");
    table.classList.toggle("has-new-rows", tableBody.querySelector(".new-item-row") !== null);
}


/* =========================================================
   RENDER FETCHED ROWS
   ========================================================= */

function displayValue(item, column) {

    const pending = pendingUpdates.get(rowId(item));

    if (pending && Object.prototype.hasOwnProperty.call(pending, column.key)) {
        return pending[column.key];
    }

    return item[column.key];
}

function renderTable() {

    tableBody.innerHTML = "";

    if (items.length === 0) {

        tableBody.innerHTML =
            '<tr><td colspan="' + (COLUMNS.length + 1) + '"' +
            ' style="text-align:center; padding:20px; color:#777;">' +
            "No items found</td></tr>";

        return;
    }

    items.forEach(function (item) {

        const id      = rowId(item);
        const pending = pendingUpdates.get(id);
        const row     = document.createElement("tr");

        row.dataset.id = id === null ? "" : id;

        if (pending) {
            row.classList.add("row-dirty");
        }

        let html = "";

        COLUMNS.forEach(function (column) {

            const value   = displayValue(item, column);
            const changed = pending &&
                Object.prototype.hasOwnProperty.call(pending, column.key);

            if (column.type === "active") {

                const isActive = value === true || value === "true" || value === 1;

                html +=
                    '<td class="col-active">' +
                        '<button type="button" class="active-tick-btn' +
                        (isActive ? "" : " inactive") + '" title="Toggle active">' +
                        (isActive ? "\u2713" : "") +
                        "</button>" +
                    "</td>";

                return;
            }

            html +=
                '<td class="col-' + column.key +
                (column.editable ? " editable-cell" : "") +
                (changed ? " cell-dirty" : "") +
                '" data-field="' + column.key + '">' +
                escapeHtml(value ?? "") +
                "</td>";
        });

               html += '<td class="action-col"></td>';

        row.innerHTML = html;

        tableBody.appendChild(row);
    });
}

function renderPagination() {

    totalPages = Math.max(1, Math.ceil(totalRows / PAGE_SIZE));

    if (items.length === 0) {
        pagination.innerHTML = "";
        return;
    }

    pagination.innerHTML =
        '<button type="button" id="prevPage"' +
        (currentPage === 1 ? " disabled" : "") + ">Previous</button>" +
        "<span>Page " + currentPage + " / " + totalPages +
        " &nbsp;·&nbsp; " + totalRows.toLocaleString() + " rows</span>" +
        '<button type="button" id="nextPage"' +
        (currentPage >= totalPages ? " disabled" : "") + ">Next</button>";

    const prev = document.getElementById("prevPage");
    const next = document.getElementById("nextPage");

    if (prev) {
        prev.addEventListener("click", function () {
            if (currentPage > 1) {
                discardPendingOrConfirm().then(function (ok) {
                    if (ok) {
                        fetchAndPopulate(currentPage - 1);
                    }
                });
            }
        });
    }

    if (next) {
        next.addEventListener("click", function () {
            if (currentPage < totalPages) {
                discardPendingOrConfirm().then(function (ok) {
                    if (ok) {
                        fetchAndPopulate(currentPage + 1);
                    }
                });
            }
        });
    }
}


/* =========================================================
   INLINE CELL EDITING
   ========================================================= */

function recordChange(row, field, value) {

    const id = row.dataset.id;

    if (!id) {
        showAlert("This row has no id, so the change can't be saved.", { type: "error" });
        return false;
    }

    const entry = pendingUpdates.get(id) || { id: id };

    entry[field] = value;

    pendingUpdates.set(id, entry);

    row.classList.add("row-dirty");

    refreshSaveButtonState();

    return true;
}

function cellValue(row, field) {

    const cell = row.querySelector('[data-field="' + field + '"]');
    return cell ? cell.innerText.trim() : "";
}

function makeCellEditable(cell) {

    if (cell.querySelector("input, select")) {
        return;
    }

    const row    = cell.parentNode;
    const field  = cell.dataset.field;
    const column = COLUMNS.find(function (c) { return c.key === field; });

    if (!column || !column.editable) {
        return;
    }

    const oldValue = cell.innerText.trim();
    let input;

    if (column.type === "select") {

        input = document.createElement("select");

        const blank = document.createElement("option");
        blank.value = "";
        input.appendChild(blank);

        column.options.forEach(function (code) {
            const option = document.createElement("option");
            option.value = code;
            option.textContent = code;
            input.appendChild(option);
        });

        input.value = oldValue;
        input.addEventListener("change", function () { input.blur(); });

    } else if (column.type === "number") {

        input = document.createElement("input");
        input.type = "number";
        input.step = "any";
        input.value = oldValue;

    } else if (column.type === "datetime") {

        input = document.createElement("input");
        input.type  = "datetime-local";
        input.step  = "1";
        input.value = toInputDateTime(oldValue);

    } else {

        input = document.createElement("input");
        input.type  = "text";
        input.value = oldValue;
    }

    let finished = false;

    function commit() {

        if (finished) {
            return;
        }

        finished = true;

        let newValue = input.value;

        if (column.type === "datetime") {
            newValue = toBackendDateTime(newValue);
        }

        newValue = String(newValue).trim();

        cell.innerText = newValue;

        if (newValue === oldValue) {
            return;
        }

        // Validate the change against the row's other values
        const candidate = {
            priority:      field === "priority"      ? newValue : cellValue(row, "priority"),
            sales_price:   field === "sales_price"   ? newValue : cellValue(row, "sales_price"),
            lower_limit:   field === "lower_limit"   ? newValue : cellValue(row, "lower_limit"),
            upper_limit:   field === "upper_limit"   ? newValue : cellValue(row, "upper_limit"),
            min_qty:       field === "min_qty"       ? newValue : cellValue(row, "min_qty"),
            starting_date: field === "starting_date" ? newValue : cellValue(row, "starting_date"),
            ending_date:   field === "ending_date"   ? newValue : cellValue(row, "ending_date")
        };

        if (!validateItem(candidate, "update")) {
            cell.innerText = oldValue;
            return;
        }

        if (!recordChange(row, field, newValue)) {
            cell.innerText = oldValue;
            return;
        }

        cell.classList.add("cell-dirty");
    }

    input.addEventListener("blur", commit);

    input.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {
            event.preventDefault();
            input.blur();
        }

        if (event.key === "Escape") {
            finished = true;
            cell.innerText = oldValue;
        }
    });

    cell.innerText = "";
    cell.appendChild(input);
    input.focus();
}


/* =========================================================
   ADD ITEM ROW
   ========================================================= */

function createNewRow(afterRow) {

    const row = document.createElement("tr");

    row.className = "new-item-row";

    let html = "";

    COLUMNS.forEach(function (column) {

        if (column.type === "active") {

            html +=
                "<td>" +
                    '<button type="button" class="active-tick-btn" tabindex="-1" title="Toggle active">\u2713</button>' +
                    '<input type="hidden" data-field="active" value="true">' +
                "</td>";

            return;
        }

        if (column.type === "datetime") {
            const value = column.key === "starting_date"
                ? nowForInput()
                : endOfTodayForInput();
            html +=
                "<td>" +
                    '<input type="datetime-local" step="1" data-field="' +
                    column.key + '" value="' + value + '"' +
                    ' min="' + nowForInput() + '">' +
                "</td>";
            return;
        }

        if (column.type === "select") {

            let optionHtml = '<option value=""></option>';

            column.options.forEach(function (code) {
                optionHtml += '<option value="' + escapeHtml(code) + '">' +
                              escapeHtml(code) + "</option>";
            });

            html += '<td><select data-field="' + column.key + '">' + optionHtml + "</select></td>";

            return;
        }

        const defaults = { condition_type: "ZEN1", currency: "AED" };

        html +=
            "<td>" +
                '<input type="' + (column.type === "number" ? "number" : "text") + '"' +
                (column.type === "number" ? ' step="any"' : "") +
                ' data-field="' + column.key + '"' +
                ' placeholder="' + escapeHtml(column.label) + '"' +
                ' value="' + (defaults[column.key] || "") + '"' +
                ' autocomplete="off">' +
            "</td>";
    });

      html +=
        "<td>" +
            '<button type="button" class="delete-row-btn delete-row" tabindex="-1" title="Remove row">' +
                '<i class="fas fa-trash"></i>' +
            "</button>" +
        "</td>";

    row.innerHTML = html;

    if (afterRow) {
        afterRow.after(row);
    } else {
        tableBody.prepend(row);
    }

    const focusTarget = afterRow
        ? row.querySelector('input:not([type="hidden"]), select')
        : row.querySelector('[data-field="item_no"]');

    if (focusTarget) {
        focusTarget.focus();
    }

    refreshSaveButtonState();

    return row;
}

function readNewRow(row) {

    const data = {};

    COLUMNS.forEach(function (column) {

        const input = row.querySelector('[data-field="' + column.key + '"]');

        if (!input) {
            data[column.key] = "";
            return;
        }

        if (column.type === "active") {
            data.active = input.value === "true";
            return;
        }

        let value = (input.value ?? "").toString().trim();

        if (column.type === "datetime") {
            value = toBackendDateTime(value);
        }

        data[column.key] = value;
    });

    return data;
}

function collectNewRows() {

    return Array.from(tableBody.querySelectorAll(".new-item-row"))
        .map(function (row) {
            return { row: row, data: readNewRow(row) };
        })
        .filter(function (entry) {
            return entry.data.item_no !== "";
        });
}


/* =========================================================
   TABLE EVENT DELEGATION
   ========================================================= */

tableBody.addEventListener("click", function (event) {

    /* ---- active toggle ---- */

    const tick = event.target.closest(".active-tick-btn");

    if (tick) {

        const isActive = !tick.classList.contains("inactive");
        const row      = tick.closest("tr");

        tick.classList.toggle("inactive", isActive);
        tick.textContent = isActive ? "" : "\u2713";

        if (row.classList.contains("new-item-row")) {

            const hidden = row.querySelector('[data-field="active"]');

            if (hidden) {
                hidden.value = isActive ? "false" : "true";
            }

            refreshSaveButtonState();
            return;
        }

        const nowActive = !isActive;

        recordChange(row, "active", nowActive);

        // Deactivating stamps the ending date with "now"
        if (!nowActive) {

            const now = new Date();

            const stamp =
                now.getFullYear() + "-" +
                String(now.getMonth() + 1).padStart(2, "0") + "-" +
                String(now.getDate()).padStart(2, "0") + " " +
                String(now.getHours()).padStart(2, "0") + ":" +
                String(now.getMinutes()).padStart(2, "0") + ":" +
                String(now.getSeconds()).padStart(2, "0");

            const endCell = row.querySelector('[data-field="ending_date"]');

            if (endCell) {
                endCell.innerText = stamp;
                endCell.classList.add("cell-dirty");
            }

            recordChange(row, "ending_date", stamp);
        }

        return;
    }


    /* ---- delete ---- */

    const deleteButton = event.target.closest(".delete-row");

    if (deleteButton) {

        const row = deleteButton.closest("tr");

        if (row.classList.contains("new-item-row")) {
            row.remove();
            refreshSaveButtonState();
            return;
        }

        const id = row.dataset.id;

        if (!id) {
            showAlert("This row has no id, so it can't be deleted.", { type: "error" });
            return;
        }

        showConfirm("Delete this item condition? This cannot be undone.", {
            title: "Delete item",
            confirmText: "Delete",
            danger: true
        })
        .then(function (ok) {

            if (!ok) {
                return;
            }

            deleteButton.disabled = true;

            fetch(API.remove, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: id })
            })
            .then(function (response) {

                return response.json().then(function (result) {

                    if (!response.ok) {
                        throw new Error(result.error || result.message || "Delete failed");
                    }

                    return result;
                });
            })
            .then(function () {

                items = items.filter(function (item) {
                    return String(rowId(item)) !== String(id);
                });

                pendingUpdates.delete(id);

                renderTable();
                renderPagination();
                refreshSaveButtonState();
            })
            .catch(function (error) {

                console.error("Delete error:", error);
                showAlert(error.message, { type: "error", title: "Delete failed" });
                deleteButton.disabled = false;
            });
        });

        return;
    }


    /* ---- inline edit ---- */

    const cell = event.target.closest("td.editable-cell");

    if (cell) {
        makeCellEditable(cell);
    }
});

tableBody.addEventListener("input", function (event) {

    if (event.target.closest(".new-item-row")) {
        refreshSaveButtonState();
    }
});

// Enter must not submit the fetch form; Tab on the last field adds a new line
tableBody.addEventListener("keydown", function (event) {

    const row = event.target.closest(".new-item-row");

    if (!row) {
        return;
    }

    if (event.key === "Enter" && event.target.matches("input")) {
        event.preventDefault();
        return;
    }

    if (event.key === "Tab" && !event.shiftKey) {

        const fields = Array.from(
            row.querySelectorAll('input:not([type="hidden"]), select')
        );

        if (event.target === fields[fields.length - 1]) {
            event.preventDefault();
            createNewRow(row);
        }
    }
});


/* =========================================================
   ITEM NO ROWS
   ========================================================= */

const itemNoContainer = document.getElementById("itemNoContainer");

itemNoContainer.addEventListener("click", function (event) {

    if (event.target.closest(".addItemNoBtn")) {

        const row = document.createElement("div");

        row.className = "item-no-row";

        row.innerHTML =
            '<input type="text" class="form-control itemNoInput"' +
            ' name="item_no[]" placeholder="Item No" autocomplete="off">' +
            '<button type="button" class="removeItemNoBtn" title="Remove Item No">\u2212</button>';

        itemNoContainer.appendChild(row);

        row.querySelector(".itemNoInput").focus();

        return;
    }

    const removeButton = event.target.closest(".removeItemNoBtn");

    if (removeButton && itemNoContainer.querySelectorAll(".item-no-row").length > 1) {
        removeButton.closest(".item-no-row").remove();
    }
});


/* =========================================================
   FILTER CHIPS
   ========================================================= */

const addFilterSelect = document.getElementById("addFilterSelect");
const activeFilters   = document.getElementById("activeFilters");

const DATE_FILTERS   = ["starting_date", "ending_date"];
const NUMBER_FILTERS = ["sales_price", "min_qty", "lower_limit", "upper_limit", "priority"];

addFilterSelect.addEventListener("change", function () {

    const value = this.value;

    this.value = "";

    if (!value || document.getElementById("filter-" + value)) {
        return;
    }

    const chip = document.createElement("div");

    chip.id = "filter-" + value;


    /* ---- customer / group / hierarchy ---- */

    if (value === "customer_group_hierarchy") {

        chip.className = "filter-chip customer-hierarchy-filter";

        chip.innerHTML =
            '<label class="customer-filter-label">CUSTOMER</label>' +
            '<select class="customer-filter-type">' +
                '<option value="customer">Customer No</option>' +
                '<option value="customer_grp">Customer Group</option>' +
                '<option value="customer_hierarchy">Customer Hierarchy</option>' +
            "</select>" +
            '<input type="text" class="customer-filter-value" placeholder="Value">' +
            '<button type="button" class="customer-filter-remove" title="Remove filter">\u00d7</button>';

        activeFilters.appendChild(chip);
        return;
    }


    /* ---- sort by ---- */

    if (value === "sort_by") {

        chip.className = "filter-chip";

        chip.innerHTML =
            "<label>Sort By</label>" +
            "<select>" +
                '<option value="">-- Select --</option>' +
                '<option value="starting_date">Starting Date</option>' +
                '<option value="ending_date">Ending Date</option>' +
                '<option value="item_no">Item No</option>' +
                '<option value="sales_price">Sales Price</option>' +
            "</select>" +
            '<button type="button" class="remove-filter" title="Remove filter">\u00d7</button>';

        activeFilters.appendChild(chip);
        return;
    }


    /* ---- generic ---- */

    const label = value
        .replace(/_/g, " ")
        .replace(/\b\w/g, function (c) { return c.toUpperCase(); });

    let inputType = "text";

    if (DATE_FILTERS.indexOf(value) !== -1) {
        inputType = "datetime-local";
    } else if (NUMBER_FILTERS.indexOf(value) !== -1) {
        inputType = "number";
    }

    chip.className = "filter-chip";

    chip.innerHTML =
        "<label>" + escapeHtml(label) + "</label>" +
        '<input type="' + inputType + '"' +
        (inputType === "datetime-local" ? ' step="1"' : "") +
        (inputType === "number" ? ' step="any"' : "") +
        ' placeholder="' + escapeHtml(label) + '">' +
        '<button type="button" class="remove-filter" title="Remove filter">\u00d7</button>';

    activeFilters.appendChild(chip);

    const focusable = chip.querySelector("input, select");

    if (focusable) {
        focusable.focus();
    }
});

activeFilters.addEventListener("click", function (event) {

    const removeButton = event.target.closest(".customer-filter-remove, .remove-filter");

    if (!removeButton) {
        return;
    }

    const chip = removeButton.closest(".filter-chip");

    if (chip) {
        chip.remove();
    }
});

function collectFilters() {

    const filters = {};

    activeFilters.querySelectorAll(".filter-chip").forEach(function (chip) {

        /* customer / group / hierarchy */
        if (chip.classList.contains("customer-hierarchy-filter")) {

            const type  = chip.querySelector(".customer-filter-type");
            const value = chip.querySelector(".customer-filter-value");

            if (type && value && value.value.trim()) {
                filters[type.value] = value.value.trim();
            }

            return;
        }

        const key   = chip.id.replace("filter-", "");
        const field = chip.querySelector("input, select");

        if (!field || !field.value.trim()) {
            return;
        }

        let value = field.value.trim();

        if (field.type === "datetime-local") {
            value = toBackendDateTime(value);
        }

        filters[key] = value;
    });

    return filters;
}


/* =========================================================
   FETCH
   ========================================================= */

// Returns a Promise<boolean>: true = safe to continue
function discardPendingOrConfirm() {

    if (pendingUpdates.size === 0 && !hasPendingNewRows()) {
        return Promise.resolve(true);
    }

    return showConfirm("You have unsaved changes. Fetching will discard them. Continue?", {
        title: "Unsaved changes",
        confirmText: "Discard & fetch"
    });
}

function fetchAndPopulate(page) {

    currentPage = page || 1;

    const itemNumbers = Array.from(document.querySelectorAll(".itemNoInput"))
        .map(function (input) { return input.value.trim(); })
        .filter(function (value) { return value !== ""; });

    const filters = collectFilters();

    // sort_by isn't a column, so it travels outside the column map
    const sortBy = filters.sort_by || "";
    delete filters.sort_by;

    const activeValue = document.getElementById("fetchActive").value;

    const hasFilters =
        itemNumbers.length > 0 ||
        activeValue !== "" ||
        sortBy !== "" ||
        Object.keys(filters).length > 0;

    const url = hasFilters ? API.filter : API.fetch;

    const payload = {
        item_no: itemNumbers,
        active:  activeValue,
        filters: toDbPayload(filters),
        sort_by: sortBy,
        page:    currentPage,
        limit:   PAGE_SIZE
    };

    console.log("Fetch:", url, payload);

    tableBody.innerHTML =
        '<tr><td colspan="' + (COLUMNS.length + 1) + '"' +
        ' style="text-align:center; padding:20px; color:#777;">Loading…</td></tr>';

    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(function (response) {

        return response.json().then(function (result) {

            if (!response.ok) {
                throw new Error(result.error || result.message || "Failed to fetch items");
            }

            return result;
        });
    })
    .then(function (result) {

        // translate DB column names back to UI keys
        items = (result.data || result.items || result.message || []).map(fromDbRow);

        totalRows = result.total || items.length;

        pendingUpdates.clear();

        renderTable();
        renderPagination();
        refreshSaveButtonState();
    })
    .catch(function (error) {

        console.error("Fetch error:", error);

        items     = [];
        totalRows = 0;

        tableBody.innerHTML =
            '<tr><td colspan="' + (COLUMNS.length + 1) + '"' +
            ' style="text-align:center; padding:20px; color:#777;">' +
            "No Items Found</td></tr>";

        pagination.innerHTML = "";

        showAlert(error.message || "Unable to fetch data", {
            type: "error",
            title: "Fetch failed"
        });
    });
}


document.getElementById("fetchForm").addEventListener("submit", function (event) {

    event.preventDefault();

    discardPendingOrConfirm().then(function (ok) {
        if (ok) {
            fetchAndPopulate();
        }
    });
});

document.getElementById("fetchActive").addEventListener("change", function () {

    discardPendingOrConfirm().then(function (ok) {
        if (ok) {
            fetchAndPopulate();
        }
    });
});


/* =========================================================
   ADD ITEM
   ========================================================= */

document.getElementById("addItemBtn").addEventListener("click", function () {
    createNewRow();
});


/* =========================================================
   SAVE

     - each NEW row    -> POST  API.save   (one request per row)
     - all EDITED rows -> ONE PUT to API.upDate carrying a list
   ========================================================= */

function sendJson(url, method, body) {

    return fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    })
    .then(function (response) {

        return response.json()
            .catch(function () {
                throw new Error("Server returned HTTP " + response.status);
            })
            .then(function (result) {

                if (
                    !response.ok ||
                    result.success === false ||
                    result.status === "error"
                ) {
                    throw new Error(result.error || result.message || "Save failed");
                }

                return result;
            });
    });
}

// NEW rows: one POST per row
function sendRow(url, data) {
    return sendJson(url, "POST", toDbPayload(data));
}

// EDITED rows: one PUT with the whole list
function sendUpdates(url, list) {
    return sendJson(url, "PUT", list.map(toDbPayload));
}

saveButton.addEventListener("click", function () {

    // Commit any editor still open
    const openEditor = tableBody.querySelector("td.editable-cell input, td.editable-cell select");

    if (openEditor) {
        openEditor.blur();
    }

    const newRows = collectNewRows();
    const updates = Array.from(pendingUpdates.values());

    if (newRows.length === 0 && updates.length === 0) {
        showAlert("No changes to save.", { type: "info" });
        return;
    }

    // Validate new rows up front — nothing is sent if one fails
    for (let index = 0; index < newRows.length; index++) {

        if (!validateItem(newRows[index].data, "insert")) {

            const input = newRows[index].row.querySelector('[data-field="item_no"]');

            if (input) {
                input.focus();
            }

            return;
        }
    }

    console.log("Saving", newRows.length, "new row(s),", updates.length, "update(s)");
    console.log("Updates:", updates);

    saveButton.disabled = true;

    const originalText = saveButton.innerText;

    saveButton.innerText = "Saving...";

    const jobs = newRows.map(function (entry) {
        return sendRow(API.save, entry.data);
    });

    if (updates.length > 0) {
        jobs.push(sendUpdates(API.upDate, updates));
    }

    Promise.all(jobs)
        .then(function (results) {

            // Results are in the same order the jobs were pushed:
            //   [ create#1, create#2, ..., updateBatch ]
            const createResults = results.slice(0, newRows.length);
            const updateResult  = updates.length > 0
                ? results[results.length - 1]
                : null;

            const lines = [];

            /* ---- create API ---- */

            if (createResults.length > 0) {
                lines.push(createResults.length + " item(s) created");
            }

            /* ---- update API ---- */

            if (updateResult) {

                const updatedCount = updateResult.updated_count ?? 0;
                const failedCount  = updateResult.failed_count  ?? 0;
                const failed       = updateResult.failed || [];

                lines.push(updatedCount + " item(s) updated.");

                if (failedCount > 0) {

                    lines.push("");
                    lines.push(failedCount + " item(s) failed:");

                    failed.forEach(function (entry) {

                        const id  = entry.id ?? "?";
                        const why = entry.error || entry.reason ||
                                    entry.message || JSON.stringify(entry);

                        lines.push("  \u2022 id " + id + ": " + why);
                    });
                }
            }

            const hasFailures = updateResult && (updateResult.failed_count ?? 0) > 0;

            showAlert(lines.join("\n"), {
                type:  hasFailures ? "warning" : "success",
                title: hasFailures ? "Saved with errors" : "Saved"
            });

            newRows.forEach(function (entry) { entry.row.remove(); });

            pendingUpdates.clear();

            // Reloading shows the true DB state
            fetchAndPopulate();
        })
        .catch(function (error) {

            console.error("Save error:", error);
            showAlert(error.message, { type: "error", title: "Save failed" });
        })
        .finally(function () {

            saveButton.innerText = originalText;
            refreshSaveButtonState();
        });
});


/* =========================================================
   CSV EXPORT (client-side, from the current result set)
   ========================================================= */

document.getElementById("downloadCsvBtn").addEventListener("click", function () {

    const headers = COLUMNS.map(function (column) { return column.label; });

    function cell(value) {
        return '"' + String(value ?? "").replace(/"/g, '""') + '"';
    }

    const rows = items.map(function (item) {

        return COLUMNS.map(function (column) {

            if (column.type === "active") {
                return cell(item.active ? "TRUE" : "FALSE");
            }

            return cell(item[column.key]);

        }).join(",");
    });

    const csv  = [headers.join(",")].concat(rows).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href     = url;
    link.download = "item_management.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
});


/* =========================================================
   CSV IMPORT
   ========================================================= */

const csvPopup   = document.getElementById("csvPopUp");
const csvOverlay = document.getElementById("csvLoadingOverlay");

let invalidRows = [];   // InvalidData from the last upload

const resultBox  = document.getElementById("resultBox");
const resultMsg  = document.getElementById("resultMsg");
const invalidMsg = document.getElementById("invalidMsg");

function resetInvalidBox() {
    invalidRows = [];
    resultBox.style.display = "none";
    resultMsg.textContent = "";
    invalidMsg.textContent = "";
}

function showResultBox(message, count) {
    resultMsg.textContent = message;
    invalidMsg.textContent =
        count + " row(s) were invalid and were NOT inserted. " +
        "Would you like to download them?";
    resultBox.style.display = "block";
}

// Preferred column order (matches your upload template); "reason" goes last
const INVALID_CSV_ORDER = [
    "change_type", "sales_organization_code", "distribution_channel_code",
    "sales_division_code", "condition_type", "customer_no", "customer_group",
    "customer_hierarchy", "location_code", "transportation_zone_code",
    "item_no", "uom", "minimum_quantity", "sales_price", "currency",
    "lower_limit", "upper_limit", "priority", "starting_date", "ending_date",
    "offer_article", "map", "tax_percent", "price_with_tax", "updated_from_sap"
];

// 2026-09-03 00:00:00  ->  09/03/2026 00:00   (US style, same as upload file)
function normalizeCsvDate(value) {
    const text = String(value ?? "").trim();
    const m = text.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::\d{2})?$/);
    return m ? m[2] + "/" + m[3] + "/" + m[1] + " " + m[4] + ":" + m[5] : text;
}

function downloadRowsAsCsv(rows, filename) {

    if (!rows || rows.length === 0) {
        return;
    }

    // All keys present in the data
    const found = new Set();
    rows.forEach(function (row) {
        Object.keys(row).forEach(function (key) { found.add(key); });
    });

    // Known columns first, then any unknown ones, then "reason" last
    const headers = INVALID_CSV_ORDER.filter(function (k) { return found.has(k); });
    found.forEach(function (k) {
        if (headers.indexOf(k) === -1 && k !== "reason") {
            headers.push(k);
        }
    });
    if (found.has("reason")) {
        headers.push("reason");
    }

    function csvCell(value) {
        if (value !== null && typeof value === "object") {
            value = JSON.stringify(value);
        }
        return '"' + String(value ?? "").replace(/"/g, '""') + '"';
    }

    function cellFor(row, key) {
        const value = row[key];
        return (key === "starting_date" || key === "ending_date")
            ? normalizeCsvDate(value)
            : value;
    }

    // Group identical reasons together so the file is easy to read
    const sorted = rows.slice().sort(function (a, b) {
        return String(a.reason ?? "").localeCompare(String(b.reason ?? ""));
    });

    const lines = [headers.map(csvCell).join(",")].concat(
        sorted.map(function (row) {
            return headers.map(function (h) { return csvCell(cellFor(row, h)); }).join(",");
        })
    );

    const blob = new Blob(["\uFEFF" + lines.join("\r\n")], {
        type: "text/csv;charset=utf-8;"
    });

    const url  = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href     = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}

document.getElementById("downloadInvalidBtn").addEventListener("click", function () {
    downloadRowsAsCsv(invalidRows, "Rejected_pricing_conditions.csv");
});

document.getElementById("importBtnUnique").addEventListener("click", function () {
    resetInvalidBox();
    csvPopup.style.display = "block";
});

document.getElementById("closeCsvPopup").addEventListener("click", function () {
    csvPopup.style.display = "none";
});

document.getElementById("cancelCsvBtn").addEventListener("click", function () {
    csvPopup.style.display = "none";
});

window.addEventListener("click", function (event) {

    if (event.target === csvPopup) {
        csvPopup.style.display = "none";
    }
});

document.getElementById("downloadSampleBtn").addEventListener("click", function () {

    const action = document.getElementById("actionSelect").value;

    window.location.href = API.sampleCsv + "?action=" + encodeURIComponent(action);
});

document.getElementById("uploadBtn").addEventListener("click", function () {

    const uploadButton = this;
    const fileInput    = document.getElementById("fileUpload");
    const file         = fileInput.files[0];

    if (!file) {
        showAlert("Please choose a CSV file to upload.", { type: "warning" });
        return;
    }

    const formData = new FormData();

    formData.append("file", file);
    formData.append("action", document.getElementById("actionSelect").value);

    resetInvalidBox();
    csvOverlay.style.display = "flex";

    uploadButton.disabled = true;

    const originalHtml = uploadButton.innerHTML;

    uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    fetch(API.import, { method: "POST", body: formData })
    .then(function (response) {

        // A 400 can still carry rejected rows, so read the body first.
        return response.json()
            .catch(function () {
                throw new Error("Server returned HTTP " + response.status);
            })
            .then(function (result) {
                return { ok: response.ok, result: result };
            });
    })
    .then(function (payload) {

        const result = payload.result;

        if (!payload.ok || result.success === false || result.status === "error") {

            // Friendly message first; keep raw DB error + row details
            const err   = new Error(result.message || result.error || "Import failed");
            err.failed  = result.failed_record || null;
            err.raw     = result.error || "";
            err.invalid = result.InvalidData || result.rejected_rows || [];
            throw err;
        }

        invalidRows = result.InvalidData || result.rejected_rows || [];

        fileInput.value = "";
        fetchAndPopulate();          // refresh table with newly inserted rows

        if (invalidRows.length > 0) {
            // Keep popup open, show the response in the second box
            showResultBox(result.message || "Upload finished", invalidRows.length);
        } else {
            showAlert(result.message || "CSV imported successfully.", {
                type: "success",
                title: "Import complete"
            });
            csvPopup.style.display = "none";
        }
    })
    .catch(function (error) {

        // Raw DB error to console, readable details to the user
        console.error("Import error:", error.raw || error);

        let text = error.message;

        // Details of the row that broke the import (from failed_record)
        if (error.failed) {
            text += "\n\nItem No: " + (error.failed.item_no ?? "-") +
                    "\nUOM: "       + (error.failed.uom ?? "-") +
                    "\nColumn: "    + (error.failed.column ?? "-") +
                    "\nValue: "     + (error.failed.value ?? "(empty)");
        }

        // If the server also sent rejected rows, offer them for download
        if (error.invalid && error.invalid.length > 0) {
            invalidRows = error.invalid;
            showResultBox("Upload failed", invalidRows.length);
        }

        showAlert(text, { type: "error", title: "Import failed" });
    })
    .finally(function () {

        csvOverlay.style.display = "none";

        uploadButton.disabled  = false;
        uploadButton.innerHTML = originalHtml;
    });
});


/* =========================================================
   WARN ON LEAVING WITH UNSAVED CHANGES
   (browsers only allow their own dialog here)
   ========================================================= */

window.addEventListener("beforeunload", function (event) {

    if (pendingUpdates.size > 0 || hasPendingNewRows()) {
        event.preventDefault();
        event.returnValue = "";
    }
});


/* =========================================================
   BOOT
   ========================================================= */

renderHead();
refreshSaveButtonState();
fetchAndPopulate();

});