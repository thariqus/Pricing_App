const form = document.getElementById("settings-form");
const body = document.getElementById("sites-body");
const rowTemplate = document.getElementById("site-row");
const msg = document.getElementById("settings-msg");
const saveBtn = document.getElementById("save-btn");

function renumber() {
  [...body.rows].forEach((row, i) => { row.querySelector(".sl").textContent = i + 1; });
}

function addRow() {
  body.append(rowTemplate.content.cloneNode(true));
  renumber();
  body.lastElementChild.querySelector(".site-location").focus();
}

document.getElementById("add-row-btn").addEventListener("click", addRow);

body.addEventListener("click", e => {
  const btn = e.target.closest(".remove-row-btn");
  if (!btn) return;
  btn.closest("tr").remove();
  renumber();
});

function showMessage(text, isError) {
  msg.hidden = false;
  msg.className = `settings-msg ${isError ? "error" : "ok"}`;
  msg.replaceChildren(...[].concat(text).map(t => Object.assign(document.createElement("div"), { textContent: t })));
}

saveBtn.addEventListener("click", async () => {
  const f = form.elements;
  const payload = {
    ho_url: f.ho_url.value,
    db_port: f.db_port.value,
    db_user: f.db_user.value,
    db_password: f.db_password.value,
    is_central: f.is_central.checked,
    sites: [...body.rows].map(row => ({
      location: row.querySelector(".site-location").value,
      ip: row.querySelector(".site-ip").value,
    })),
  };

  saveBtn.disabled = true;
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  saveBtn.disabled = false;

  const data = await res.json();
  if (!res.ok) {
    showMessage(data.errors || "Save failed.", true);
    return;
  }
  showMessage("Settings saved.", false);
});

renumber();
if (!body.rows.length) addRow();
