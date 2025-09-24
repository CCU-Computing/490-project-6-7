// semesters/state_nav.js
export const maxPerSemester = 8;      // backend guard
export const maxCreditsPerSem = 18;   // client guard

// DOM refs
export const track = document.getElementById("track");
export const dots = document.getElementById("dots");
export const viewport = document.getElementById("viewport");
export const addOpen = document.getElementById("open-add-modal");
export const addModal = document.getElementById("add-modal");
export const addClose = document.getElementById("close-add-modal");
export const addCancel = document.getElementById("modal-cancel");
export const addConfirm = document.getElementById("modal-add");
export const searchInput = document.getElementById("modal-search-input");
export const searchBtn = document.getElementById("modal-search-btn");
export const results = document.getElementById("modal-results");
export const selectedCount = document.getElementById("modal-selected-count");

// State
let semesters = [];
let current = 0;

export const getSemesters = () => semesters;
export const setSemesters = (arr) => { semesters = Array.isArray(arr) ? arr : []; };
export const getCurrent = () => current;
export const setCurrent = (i) => { current = i; };

// API
export async function fetchSemesters() {
  const r = await fetch("/api/semesters");
  if (!r.ok) throw new Error("failed");
  return r.json();
}
export async function searchCourses(q) {
  const r = await fetch(`/api/courses?unassigned=1&q=${encodeURIComponent(q || "")}`);
  if (!r.ok) throw new Error("search failed");
  return r.json();
}

// Add a catalog course to a semester (creates StudentCourse)
export async function addClass(course_id, semester_id, section = null) {
  const r = await fetch(`/api/classes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ course_id, semester_id, section })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// Move an existing StudentCourse to another semester
export async function moveClass(studentCourseId, semester_id) {
  const r = await fetch(`/api/classes/${studentCourseId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ semester_id })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteClass(studentCourseId) {
  const r = await fetch(`/api/classes/${studentCourseId}`, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
}

// Helpers
export function toNum(x){ const n = Number(x); return Number.isFinite(n) ? n : 0; }
export function semCredits(sem){ return (sem.classes || []).reduce((s,c)=>s+toNum(c.credits),0); }
export function remainingCredits(sem){ return Math.max(0, maxCreditsPerSem - semCredits(sem)); }
export function escapeHTML(s){ return String(s).replace(/[&<>"']/g, m => ({ "&":"&amp;","<":"&lt;","&gt;":">","\"":"&quot;","'":"&#039;" }[m])); }

// Navigation helpers
export function scrollToIndex(i, smooth = true, cardLis = []) {
  const next = Math.max(0, Math.min(getSemesters().length - 1, i));
  setCurrent(next);
  const li = cardLis[next];
  if (li) li.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "nearest", inline: "center" });
}
export function updateDotsAndHighlight(cardDivs = []) {
  const curr = getCurrent();
  Array.from(dots.children).forEach((d, idx) => {
    d.className = `h-2 w-2 rounded-full transition-all ${idx === curr ? "w-6 bg-gray-900" : "bg-gray-300 hover:bg-gray-400"}`;
  });
  cardDivs.forEach((el, idx) => el.classList.toggle("card-selected", idx === curr));
}
export function updateCenteredSemester(cardLis = [], cardDivs = []) {
  if (!cardLis.length) return;
  const vpRect = viewport.getBoundingClientRect();
  const vpCenter = viewport.scrollLeft + vpRect.width / 2;
  let min = Infinity, best = getCurrent();
  cardLis.forEach((li, idx) => {
    const rect = li.getBoundingClientRect();
    const center = viewport.scrollLeft + (rect.left - vpRect.left) + rect.width / 2;
    const d = Math.abs(center - vpCenter);
    if (d < min) { min = d; best = idx; }
  });
  if (best !== getCurrent()) setCurrent(best);
  updateDotsAndHighlight(cardDivs);
}
//... (1 line left)