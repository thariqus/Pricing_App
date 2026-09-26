const table = document.querySelector(".items-table");
const siteCode = table.dataset.site;
const pageSize = Number(table.dataset.pageSize);
const rows = [...table.tBodies[0].rows];
const pager = document.getElementById("pager");
const liveBtn = document.getElementById("live-btn");

// Live toggle: red when off, green when on; page buttons hidden while live
liveBtn.addEventListener("click", () => {
  const on = liveBtn.classList.toggle("on");
  liveBtn.setAttribute("aria-pressed", on);
  pager.hidden = on;
});

// Pagination: one button per block of `pageSize` rows (100, 200, 300, ...)
const pageCount = Math.ceil(rows.length / pageSize);

function showPage(page) {
  rows.forEach((row, i) => {
    row.hidden = Math.floor(i / pageSize) !== page;
  });
  pager.querySelectorAll("button").forEach((btn, i) => btn.classList.toggle("active", i === page));
}

for (let p = 0; p < pageCount; p++) {
  const btn = document.createElement("button");
  btn.textContent = Math.min((p + 1) * pageSize, rows.length);
  btn.addEventListener("click", () => showPage(p));
  pager.append(btn);
}
showPage(0);

// Retry confirmation popup
const modal = document.getElementById("retry-modal");
const modalMsg = document.getElementById("retry-msg");
let pendingBtn = null;

function openRetryModal(btn) {
  pendingBtn = btn;
  const itemCode = btn.closest("tr").cells[1].textContent.trim();
  modalMsg.innerHTML = "";
  modalMsg.append("Retry replication to site ");
  modalMsg.append(Object.assign(document.createElement("strong"), { textContent: siteCode }));
  modalMsg.append(" for all prices of item code ");
  modalMsg.append(Object.assign(document.createElement("strong"), { textContent: itemCode }));
  modalMsg.append("?");
  modal.hidden = false;
  document.getElementById("retry-ok").focus();
}

function closeRetryModal() {
  modal.hidden = true;
  pendingBtn = null;
}

document.getElementById("retry-close").addEventListener("click", closeRetryModal);
modal.addEventListener("click", e => { if (e.target === modal) closeRetryModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape" && !modal.hidden) closeRetryModal(); });
document.getElementById("retry-ok").addEventListener("click", () => {
  const btn = pendingBtn;
  closeRetryModal();
  if (btn) retryItem(btn);
});

table.addEventListener("click", e => {
  const btn = e.target.closest(".retry-btn");
  if (btn) openRetryModal(btn);
});

// Retry an item
async function retryItem(btn) {
  const row = btn.closest("tr");
  btn.disabled = true;
  btn.textContent = "Retrying…";
  const res = await fetch(`/api/sites/${siteCode}/items/${row.dataset.sl}/retry`, { method: "POST" });
  if (!res.ok) {
    btn.disabled = false;
    btn.textContent = "Retry";
    return;
  }
  const item = await res.json();
  const badge = row.querySelector(".badge");
  badge.className = `badge ${item.status.toLowerCase()}`;
  badge.textContent = item.status;
  btn.textContent = "Retry";
  btn.disabled = item.status === "Success";
}
