// static/js/modal/actions.js
import {
  addModal, searchInput, searchBtn, addOpen, addClose, addCancel, addConfirm,
  results, getSemesters, remainingCredits, toNum,
  fetchSemesters, addClass, setSemesters
} from "../semesters/state_nav.js";
import { selectedCourseIds, loadAndRenderModal } from "./search.js";
import { showError } from "../context_menu/toast.js";

const LOG_NS = "modal/actions";

/* ---------------- helpers ---------------- */
function currentPlannerIndex() {
  const v = Number(document.body.dataset.currentIndex || 0);
  return v;
}
function currentPlannerOrder() {
  const idx = currentPlannerIndex();
  const sems = getSemesters() || [];
  return sems[idx]?.order ?? idx;
}
function currentPlannerId() {
  const idx = currentPlannerIndex();
  const sems = getSemesters() || [];
  return sems[idx]?.id || null;
}
function currentPlannerTermUpper() {
  const idx = currentPlannerIndex();
  const sems = getSemesters() || [];
  const sem = sems[idx];
  if (sem) document.body.dataset.currentSemesterId = String(sem.id || "");
  return (sem?.term || "").trim().toUpperCase();
}

/* Canonicalize catalog identity */
function catalogKey(v) {
  if (v == null) return "";
  const s = String(v).trim();
  return s.toUpperCase().replace(/\s+/g, "").replace(/-/g, "");
}

/* Ensure a grid wrapper exists inside a group's body and return it */
function getOrCreateGrid(body) {
  let grid = body.querySelector(":scope > .modal-grid");
  if (!grid) {
    grid = document.createElement("div");
    grid.className = "modal-grid";
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(3, minmax(0, 1fr))";
    grid.style.gap = "0.5rem";
    grid.style.alignItems = "stretch";
    // move any stray cards into the grid (fixes earlier sort bug)
    Array.from(body.querySelectorAll(":scope > .modal-card")).forEach(card => grid.appendChild(card));
    body.appendChild(grid);
  }
  return grid;
}

/* ---------------- requirements fetch ---------------- */
async function fetchRequirements(q, currentTerm) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (currentTerm) params.set("current_term", currentTerm);
  params.set("current_order", String(currentPlannerOrder()));
  const curId = currentPlannerId();
  if (curId) params.set("current_semester_id", String(curId));

  const urls = [`/api/requirements?${params.toString()}`];
  const res = await Promise.all(urls.map(u => fetch(u).catch(() => null)));
  const payloads = [];
  for (const r of res) {
    if (!r) continue;
    if (!r.ok) continue;
    payloads.push(await r.json());
  }
  return payloads;
}

/* ---------------- group progress ---------------- */
function normalizeTitle(txt) {
  return (txt || "")
    .replace(/\d+\s*\/\s*\d+.*$/u, "")
    .replace(/[▾▸►▼▲▷◁⯆⯈]+$/u, "")
    .replace(/\s+/g, " ")
    .trim();
}
function readHeaderTitle(header) {
  const raw =
    header.querySelector(".group-title")?.textContent ??
    header.getAttribute("data-group-title") ??
    header.textContent ??
    "";
  return normalizeTitle(raw);
}

function getOrCreateProgress(slot) {
  let box = slot.querySelector(".group-progress");
  if (!box) {
    box = document.createElement("div");
    box.className = "group-progress";
    const bar = document.createElement("div");
    bar.className = "group-progress-bar";
    const fill = document.createElement("div");
    fill.className = "group-progress-fill";
    bar.appendChild(fill);
    const txt = document.createElement("span");
    txt.className = "group-progress-text";
    box.appendChild(bar);
    box.appendChild(txt);
    box.style.marginLeft = "auto";
    slot.appendChild(box);
  }
  return box;
}
function updateProgressUI(header, planned, required) {
  const box = getOrCreateProgress(header);
  const pct = required > 0 ? Math.min(100, Math.round((Math.min(planned, required) / required) * 100)) : 0;
  const fill = box.querySelector(".group-progress-fill");
  fill.style.width = pct + "%";
  const txt = box.querySelector(".group-progress-text");
  txt.textContent = `${Math.min(planned, required)}/${required}`;
}

/* Assigned courses from current semesters (authoritative) */
function currentAssignedCatalogSet() {
  const out = new Set();
  const sems = getSemesters() || [];
  for (const s of sems) {
    for (const c of (s.classes || [])) {
      const k = catalogKey(c.catalog_id ?? c.catalogId ?? c.code ?? c.id);
      if (k) out.add(k);
    }
  }
  return out;
}
function isCourseAssignedByCatalog(catKey) {
  if (!catKey) return false;
  return currentAssignedCatalogSet().has(catalogKey(catKey));
}

/* ---------------- sort (fixed to sort inside GRID) ---------------- */
function sortCardsByPlannerCriteria(body) {
  const grid = getOrCreateGrid(body);
  const cards = Array.from(grid.querySelectorAll(":scope > .modal-card"));
  const withKey = cards.map(card => {
    const codeVal = (card.dataset.codeVal || card.dataset.catalogId || "").toString();
    return { el: card, code: codeVal };
  });
  withKey.sort((a, b) => a.code.localeCompare(b.code));
  const frag = document.createDocumentFragment();
  withKey.forEach(x => frag.appendChild(x.el));
  grid.appendChild(frag);
}

/* ---------------- ensure structure ---------------- */
function ensureGroupStructure(section) {
  let header = section.querySelector(":scope .modal-group-header");
  if (!header) { header = section.firstElementChild; if (header) header.classList.add("modal-group-header"); }
  let body = section.querySelector(":scope .modal-group-body");
  if (!body) {
    body = document.createElement("div");
    body.className = "modal-group-body";
    if (header && header.nextSibling) section.insertBefore(body, header.nextSibling); else section.appendChild(body);
  }
  // always ensure a grid inside body
  getOrCreateGrid(body);
  const clean = readHeaderTitle(header);
  if (clean) section.dataset.groupTitle = clean;
  return { header, body };
}

/* ---------------- hydrate ---------------- */
function setCardStateClasses(card, { planned, prereqOk }) {
  // remove any previous state classes
  card.classList.remove("is-planned", "is-blocked", "is-available", "border-green-500", "border-yellow-500", "border-gray-200");
  if (planned) {
    card.classList.add("is-planned", "border-green-500");
  } else if (!prereqOk) {
    card.classList.add("is-blocked", "border-yellow-500");
  } else {
    card.classList.add("is-available", "border-gray-200");
  }
}

function hydrateFlatList(payloads) {
  const idToGroup = new Map();
  const idMap = new Map();

  payloads.forEach(p => {
    (p.groups || []).forEach(g => {
      idToGroup.set(g.group_id, g);
      (g.courses || []).forEach(it => idMap.set(it.id, it));
    });
  });

  const sections = Array.from(results.querySelectorAll("section.modal-group"));
  sections.forEach(sec => {
    const { header, body } = ensureGroupStructure(sec);
    const grid = getOrCreateGrid(body);

    const cards = Array.from(grid.querySelectorAll(":scope > .modal-card"));
    cards.forEach(card => {
      const id = Number(card.dataset.id || NaN);
      const item = idMap.get(id);
      if (!item) return;

      const code = (item.code || "");
      const catKey = code.replace(/\s+/g,"").toUpperCase();
      card.dataset.codeVal = catKey;

      const btn = card.querySelector("input[type='checkbox']");
      const planned = isCourseAssignedByCatalog(code) || !!(item.taken || item.assigned);
      const prereqOk = !!(item.prereq_ok_planned ?? item.prereq_ok);

      if (btn) btn.toggleAttribute("disabled", !!(planned || !prereqOk));
      setCardStateClasses(card, { planned, prereqOk });
    });

    sortCardsByPlannerCriteria(body);

    if (header) {
      const gid = Number(sec.dataset.groupId || header.getAttribute("data-group-id") || NaN);
      const group = !Number.isNaN(gid) ? idToGroup.get(gid) : null;
      if (group) {
        const assigned = currentAssignedCatalogSet();
        let plannedCt = 0;
        for (const it of (group.courses || [])) {
          const code = (it.code || "").replace(/\s+/g,"").toUpperCase();
          if (assigned.has(code) || it.taken || it.assigned) plannedCt++;
        }
        const required = Number(group.required_count || 0);
        updateProgressUI(header, plannedCt, required);
      }
    }
  });
}

async function hydrateModal() {
  const q = (searchInput?.value || "").trim();
  const term = currentPlannerTermUpper();
  const payloads = await fetchRequirements(q, term);
  hydrateFlatList(payloads);
}

/* ---------------- open/close ---------------- */
export async function openAddModal() {
  selectedCourseIds.clear();
  const sc = document.getElementById("modal-selected-count");
  if (sc) sc.textContent = "0 selected";
  addModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";

  const term = currentPlannerTermUpper();
  try {
    await loadAndRenderModal("", term);
  } catch (e) {
    // ignore
  }
  await hydrateModal().catch(() => {});
}

export function closeAddModal() {
  addModal.classList.add("hidden");
  document.body.style.overflow = "";
}

/* ---------------- add ---------------- */
async function fetchCourseLocalOrServerByCatalogId(catalogId) {
  const el = results?.querySelector(`.modal-card[data-catalog-id="${catalogId}"] .chip-credits`);
  if (el) {
    const m = el.textContent?.match(/(\d+(\.\d+)?)\s*credits/i);
    const credits = m ? Number(m[1]) : 0;
    return { id: Number(catalogId), credits };
  }
  return { id: Number(catalogId), credits: 0 };
}

export async function addSelectedToCurrentSemester(currentIndex) {
  const semesters = getSemesters();
  const sem = semesters[currentIndex];
  if (!sem) { closeAddModal(); return; }

  const ids = Array.from(selectedCourseIds);
  if (!ids.length) { closeAddModal(); return; }

  let remaining = remainingCredits(sem);
  let added = 0, blockedCredits = false, blockedAssigned = false;

  for (const catalogId of ids) {
    const catKey = catalogKey(catalogId);
    if (isCourseAssignedByCatalog(catKey)) { blockedAssigned = true; continue; }
    try {
      const { credits } = await fetchCourseLocalOrServerByCatalogId(catalogId);
      const need = toNum(credits);
      if (need <= 0) continue;
      if (need > remaining) { blockedCredits = true; continue; }
      await addClass(Number(catalogId), Number(sem.id));
      remaining -= need;
      added++;
    } catch (e) { /* no-op */ }
  }

  try {
    const data = await fetchSemesters();
    setSemesters(data);
    await hydrateModal();
    window.dispatchEvent(new Event("planner:render"));
    window.dispatchEvent(new Event("planner:reload"));
  } catch (e) {
    showError("Failed to refresh semesters.");
  }

  closeAddModal();
  if (blockedAssigned) showError("Some courses are already scheduled.");
  if (blockedCredits)  showError("Credit limit exceeded. Max 18 per semester.");
  if (!added && !blockedAssigned && !blockedCredits) showError("No courses were added.");
}

/* ---------------- bind ---------------- */
export function bindModalControls() {
  addOpen?.addEventListener("click", openAddModal);
  addClose?.addEventListener("click", closeAddModal);
  addCancel?.addEventListener("click", closeAddModal);
  addConfirm?.addEventListener("click", () => {
    const idx = Number(document.body.dataset.currentIndex || 0);
    addSelectedToCurrentSemester(idx);
  });

  const reload = async () => {
    const term = currentPlannerTermUpper();
    await loadAndRenderModal(searchInput.value, term);
    await hydrateModal().catch(() => {});
  };
  searchBtn?.addEventListener("click", reload);

  let searchTimer = null;
  searchInput?.addEventListener("input", () => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(reload, 150);
  });

  window.addEventListener("planner:render", () => setTimeout(() => { hydrateModal().catch(() => {}); }, 0));
  window.addEventListener("planner:reload", () => setTimeout(() => { hydrateModal().catch(() => {}); }, 0));
}
