// static/js/context_menu/menu.js

/**
 * Build a floating context menu rendered in a portal (document.body)
 * so it never gets clipped. Positioned near the anchor element.
 *
 * items: [{ label, colorClass?, icon?, onClick?(anchorEl, menu) }]
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

  // Tabler-like minimal SVGs (valid paths)
  const icons = {
    info: `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h2v4"/></svg>`,
    // move icon removed by request
    trash:`<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/><path d="M9 7V4h6v3"/></svg>`
  };

  const mkItem = (label, colorClass, iconKey, onClick) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className =
      "w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg " +
      "hover:bg-gray-50 focus:outline-none";
    btn.innerHTML = `
      <span class="inline-flex h-5 w-5 items-center justify-center ${colorClass || "text-gray-600"}">
        ${icons[iconKey] || ""}
      </span>
      <span class="text-gray-800">${label}</span>
    `;
    if (typeof onClick === "function") {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        try { onClick(anchorEl, menu); } finally { destroy(); }
      });
    } else {
      btn.addEventListener("click", () => destroy());
    }
    return btn;
  };

  // If caller passes no items, provide a sane default: Details + Delete.
  if (!items || items.length === 0) {
    items = [
      { label: "Details", icon: "info", colorClass: "text-blue-600", onClick: (el) => {
          const ev = new CustomEvent("ctx:details", { detail: { anchor: el } });
          window.dispatchEvent(ev);
        } },
      { label: "Delete", icon: "trash", colorClass: "text-red-600", onClick: (el) => {
          const ev = new CustomEvent("ctx:delete", { detail: { anchor: el } });
          window.dispatchEvent(ev);
        } },
    ];
  }

  items.forEach(({ label, colorClass, icon, onClick }) => {
    if (icon === "move") return; // removed tool
    menu.appendChild(mkItem(label, colorClass, icon, onClick));
  });

  // Portal attach
  document.body.appendChild(menu);

  // Position near anchor (bottom-right), with viewport bounds guard
  const place = () => {
    let x = window.scrollX + window.innerWidth - 12;
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

  // Close on outside click and on Escape
  const onDocClick = (e) => {
    if (!menu.contains(e.target)) destroy();
  };
  const onKey = (e) => {
    if (e.key === "Escape") destroy();
  };
  setTimeout(() => {
    document.addEventListener("mousedown", onDocClick, { passive: true });
    document.addEventListener("keydown", onKey);
  }, 0);

  // Cleanup helper
  function destroy() {
    window.removeEventListener("resize", onWin);
    window.removeEventListener("scroll", onWin);
    document.removeEventListener("mousedown", onDocClick);
    document.removeEventListener("keydown", onKey);
    menu.remove();
  }
  menu._destroy = destroy;

  return menu;
}
