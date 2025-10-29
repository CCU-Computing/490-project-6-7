// static/js/class_modal/search.js
import { results, selectedCount } from "../semesters/state_nav.js";

export const selectedCourseIds = new Set(); // stores catalogId (c.catalog_id ?? c.id) as strings
const expandedGroupIds = new Set(); // collapsed/expanded state per group
let CURRENT_TERM_UPPER = ""; // set by loadAndRenderModal()

/* ---------- style bootstrap (first-open safety) ---------- */
function ensurePlannerStyles() {
  const has = Array.from(document.styleSheets).some(s => {
    try { return (s.href || "").includes("planner.css"); } catch { return false; }
  });
  if (!has) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/static/css/planner.css";
    document.head.appendChild(link);
  }
}

/* ensure/return the grid container inside a group's body */
function getOrCreateGrid(body) {
  let grid = body.querySelector(":scope > .modal-grid");
  if (!grid) {
    grid = document.createElement("div");
    grid.className = "modal-grid";
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(3, minmax(0, 1fr))";
    grid.style.gap = "0.5rem";
    grid.style.alignItems = "stretch";
    // move any existing cards into the grid
    Array.from(body.querySelectorAll(":scope > .modal-card")).forEach(card => grid.appendChild(card));
    body.appendChild(grid);
  }
  return grid;
}

/* ---------- UI helpers ---------- */

function termChipsFull(offered_terms) {
  const ALL = ["SPRING", "SUMMER", "FALL"];
  const LABEL = { SPRING: "Spring", SUMMER: "Summer", FALL: "Fall" };
  const set = new Set((offered_terms || []).map(s => String(s || "").toUpperCase()));

  const row = document.createElement("div");
  row.className = "flex items-center gap-1 mt-1 pb-2 offered-row";

  ALL.forEach((t) => {
    const chip = document.createElement("span");
    const enabled = set.has(t);
    chip.className = [
      "inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] leading-4 whitespace-nowrap",
      enabled
        ? "border-gray-400 bg-gray-100 text-gray-800"
        : "border-gray-300 text-gray-500 opacity-50"
    ].join(" ");
    chip.textContent = LABEL[t];
    row.appendChild(chip);
  });

  if (
    CURRENT_TERM_UPPER &&
    Array.isArray(offered_terms) &&
    offered_terms.length > 0 &&
    !offered_terms.map(s => String(s).toUpperCase()).includes(CURRENT_TERM_UPPER)
  ) {
    const ctx = document.createElement("span");
    ctx.className = "ml-auto text-[10px] text-gray-600 whitespace-nowrap";
    const nice = CURRENT_TERM_UPPER[0] + CURRENT_TERM_UPPER.slice(1).toLowerCase();
    ctx.textContent = `Not typically offered in ${nice}`;
    row.appendChild(ctx);
  }

  return row;
}

// Styled yellow box with unmet prereqs listed
function prereqWarningBox(unmetList) {
  const has = Array.isArray(unmetList) && unmetList.length > 0;
  const box = document.createElement("div");
  box.className = "prereq-box " + (has ? "warn" : "spacer");

  if (has) {
    const head = document.createElement("span");
    head.className = "font-medium mr-1";
    head.textContent = "Prerequisites not met:";
    const span = document.createElement("span");
    span.className = "flex-1";
    span.textContent = unmetList.join(", ");
    box.appendChild(head);
    box.appendChild(span);
  } else {
    box.appendChild(document.createElement("span"));
  }
  return box;
}

/* ---------- Card ---------- */

function courseCard(c) {
  const catalogId = String(c.catalog_id ?? c.id);

  const card = document.createElement("div");
  card.className = "modal-card relative flex flex-col gap-2 p-2 rounded border";
  card.dataset.id = String(c.id);
  card.dataset.catalogId = catalogId;
  card.dataset.selected = selectedCourseIds.has(catalogId) ? "true" : "false";
  card.style.gridColumn = "auto"; // never span full width

  let disabled = !!c.disabled;
  const isPlanned = !!(c.taken || c.assigned);
  const prereqNotMet = !c.prereq_ok;

  // state classes (CSS handles background)
  card.classList.remove("is-planned","is-blocked","is-available","border-green-500","border-yellow-500","border-gray-200");
  if (isPlanned) {
    card.classList.add("is-planned", "border-green-500");
    disabled = true;
  } else if (prereqNotMet) {
    card.classList.add("is-blocked", "border-yellow-500");
    disabled = true;
  } else {
    card.classList.add("is-available", "border-gray-200");
  }

  const content = document.createElement("div");
  content.className = "flex-1 flex flex-col";

  const headerRow = document.createElement("div");
  headerRow.className = "flex items-start gap-2";

  const title = document.createElement("div");
  title.className = "text-sm font-semibold chip-title two-line-title flex-1";
  title.textContent = `${c.code} · ${c.title}`;

  const rightHead = document.createElement("div");
  rightHead.className = "flex items-center gap-2 shrink-0";

  const credits = document.createElement("div");
  credits.className = "chip-credits text-xs text-gray-600";
  credits.textContent = `${c.credits || 0} credits`;

  const toggle = document.createElement("input");
  toggle.type = "checkbox";
  toggle.checked = selectedCourseIds.has(catalogId);
  toggle.disabled = disabled;
  if (disabled) toggle.setAttribute("aria-disabled", "true");

  rightHead.appendChild(credits);
  rightHead.appendChild(toggle);

  headerRow.appendChild(title);
  headerRow.appendChild(rightHead);

  const chipsRow = termChipsFull(c.offered_terms || []);
  const unmet = Array.isArray(c.unmet_prereqs) ? c.unmet_prereqs : [];
  const prereqRow = prereqWarningBox(prereqNotMet ? unmet : []);

  const state = document.createElement("div");
  state.className = "text-[11px] mt-1";
  if (c.taken) { state.textContent = "Completed"; state.classList.add("text-green-600"); }
  else if (c.assigned) { state.textContent = "Already in your plan"; state.classList.add("text-gray-600"); }

  const toggleSelection = (on) => {
    if (disabled) return;
    if (on) selectedCourseIds.add(catalogId); else selectedCourseIds.delete(catalogId);
    card.dataset.selected = on ? "true" : "false";
    selectedCount.textContent = `${selectedCourseIds.size} selected`;
  };
  toggle.addEventListener("click", (e) => { e.stopPropagation(); toggleSelection(toggle.checked); });
  card.addEventListener("click", () => {
    if (disabled) return;
    const next = !selectedCourseIds.has(catalogId);
    toggle.checked = next;
    toggleSelection(next);
  });

  card.style.minHeight = "154px";

  content.appendChild(headerRow);
  content.appendChild(chipsRow);
  content.appendChild(prereqRow);
  if (isPlanned) content.appendChild(state);

  card.appendChild(content);
  return card;
}

/* ---------- Group ---------- */

function groupSection(g) {
  const sec = document.createElement("section");
  sec.className = "modal-group w-full rounded border border-gray-200 bg-slate-50";
  sec.dataset.groupId = String(g.group_id);

  const header = document.createElement("button");
  header.type = "button";
  header.className = "w-full flex items-center gap-2 p-2 modal-group-header sticky top-0 z-20 bg-inherit";
  header.setAttribute("aria-expanded", expandedGroupIds.has(g.group_id) ? "true" : "false");

  const hLeft = document.createElement("div");
  hLeft.className = "group-title font-semibold truncate";
  hLeft.textContent = g.title;

  const caret = document.createElement("span");
  caret.className = "text-xs select-none";
  caret.textContent = expandedGroupIds.has(g.group_id) ? "▾" : "▸";

  const hRight = document.createElement("div");
  hRight.className = "flex items-center gap-2";
  hRight.appendChild(caret);

  header.appendChild(hLeft);
  header.appendChild(hRight);

  const body = document.createElement("div");
  body.className = "px-2 pb-3 modal-group-body";
  if (!expandedGroupIds.has(g.group_id)) body.style.display = "none";

  const grid = getOrCreateGrid(body);

  (g.courses || []).forEach((c) => {
    const card = courseCard(c);
    card.classList.add("h-full");
    grid.appendChild(card);
  });

  header.addEventListener("click", () => {
    const nowOpen = body.style.display === "none";
    body.style.display = nowOpen ? "block" : "none";
    header.setAttribute("aria-expanded", nowOpen ? "true" : "false");
    caret.textContent = nowOpen ? "▾" : "▸";
    if (nowOpen) expandedGroupIds.add(g.group_id); else expandedGroupIds.delete(g.group_id);
  });

  sec.appendChild(header);
  sec.appendChild(body);
  return sec;
}

/* ---------- Render ---------- */

export function renderModalGroups(groups) {
  ensurePlannerStyles();
  if (!results) return;
  results.className = "";
  results.classList.add("results-scroll", "flex", "flex-col", "gap-4", "w-full");
  results.style.overflowX = "hidden";
  results.style.overflowY = "auto";

  if (expandedGroupIds.size === 0) {
    (groups || []).forEach(g => expandedGroupIds.add(g.group_id));
  }

  results.innerHTML = "";
  (groups || []).forEach((g) => results.appendChild(groupSection(g)));
}

/* ---------- Fetch + render ---------- */

export async function loadAndRenderModal(q, currentTermUpper) {
  ensurePlannerStyles();
  CURRENT_TERM_UPPER = String(currentTermUpper || "").toUpperCase();
  const url = new URL("/api/requirements", window.location.origin);
  if (q && q.trim()) url.searchParams.set("q", q.trim());
  if (CURRENT_TERM_UPPER) url.searchParams.set("current_term", CURRENT_TERM_UPPER);
  const r = await fetch(url.toString());
  if (!r.ok) throw new Error("failed to load requirements");
  const data = await r.json();
  renderModalGroups(data.groups || []);
  return true;
}
