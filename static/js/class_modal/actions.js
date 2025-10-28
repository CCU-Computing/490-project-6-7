// static/js/class_modal/actions.js
import {
  addModal, searchInput, searchBtn, addOpen, addClose, addCancel, addConfirm,
  results, getSemesters, remainingCredits, toNum,
  fetchSemesters, addClass, setSemesters
} from "../semesters/state_nav.js";
import { selectedCourseIds, loadAndRenderModal } from "./search.js";
import { showError } from "../context_menu/toast.js";

/* ---------------- scroll ---------------- */
function ensureResultsScrollable() {
  if (!results) return;
  results.classList.add("results-scroll", "flex", "flex-col", "gap-4", "w-full");
  results.style.minHeight = "0";
  results.style.height = "100%";
  const p = results.parentElement;
  if (p) {
    p.style.minHeight = "0";
    p.style.height = "100%";
    const cs = getComputedStyle(p);
    if (cs.display.includes("flex")) {
      p.style.display = "flex";
      p.style.flexDirection = "column";
      p.style.flex = "1 1 auto";
    }
  }
}

/* ---------------- helpers ---------------- */
const norm = (s) => String(s || "").trim().replace(/\s+/, " ").toUpperCase();

function currentPlannerIndex() {
  return Number(document.body.dataset.currentIndex || 0);
}
function currentPlannerOrder() {
  const idx = currentPlannerIndex();
  const sems = getSemesters() || [];
  return sems[idx]?.order ?? idx; // fallback
}
function plannedBeforeCodes() {
  const idx = currentPlannerIndex();
  const sems = getSemesters() || [];
  const out = new Set();
  for (let i = 0; i < sems.length; i++) {
    if (i >= idx) break;
    const s = sems[i];
    (s.classes || []).forEach(c => {
      if (c && c.code) out.add(norm(c.code));
    });
  }
  return out;
}

/* ---------------- inline prereq chips ---------------- */
function renderInlinePrereqBox(card, codes = []) {
  let box = card.querySelector(".prereq-not-met");
  if (!codes.length) {
    if (box) box.remove();
    return;
  }
  if (!box) {
    box = document.createElement("div");
    box.className = "prereq-not-met bg-yellow-50 border border-yellow-200 text-yellow-800 rounded px-2 py-1 mt-2";
    const anchor = card.querySelector(".modal-meta") || card.firstElementChild;
    anchor.insertAdjacentElement("afterend", box);
  }
  box.innerHTML = ""; // rebuild
  box.classList.add("flex", "items-center", "flex-wrap", "gap-1");

  const lbl = document.createElement("span");
  lbl.className = "text-xs font-medium";
  lbl.textContent = "Prerequisites not met:";
  box.appendChild(lbl);

  codes.forEach((code, i) => {
    const chip = document.createElement("span");
    chip.className = "chip chip-sm";
    chip.textContent = code;
    if (i > 0) {
      const comma = document.createElement("span");
      comma.className = "pr-comma";
      comma.textContent = ", ";
      box.appendChild(comma);
    }
    box.appendChild(chip);
  });
}

/* ---------------- requirements fetch ---------------- */
async function fetchRequirements(q, currentTerm) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (currentTerm) params.set("current_term", currentTerm);
  params.set("current_order", String(currentPlannerOrder()));
  const urls = [
    `/api/requirements?program=BS-CS-Core-2025&${params.toString()}`,
    `/api/requirements?program=BS-CS-Foundations-2025&${params.toString()}`,
  ];
  const res = await Promise.all(urls.map(u => fetch(u).catch(() => null)));
  const payloads = [];
  for (const r of res) if (r && r.ok) payloads.push(await r.json());
  return payloads;
}

/* ---------------- decorate cards only ---------------- */
function decorateCardWithItem(card, item) {
  // meta row
  let meta = card.querySelector(".modal-meta");
  if (!meta) {
    meta = document.createElement("div");
    meta.className = "modal-meta flex flex-wrap items-center gap-2";
    const titleEl = card.querySelector(".chip-title, .title, h3, h4, .modal-title") || card.firstElementChild || card;
    titleEl.insertAdjacentElement("afterend", meta);
  } else {
    meta.innerHTML = "";
  }

  // offered chips
  const offeredWrap = document.createElement("div");
  offeredWrap.className = "offered flex flex-wrap items-center gap-1";
  (item.offered_terms || []).forEach(term => {
    const t = document.createElement("span");
    t.className = "chip chip-xs";
    t.textContent = term;
    offeredWrap.appendChild(t);
  });
  if (item.offered_this_term) {
    const now = document.createElement("span");
    now.className = "chip chip-xs";
    now.textContent = "This term";
    offeredWrap.appendChild(now);
  }
  if (offeredWrap.childElementCount > 0) meta.appendChild(offeredWrap);

  // planned-aware unmet list
  const unmet = Array.isArray(item.unmet_prereqs_planned) ? item.unmet_prereqs_planned : (item.unmet_prereqs || []);
  renderInlinePrereqBox(card, unmet);

  // disable add with planned-aware flag
  const effectiveOk = item.prereq_ok_planned !== undefined ? item.prereq_ok_planned : item.prereq_ok;
  const btn = card.querySelector("button, .btn-add, [data-action='add']");
  if (btn) {
    const dis = !!(item.taken || item.assigned || !effectiveOk);
    btn.toggleAttribute("disabled", dis);
    if (dis) btn.classList.add("opacity-50", "pointer-events-none");
    else btn.classList.remove("opacity-50", "pointer-events-none");
  }
}

function purgeDataTitleGroups() {
  results.querySelectorAll('section.modal-group[data-title]').forEach(n => n.remove());
}

function hydrateFlatList(payloads) {
  const idMap = new Map();
  payloads.forEach(p => (p.groups || []).forEach(g => (g.courses || []).forEach(it => idMap.set(it.id, it))));
  purgeDataTitleGroups();

  const cards = Array.from(results.querySelectorAll(".modal-card"));
  cards.forEach(card => {
    const id = Number(card.dataset.id || NaN);
    const item = idMap.get(id);
    if (item) decorateCardWithItem(card, item);
  });
}

/* ---------------- planner term ---------------- */
function currentPlannerTermUpper() {
  const idx = Number(document.body.dataset.currentIndex || 0);
  const sem = getSemesters()[idx];
  if (sem) document.body.dataset.currentSemesterId = String(sem.id || "");
  return (sem?.term || "").trim().toUpperCase();
}

/* ---------------- hydrate ---------------- */
async function hydrateModal() {
  const q = (searchInput?.value || "").trim();
  const term = currentPlannerTermUpper();

  try {
    const payloads = await fetchRequirements(q, term);
    hydrateFlatList(payloads);
  } catch {
    purgeDataTitleGroups();
  }
}

/* ---------------- open/close ---------------- */
export function openAddModal() {
  selectedCourseIds.clear();
  const sc = document.getElementById("modal-selected-count");
  if (sc) sc.textContent = "0 selected";
  addModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  ensureResultsScrollable();

  loadAndRenderModal("", currentPlannerTermUpper());

  setTimeout(hydrateModal, 0);
}
export function closeAddModal() {
  addModal.classList.add("hidden");
  document.body.style.overflow = "";
}

/* ---------------- add ---------------- */
function isCourseAssigned(catalogId){
  const idStr = String(catalogId);
  for (const s of getSemesters()) {
    if ((s.classes || []).some(c => String(c.catalog_id) === idStr)) return true;
  }
  return false;
}
async function fetchCourseLocalOrServer(id) {
  const el = results?.querySelector(`.modal-card[data-id="${id}"] .chip-sub`);
  if (el) {
    const m = el.textContent?.match(/(\d+(\.\d+)?)\s*credits/i);
    const credits = m ? Number(m[1]) : 0;
    return { id: Number(id), credits };
  }
  return { id: Number(id), credits: 0 };
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
    if (isCourseAssigned(catalogId)) { blockedAssigned = true; continue; }
    try {
      const { credits } = await fetchCourseLocalOrServer(catalogId);
      const need = toNum(credits);
      if (need <= 0) continue;
      if (need > remaining) { blockedCredits = true; continue; }

      await addClass(Number(catalogId), Number(sem.id));
      remaining -= need;
      added++;
    } catch { /* ignore */ }
  }

  try {
    const data = await fetchSemesters();
    setSemesters(data);
    window.dispatchEvent(new Event("planner:render"));
    window.dispatchEvent(new Event("planner:reload"));
    setTimeout(hydrateModal, 0);
  } catch {
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

  const reload = () => {
    ensureResultsScrollable();
    loadAndRenderModal(searchInput.value, currentPlannerTermUpper());
    setTimeout(hydrateModal, 0);
  };
  searchBtn?.addEventListener("click", reload);

  let searchTimer = null;
  searchInput?.addEventListener("input", () => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(reload, 150);
  });

  setTimeout(reload, 0);
}
