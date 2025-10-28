// static/js/class_modal/search.js
import { results, selectedCount } from "../semesters/state_nav.js";

export const selectedCourseIds = new Set();
const expandedGroupIds = new Set(); // collapsed/expanded state per group

// ---------------- UI helpers ----------------
function progressBar(completed, required) {
  const pct = required > 0 ? Math.min(100, Math.round((completed / required) * 100)) : 0;
  const wrap = document.createElement("div");
  wrap.className = "w-full mt-1 h-2 bg-gray-200 rounded";
  const fill = document.createElement("div");
  fill.className = "h-2 rounded";
  fill.style.width = `${pct}%`;
  wrap.appendChild(fill);
  fill.classList.add(pct >= 100 ? "bg-green-500" : "bg-blue-500");
  return wrap;
}

function termChips(offered_terms) {
  const row = document.createElement("div");
  row.className = "flex gap-1 flex-wrap mt-1";
  const all = ["SPRING","SUMMER","FALL"];
  const set = new Set(offered_terms || []);
  for (const t of all) {
    const chip = document.createElement("span");
    chip.className = "text-[10px] px-1.5 py-0.5 rounded border";
    chip.textContent = t[0] + t.slice(1).toLowerCase();
    if (set.has(t)) chip.classList.add("border-gray-300");
    else chip.classList.add("opacity-40", "border-gray-300");
    row.appendChild(chip);
  }
  if (!offered_terms || offered_terms.length === 0) {
    const chip = document.createElement("span");
    chip.className = "text-[10px] px-1.5 py-0.5 rounded border opacity-60";
    chip.textContent = "As needed";
    row.appendChild(chip);
  }
  return row;
}

// unmet prereqs block (count + list)
function unmetPrereqBlock(c) {
  if (c.prereq_ok) return document.createElement("div");
  const list = Array.isArray(c.unmet_prereqs) ? c.unmet_prereqs : [];
  const box = document.createElement("div");
  box.className = "text-[11px] mt-0.5 text-yellow-700";
  const head = document.createElement("div");
  head.textContent = `Prerequisites not met (${list.length})`;
  box.appendChild(head);
  if (list.length) {
    const ul = document.createElement("ul");
    ul.className = "list-disc ml-4";
    list.slice(0, 8).forEach(p => {
      const li = document.createElement("li");
      li.textContent = p;
      ul.appendChild(li);
    });
    if (list.length > 8) {
      const more = document.createElement("div");
      more.textContent = `+${list.length - 8} more`;
      ul.appendChild(more);
    }
    box.appendChild(ul);
  }
  return box;
}

function courseCard(c) {
  const card = document.createElement("div");
  card.className = "modal-card flex items-center justify-between gap-3 p-2 rounded border";
  card.dataset.id = String(c.id);
  card.dataset.selected = selectedCourseIds.has(String(c.id)) ? "true" : "false";

  let disabled = !!c.disabled;
  if (c.taken) {
    card.classList.add("border-green-500", "opacity-60");
    disabled = true;
  } else if (c.assigned) {
    card.classList.add("border-gray-500", "opacity-60");
    disabled = true;
  } else if (!c.prereq_ok) {
    card.classList.add("border-yellow-500", "opacity-80");
    disabled = true;
  } else {
    card.classList.add("border-gray-200");
    if (!c.offered_this_term) card.classList.add("opacity-90");
  }

  const left = document.createElement("div");
  left.className = "min-w-0 flex-1";
  const title = document.createElement("div");
  title.className = "text-sm font-semibold chip-title flex items-center gap-2 truncate";
  title.textContent = `${c.code} · ${c.title}`;

  const sub = document.createElement("div");
  sub.className = "text-xs text-gray-500 chip-sub";
  sub.textContent = `${c.credits || 0} credits`;

  const chips = termChips(c.offered_terms || []);

  const stateHint = document.createElement("div");
  stateHint.className = "text-[11px] mt-0.5";
  if (c.taken) { stateHint.textContent = "Completed"; stateHint.classList.add("text-green-600"); }
  else if (c.assigned) { stateHint.textContent = "Already in your plan"; stateHint.classList.add("text-gray-600"); }
  else if (!c.prereq_ok && (!c.unmet_prereqs || c.unmet_prereqs.length === 0)) { stateHint.textContent = "Prerequisites not met"; stateHint.classList.add("text-yellow-700"); }
  else if (!c.offered_this_term) { stateHint.textContent = "Not typically offered this term"; stateHint.classList.add("text-gray-500"); }

  left.appendChild(title);
  left.appendChild(sub);
  left.appendChild(chips);
  if (stateHint.textContent) left.appendChild(stateHint);
  if (!c.prereq_ok) left.appendChild(unmetPrereqBlock(c));

  const toggle = document.createElement("input");
  toggle.type = "checkbox";
  toggle.checked = selectedCourseIds.has(String(c.id));
  toggle.disabled = disabled;

  const toggleSelection = (on) => {
    if (disabled) return;
    if (on) selectedCourseIds.add(String(c.id)); else selectedCourseIds.delete(String(c.id));
    card.dataset.selected = on ? "true" : "false";
    selectedCount.textContent = `${selectedCourseIds.size} selected`;
  };

  toggle.addEventListener("click", (e) => { e.stopPropagation(); toggleSelection(toggle.checked); });
  card.addEventListener("click", () => {
    if (disabled) return;
    const next = !selectedCourseIds.has(String(c.id));
    toggle.checked = next;
    toggleSelection(next);
  });

  card.appendChild(left);
  card.appendChild(toggle);
  return card;
}

// Collapsible full-width group. Cards rendered in 3-column grid.
function groupSection(g) {
  const sec = document.createElement("section");
  sec.className = "modal-group w-full rounded border border-gray-200";

  // header
  const header = document.createElement("button");
  header.type = "button";
  header.className = "w-full flex items-center justify-between p-2";
  header.setAttribute("aria-expanded", expandedGroupIds.has(g.group_id) ? "true" : "false");

  const hLeft = document.createElement("div");
  hLeft.className = "font-semibold truncate";
  hLeft.textContent = g.title;

  const rightWrap = document.createElement("div");
  rightWrap.className = "flex items-center gap-3";

  const count = document.createElement("div");
  count.className = "text-sm text-gray-600 whitespace-nowrap";
  count.textContent = `${g.completed_count || 0} / ${g.required_count || 0}`;

  const caret = document.createElement("span");
  caret.className = "text-xs select-none";
  caret.textContent = expandedGroupIds.has(g.group_id) ? "▾" : "▸";

  rightWrap.appendChild(count);
  rightWrap.appendChild(caret);

  header.appendChild(hLeft);
  header.appendChild(rightWrap);

  // body
  const body = document.createElement("div");
  body.className = "px-2 pb-3";
  if (!expandedGroupIds.has(g.group_id)) body.style.display = "none";

  const bar = progressBar(g.completed_count || 0, g.required_count || 0);
  bar.classList.add("mb-2");
  body.appendChild(bar);

  const grid = document.createElement("div");
  grid.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mt-1 w-full";
  (g.courses || []).forEach((c) => grid.appendChild(courseCard(c)));
  body.appendChild(grid);

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

// Render groups stacked vertically
export function renderModalGroups(groups) {
  if (!results) return;
  results.className = "";
  results.classList.add("results-scroll", "flex", "flex-col", "gap-4", "w-full");
  results.style.overflowX = "hidden";

  if (expandedGroupIds.size === 0) {
    (groups || []).forEach(g => expandedGroupIds.add(g.group_id));
  }

  results.innerHTML = "";
  (groups || []).forEach((g) => results.appendChild(groupSection(g)));
}

// Fetch groups and render
export async function loadAndRenderModal(q, currentTermUpper) {
  const url = new URL("/api/requirements", window.location.origin);
  if (q && q.trim()) url.searchParams.set("q", q.trim());
  if (currentTermUpper) url.searchParams.set("current_term", currentTermUpper);
  const r = await fetch(url.toString());
  if (!r.ok) throw new Error("failed to load requirements");
  const data = await r.json();
  renderModalGroups(data.groups || []);
}
