// Single entry that wires all modules. No imports in HTML besides this file.

// Semesters UI (entry renders and bootstraps everything)
import "./semesters/view.js";

// Optional: re-export for DevTools access if needed
export * as SemState from "./semesters/state_nav.js";
export * as View from "./semesters/view.js";
export * as ModalSearch from "./class_modal/search.js";
export * as ModalActions from "./class_modal/actions.js";
export * as CtxMenu from "./context_menu/menu.js";
export * as Toast from "./context_menu/toast.js";
