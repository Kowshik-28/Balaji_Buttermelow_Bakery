const CART_KEY = "treats-by-mimi-cart-v1";

function readCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch {
    return [];
  }
}

function writeCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartCount();
  window.dispatchEvent(new CustomEvent("cart:updated"));
}

function addToCart(item) {
  const cart = readCart();
  const existing = cart.find((entry) => entry.id === item.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ ...item, quantity: 1 });
  }
  writeCart(cart);
  showToast(`${item.name} added to your cart`);
}

function updateCartCount() {
  const count = readCart().reduce((total, item) => total + item.quantity, 0);
  document.querySelectorAll("[data-cart-count]").forEach((element) => {
    element.textContent = count;
    element.classList.remove("pulse");
    void element.offsetWidth; // Trigger reflow to restart animation
    element.classList.add("pulse");
    setTimeout(() => element.classList.remove("pulse"), 300);
  });
}

function showToast(message) {
  const toast = document.querySelector(".toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => toast.classList.remove("visible"), 2400);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".add-to-cart");
  if (!button) return;
  addToCart(JSON.parse(button.dataset.item));
});

const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");
if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const open = siteNav.classList.toggle("open");
    navToggle.setAttribute("aria-expanded", String(open));
  });
}

updateCartCount();

window.TreatsCart = { readCart, writeCart, showToast, CART_KEY };
