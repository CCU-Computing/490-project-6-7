// class_modal/search.js
import { searchCourses, results, selectedCount } from "../semesters/state_nav.js";

export const selectedCourseIds = new Set();

export function renderModalResults(items) {
  results.innerHTML = "";
  items.forEach((c) => {
    const card = document.createElement("div");
    card.className = "modal-card";
    card.dataset.id = String(c.id);
    card.dataset.selected = selectedCourseIds.has(String(c.id)) ? "true" : "false";

    const left = document.createElement("div");
    left.className = "overflow-hidden";
    left.innerHTML = `<div class="text-sm font-semibold chip-title">${c.code} · ${c.title}</div><div class="text-xs text-gray-500 chip-sub">${c.credits || 0} credits</div>`;

    const toggle = document.createElement("input");
    toggle.type = "checkbox";
    toggle.checked = selectedCourseIds.has(String(c.id));
    toggle.addEventListener("click", (e) => { e.stopPropagation(); toggleSelection(c.id, toggle.checked, card); });

    card.addEventListener("click", () => {
      const next = !selectedCourseIds.has(String(c.id));
      toggle.checked = next;
      toggleSelection(c.id, next, card);
    });

    card.appendChild(left);
    card.appendChild(toggle);
    results.appendChild(card);
  });
}

export function toggleSelection(id, on, cardEl) {
  if (on) selectedCourseIds.add(String(id)); else selectedCourseIds.delete(String(id));
  if (cardEl) cardEl.dataset.selected = on ? "true" : "false";
  selectedCount.textContent = `${selectedCourseIds.size} selected`;
}

export async function loadAndRenderModal(q) {
  const items = await searchCourses(q);
  renderModalResults(items);
}
