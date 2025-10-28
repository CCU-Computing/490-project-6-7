// static/js/context_menu/menu.js

/**
 * Build a floating context menu rendered in a portal (document.body)
 * so it never gets clipped. Positioned near the anchor element.
 *
 * items: [{ label, colorClass?, icon?, onClick? }]
 * anchorEl: HTMLElement used for positioning.
 */
export function buildMenu(items = [], anchorEl = null) {
  const menu = document.createElement("div");
  menu.className =
    "ctx-menu fixed min-w-[180px] rounded-xl bg-white border border-black/5 " +
    "shadow-[0_1px_2px_rgba(0,0,0,0.04),0_12px_28px_rgba(0,0,0,0.12)] " +
    "py-1 z-[99999] origin-top-right transition transform";
  menu.style.opacity = "0";
  menu.style.transform = "scale(0.98)";
  menu.style.pointerEvents = "auto";

  const mkItem = (label, colorClass, iconSvg, onClick) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className =
      "w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg " +
      "hover:bg-gray-50 focus:outline-none";
    btn.innerHTML = `
      <span class="inline-flex h-5 w-5 items-center justify-center ${colorClass || "text-gray-600"}">
        ${iconSvg || ""}
      </span>
      <span class="text-gray-800">${label}</span>
    `;
    if (typeof onClick === "function") {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        onClick();
      });
    }
    return btn;
  };

  // Tabler-like minimal SVGs (valid paths)
  const icons = {
    info: `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h2v4"/></svg>`,
    move: `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 12h18"/><path d="m12 3-3 3m3-3 3 3m-3 18-3-3m3 3 3-3M3 12l3-3M3 12l3 3m15-3-3-3m3 3-3 3"/></svg>`,
    trash:`<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/><path d="M9 7V4h6v3"/></svg>`
  };

  items.forEach(({ label, colorClass, icon, onClick }) => {
    menu.appendChild(mkItem(label, colorClass, icons[icon] || "", onClick));
  });

  // Portal attach
  document.body.appendChild(menu);

  // Position near anchor (bottom-right), with viewport bounds guard
  const place = () => {
    let x = window.scrollX + window.innerWidth - 12; // default right padding
    let y = window.scrollY + 12;
    if (anchorEl) {
      const r = anchorEl.getBoundingClientRect();
      x = r.right + window.scrollX;
      y = r.bottom + window.scrollY;
    }
    const mw = menu.offsetWidth || 180;
    const mh = menu.offsetHeight || 120;
    const maxX = window.scrollX + window.innerWidth - 12 - mw;
    const maxY = window.scrollY + window.innerHeight - 12 - mh;
    menu.style.left = Math.max(window.scrollX + 12, Math.min(x - mw + 8, maxX)) + "px";
    menu.style.top  = Math.max(window.scrollY + 12, Math.min(y + 8, maxY)) + "px";
  };

  // Animate in after first paint
  requestAnimationFrame(() => {
    place();
    menu.style.opacity = "1";
    menu.style.transform = "scale(1)";
    menu.style.transition = "opacity 120ms ease, transform 120ms ease";
  });

  // Reposition on resize/scroll
  const onWin = () => place();
  window.addEventListener("resize", onWin, { passive: true });
  window.addEventListener("scroll", onWin, { passive: true });

  // Cleanup helper
  menu._destroy = () => {
    window.removeEventListener("resize", onWin);
    window.removeEventListener("scroll", onWin);
    menu.remove();
  };

  return menu;
}
