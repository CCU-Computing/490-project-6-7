// static/js/semesters/view.js  (entry)
import {
  maxCreditsPerSem,
  track, dots, viewport,
  fetchSemesters, deleteClass,
  getSemesters, setSemesters, getCurrent, setCurrent,
  semCredits, escapeHTML,
  scrollToIndex, updateDotsAndHighlight, updateCenteredSemester
} from "./state_nav.js";
import { buildMenu } from "../context_menu/menu.js";
import { showError } from "../context_menu/toast.js";
import { bindModalControls } from "../class_modal/actions.js";

let currentOpenMenu = null;
let cardLisRef = [];
let cardDivsRef = [];
let navBound = false;

/* ---------------- Render ---------------- */
export function render() {
  track.innerHTML = "";
  dots.innerHTML = "";
  cardLisRef = [];
  cardDivsRef = [];

  const leftPad = document.createElement("li");
  leftPad.className = "edge-pad";
  track.appendChild(leftPad);

  document.body.dataset.currentIndex = String(getCurrent());

  getSemesters().forEach((sem, i) => {
    const li = document.createElement("li");
    li.className = "snap-center shrink-0 card-li";
    li.addEventListener("click", (e) => {
      // ignore clicks that originated from a context-menu button
      if (e.target.closest?.("[data-action='menu']")) return;
      setCurrent(i);
      document.body.dataset.currentIndex = String(i);
      snapToCurrent();
    });

    const card = document.createElement("div");
    card.className = "card semester-body semester-card-minh";
    card.tabIndex = 0;
    card.style.position = "relative";

    const head = document.createElement("div");
    head.className = "flex items-center justify-between p-4";
    const credits = semCredits(sem);
    head.innerHTML = `
      <div>
        <div class="text-xs uppercase tracking-widest text-gray-500">Semester</div>
        <h2 class="text-lg font-semibold tracking-tight">${escapeHTML(sem.name)}</h2>
      </div>
      <div class="text-sm font-semibold ${credits > maxCreditsPerSem ? 'text-red-600' : 'text-gray-700'}">
        ${credits}/${maxCreditsPerSem} credits
      </div>
    `;

    const body = document.createElement("div");
    body.className = "px-4 pb-4";
    const list = document.createElement("ul");
    list.className = "semester-list";
    (sem.classes || []).forEach((cls) => list.appendChild(classRow(cls)));

    body.appendChild(list);
    card.appendChild(head);
    card.appendChild(body);
    li.appendChild(card);
    track.appendChild(li);

    cardLisRef[i] = li;
    cardDivsRef[i] = card;
  });

  const rightPad = document.createElement("li");
  rightPad.className = "edge-pad";
  track.appendChild(rightPad);

  getSemesters().forEach((_, i) => {
    const b = document.createElement("button");
    b.className = `h-2 w-2 rounded-full transition-all ${i === getCurrent() ? "w-6 bg-gray-900" : "bg-gray-300 hover:bg-gray-400"}`;
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      setCurrent(i);
      document.body.dataset.currentIndex = String(i);
      snapToCurrent();
    });
    dots.appendChild(b);
  });

  snapToCurrent();

  window.addEventListener("resize", () => {
    updateCenteredSemester(cardLisRef, cardDivsRef);
    document.body.dataset.currentIndex = String(getCurrent());
    snapToCurrent();
  });

  if (!navBound) {
    bindNavOnce();
    navBound = true;
  }
}

/* ---------------- Class row ---------------- */
function classRow(cls) {
  const li = document.createElement("li");

  const wrap = document.createElement("div");
  // grid keeps credit badges aligned in the same column
  wrap.className = "class-chip grid grid-cols-[1fr_auto_auto] items-center gap-3";
  wrap.style.position = "relative";

  const left = document.createElement("div");
  left.className = "flex items-center gap-3 overflow-hidden";
  left.innerHTML = `
    <div class="chip-text">
      <div class="chip-title">${escapeHTML(cls.title || "")}</div>
      <div class="chip-sub">${escapeHTML(cls.code || "")}${cls.section ? " · " + escapeHTML(cls.section) : ""}</div>
    </div>
  `;

  const credits = Number.isFinite(+cls.credits) ? +cls.credits : 0;
  const creditEl = document.createElement("span");
  creditEl.className = "chip-credits w-12 text-right text-xs font-semibold text-gray-600 justify-self-end";
  creditEl.textContent = `${credits} cr`;

  const menuBtn = document.createElement("button");
  menuBtn.type = "button";
  menuBtn.dataset.action = "menu";
  menuBtn.setAttribute("aria-haspopup", "menu");
  menuBtn.setAttribute("aria-expanded", "false");
  menuBtn.setAttribute("aria-label", "Actions");
  menuBtn.style.cssText = "display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border:none;background:transparent;border-radius:8px;cursor:pointer;";
  menuBtn.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" class="opacity-70 pointer-events-none">
      <circle cx="5" cy="12" r="2"></circle>
      <circle cx="12" cy="12" r="2"></circle>
      <circle cx="19" cy="12" r="2"></circle>
    </svg>
  `;

  attachClassMenu(menuBtn, cls);

  wrap.appendChild(left);
  wrap.appendChild(creditEl);
  wrap.appendChild(menuBtn);
  li.appendChild(wrap);
  return li;
}

/* ---------------- Context menu ---------------- */
function attachClassMenu(btn, cls) {
  if (!btn) return;

  // Prevent parent click navigation when interacting with the menu button.
  ["pointerdown", "mousedown", "click"].forEach((ev) =>
    btn.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, true)
  );

  const modalOpen = () => {
    const m = document.getElementById("add-modal");
    return m && !m.classList.contains("hidden");
  };

  const closeMenu = () => {
    if (!currentOpenMenu) return;
    const ref = currentOpenMenu;
    currentOpenMenu = null;
    ref.style.opacity = "0";
    ref.style.transform = "scale(0.98)";
    setTimeout(() => (ref._destroy ? ref._destroy() : ref.remove()), 120);
    document.removeEventListener("pointerdown", onDocDown, true);
  };

  const onDocDown = (e) => {
    if (!currentOpenMenu) return;
    if (!currentOpenMenu.contains(e.target) && e.target !== btn) {
      closeMenu();
    }
  };

  // Open on pointerup so our outside handler (pointerdown) doesn't immediately close it.
  btn.addEventListener("pointerup", async (e) => {
    if (modalOpen()) return;
    e.preventDefault();
    e.stopPropagation();

    if (currentOpenMenu) { closeMenu(); return; }

    const items = [
      { label: "Details", colorClass: "text-blue-600",  icon: "info", onClick: null },
      { label: "Move…",   colorClass: "text-amber-600", icon: "move", onClick: null },
      { label: "Delete",  colorClass: "text-red-600",   icon: "trash", onClick: async () => {
          try {
            await deleteClass(cls.id); // StudentCourse id
            const data = await fetchSemesters();
            setSemesters(data);
            window.dispatchEvent(new Event("planner:render"));
          } catch {
            showError("Delete failed.");
          } finally {
            closeMenu();
          }
        } },
    ];

    currentOpenMenu = buildMenu(items, btn);
    // Attach outside-close BEFORE any subsequent clicks happen.
    document.addEventListener("pointerdown", onDocDown, true);
  });
}

/* ---------------- Navigation ---------------- */
function snapToCurrent() {
  scrollToIndex(getCurrent(), true, cardLisRef);
  updateDotsAndHighlight(cardDivsRef);
}
function bindNavOnce() {
  // One card per wheel gesture (skip when modal open)
  let wheelLock = false;
  viewport.addEventListener("wheel", (e) => {
    const m = document.getElementById("add-modal");
    const isModalOpen = m && !m.classList.contains("hidden");
    if (isModalOpen) return;

    if (Math.abs(e.deltaY) >= Math.abs(e.deltaX)) {
      e.preventDefault();
      if (wheelLock) return;
      wheelLock = true;
      const dir = e.deltaY > 0 ? 1 : -1;
      const next = Math.max(0, Math.min(getSemesters().length - 1, getCurrent() + dir));
      if (next !== getCurrent()) {
        setCurrent(next);
        document.body.dataset.currentIndex = String(next);
        snapToCurrent();
      }
      setTimeout(() => { wheelLock = false; }, 220);
    }
  }, { passive: false });

  // Touch swipe, one card per gesture (skip when modal open)
  let startX = 0, isTouching = false;
  viewport.addEventListener("touchstart", (e) => {
    const m = document.getElementById("add-modal");
    const isModalOpen = m && !m.classList.contains("hidden");
    if (isModalOpen) return;
    if (e.touches.length === 1) {
      isTouching = true;
      startX = e.touches[0].clientX;
    }
  }, { passive: true });

  viewport.addEventListener("touchend", (e) => {
    const m = document.getElementById("add-modal");
    const isModalOpen = m && !m.classList.contains("hidden");
    if (!isTouching || isModalOpen) return;
    isTouching = false;
    const endX = (e.changedTouches && e.changedTouches[0]?.clientX) || startX;
    const dx = endX - startX;
    const threshold = 30;
    if (Math.abs(dx) >= threshold) {
      const dir = dx < 0 ? 1 : -1;
      const next = Math.max(0, Math.min(getSemesters().length - 1, getCurrent() + dir));
      if (next !== getCurrent()) {
        setCurrent(next);
        document.body.dataset.currentIndex = String(next);
        snapToCurrent();
      }
    }
  }, { passive: true });

  viewport.addEventListener("scroll", () => updateCenteredSemester(cardLisRef, cardDivsRef));

  // Keyboard arrows (when modal closed)
  document.addEventListener("keydown", (e) => {
    const m = document.getElementById("add-modal");
    const isModalOpen = m && !m.classList.contains("hidden");
    if (isModalOpen) return;
    if (e.key === "ArrowLeft") {
      const next = Math.max(0, getCurrent() - 1);
      setCurrent(next);
      document.body.dataset.currentIndex = String(next);
      snapToCurrent();
    }
    if (e.key === "ArrowRight") {
      const next = Math.min(getSemesters().length - 1, getCurrent() + 1);
      setCurrent(next);
      document.body.dataset.currentIndex = String(next);
      snapToCurrent();
    }
  });
}

/* ---------------- Boot ---------------- */
(async function init() {
  bindModalControls();

  window.addEventListener("planner:render", () => render());
  window.addEventListener("planner:reload", async () => {
    const data = await fetchSemesters();
    setSemesters(data);
    render();
  });

  try {
    const data = await fetchSemesters();
    setSemesters(data);
    render();
  } catch (e) {
    console.error("Failed to load semesters", e);
    showError("Failed to load semesters.");
  }
})();
