// class_modal/actions.js
import {
  addModal, searchInput, searchBtn, addOpen, addClose, addCancel, addConfirm,
  results, getSemesters, remainingCredits, toNum,
  fetchSemesters, addClass, setSemesters
} from "../semesters/state_nav.js";
import { selectedCourseIds, loadAndRenderModal } from "./search.js";
import { showError } from "../context_menu/toast.js";

function ensureResultsScrollable() {
  // make sure results list always scrolls, regardless of tailwind changes
  if (results) {
    results.classList.add("results-scroll");
    results.style.overflowY = "auto";
    results.style.maxHeight = "min(56vh, 520px)";
    results.style.webkitOverflowScrolling = "touch";
  }
}

// open/close
export function openAddModal() {
  selectedCourseIds.clear();
  const sc = document.getElementById("modal-selected-count");
  if (sc) sc.textContent = "0 selected";
  addModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  ensureResultsScrollable();
  loadAndRenderModal("");
}
export function closeAddModal() {
  addModal.classList.add("hidden");
  document.body.style.overflow = "";
}

// Is this catalog course already planned anywhere?
function isCourseAssigned(catalogCourseId){
  const idStr = String(catalogCourseId);
  for (const s of getSemesters()) {
    if ((s.classes || []).some(c => String(c.catalog_id) === idStr)) return true;
  }
  return false;
}

async function fetchCourseLocalOrServer(id) {
  const el = results.querySelector(`.modal-card[data-id="${id}"]`);
  if (el) {
    const creditsTxt = el.querySelector(".chip-sub")?.textContent || "";
    const m = creditsTxt.match(/(\d+(\.\d+)?)\s*credits/i);
    const credits = m ? Number(m[1]) : 0;
    return { id: Number(id), credits };
  }
  return { id: Number(id), credits: 0 };
}

// Add selected with credit + assignment guards. Then refresh state and re-render.
export async function addSelectedToCurrentSemester(currentIndex) {
  const semesters = getSemesters();
  const sem = semesters[currentIndex];
  if (!sem) { closeAddModal(); return; }

  const ids = Array.from(selectedCourseIds); // catalog ids
  if (!ids.length) { closeAddModal(); return; }

  let remaining = remainingCredits(sem);
  let added = 0;
  let blockedCredits = false;
  let blockedAssigned = false;

  for (const catalogId of ids) {
    if (isCourseAssigned(catalogId)) { blockedAssigned = true; continue; }
    try {
      const course = await fetchCourseLocalOrServer(catalogId);
      const need = toNum(course.credits);
      if (need <= 0) continue;
      if (need > remaining) { blockedCredits = true; continue; }

      await addClass(Number(catalogId), Number(sem.id));
      remaining -= need;
      added++;
    } catch {
      // ignore single failure to allow others to proceed
    }
  }

  // reload state and ask view to render
  try {
    const data = await fetchSemesters();
    setSemesters(data);
    window.dispatchEvent(new Event("planner:render"));
    window.dispatchEvent(new Event("planner:reload"));
  } catch {
    showError("Failed to refresh semesters.");
  }

  closeAddModal();
  if (blockedAssigned) showError("One or more selected courses are already scheduled in another semester.");
  if (blockedCredits)  showError("Credit limit exceeded. Max 18 credits per semester.");
  if (!added && !blockedAssigned && !blockedCredits) showError("No courses were added.");
}

// wire modal buttons and search
export function bindModalControls() {
  addOpen?.addEventListener("click", openAddModal);
  addClose?.addEventListener("click", closeAddModal);
  addCancel?.addEventListener("click", closeAddModal);
  addConfirm?.addEventListener("click", () => {
    const idx = Number(document.body.dataset.currentIndex || 0);
    addSelectedToCurrentSemester(idx);
  });
  searchBtn?.addEventListener("click", async () => loadAndRenderModal(searchInput.value));

  let searchTimer = null;
  searchInput?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => loadAndRenderModal(searchInput.value), 150);
  });
}
