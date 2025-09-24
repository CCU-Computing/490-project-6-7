// context_menu/toast.js
export function showError(msg){
  let host = document.getElementById("toast-host");
  if (!host) {
    host = document.createElement("div");
    host.id = "toast-host";
    host.style.cssText = "position:fixed;inset:auto 0 24px 0;display:flex;justify-content:center;z-index:50;pointer-events:none;";
    document.body.appendChild(host);
  }
  const toast = document.createElement("div");
  toast.textContent = msg;
  toast.style.cssText = `
    pointer-events:auto; background:#fee2e2; color:#991b1b;
    border:1px solid rgba(0,0,0,0.05);
    box-shadow:0 1px 1px rgba(0,0,0,0.04), 0 6px 14px rgba(0,0,0,0.08);
    padding:0.75rem 1rem; border-radius:0.75rem;
    transform: translateY(16px) scale(0.98); opacity:0;
    transition: transform 180ms ease, opacity 180ms ease;
  `;
  host.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = "1"; toast.style.transform = "translateY(0) scale(1)"; });
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(16px) scale(0.98)";
    setTimeout(() => toast.remove(), 200);
  }, 2600);
}
