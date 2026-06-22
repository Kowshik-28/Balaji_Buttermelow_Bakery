const itemsContainer = document.querySelector("#cart-items");
const emptyCart = document.querySelector("#empty-cart");
const totalElement = document.querySelector("#cart-total");
const checkoutForm = document.querySelector("#checkout-form");
const formError = document.querySelector("#form-error");
const addressField = document.querySelector("#address-field");

function money(paise) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(paise / 100);
}

function imageUrl(path) {
  if (!path) return "/static/logo.jpg";
  return path.startsWith("uploads/") ? `/${path}` : `/static/${path}`;
}

function renderCart() {
  const cart = TreatsCart.readCart();
  itemsContainer.innerHTML = "";
  emptyCart.hidden = cart.length > 0;
  checkoutForm.hidden = cart.length === 0;
  totalElement.parentElement.hidden = cart.length === 0;

  let total = 0;
  cart.forEach((item) => {
    total += item.price_paise * item.quantity;
    const row = document.createElement("article");
    row.className = "cart-item";
    row.innerHTML = `
      <img src="${imageUrl(item.image_path)}" alt="">
      <div class="cart-item-copy">
        <h2></h2>
        <span>${money(item.price_paise)} each</span>
      </div>
      <div class="quantity-control" aria-label="Quantity">
        <button type="button" data-action="decrease" aria-label="Decrease quantity">−</button>
        <strong>${item.quantity}</strong>
        <button type="button" data-action="increase" aria-label="Increase quantity">+</button>
      </div>
      <strong>${money(item.price_paise * item.quantity)}</strong>
      <button class="remove-button" type="button" data-action="remove" aria-label="Remove item">×</button>
    `;
    row.querySelector("h2").textContent = item.name;
    row.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => updateItem(item.id, button.dataset.action));
    });
    itemsContainer.appendChild(row);
  });
  totalElement.textContent = money(total);
}

function updateItem(id, action) {
  const cart = TreatsCart.readCart();
  const item = cart.find((entry) => entry.id === id);
  if (!item) return;
  if (action === "increase") item.quantity = Math.min(50, item.quantity + 1);
  if (action === "decrease") item.quantity -= 1;
  const nextCart = action === "remove" || item.quantity < 1
    ? cart.filter((entry) => entry.id !== id)
    : cart;
  TreatsCart.writeCart(nextCart);
}

document.querySelectorAll('input[name="fulfillment_type"]').forEach((input) => {
  input.addEventListener("change", () => {
    const delivery = input.value === "delivery" && input.checked;
    addressField.hidden = !delivery;
    addressField.querySelectorAll("input[name^='address_']").forEach((field) => {
      field.required = delivery;
    });
  });
});

// Sync structured address inputs with the hidden address input
function updateHiddenAddress() {
  const flat = checkoutForm.querySelector('[name="address_flat"]').value.trim();
  const street = checkoutForm.querySelector('[name="address_street"]').value.trim();
  const pincode = checkoutForm.querySelector('[name="address_pincode"]').value.trim();
  const city = checkoutForm.querySelector('[name="address_city"]').value.trim();
  
  if (flat || street || city || pincode) {
    checkoutForm.querySelector('[name="address"]').value = `${flat}, ${street}, ${city} - ${pincode}`;
  } else {
    checkoutForm.querySelector('[name="address"]').value = "";
  }
}

checkoutForm.querySelectorAll('input[name^="address_"]').forEach((input) => {
  input.addEventListener("input", updateHiddenAddress);
});

// Live Location Detection using browser Geolocation + OpenStreetMap Nominatim API
const detectLocationBtn = document.querySelector("#detect-location-btn");
if (detectLocationBtn) {
  detectLocationBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    detectLocationBtn.disabled = true;
    detectLocationBtn.textContent = "⏳ Detecting...";

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          // Fetch reverse geocoded address from Nominatim API (Free & Keyless)
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`
          );
          if (!response.ok) throw new Error("Location lookup failed.");
          
          const data = await response.json();
          if (data && data.address) {
            const addr = data.address;
            
            // Extract street / area details
            const streetVal = addr.road || addr.suburb || addr.neighbourhood || addr.village || "";
            const cityVal = addr.city || addr.town || addr.village || addr.county || "";
            const pincodeVal = addr.postcode || "";

            // Populate form fields
            const streetInput = checkoutForm.querySelector('[name="address_street"]');
            const pincodeInput = checkoutForm.querySelector('[name="address_pincode"]');
            const cityInput = checkoutForm.querySelector('[name="address_city"]');
            
            if (streetVal) streetInput.value = streetVal;
            if (pincodeVal) pincodeInput.value = pincodeVal;
            if (cityVal) cityInput.value = cityVal;

            updateHiddenAddress();

            // Set focus to the Flat No field so the user can easily type their house/flat number
            checkoutForm.querySelector('[name="address_flat"]').focus();
          }
        } catch (error) {
          alert("Could not fetch address details for your location. Please enter it manually.");
        } finally {
          detectLocationBtn.disabled = false;
          detectLocationBtn.textContent = "📍 Detect location";
        }
      },
      (error) => {
        alert("Location access denied or unavailable. Please enter your address manually.");
        detectLocationBtn.disabled = false;
        detectLocationBtn.textContent = "📍 Detect location";
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

checkoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.textContent = "";
  const button = checkoutForm.querySelector('button[type="submit"]');
  const data = new FormData(checkoutForm);
  const cart = TreatsCart.readCart();
  if (!cart.length) return renderCart();

  button.disabled = true;
  button.textContent = "Saving order…";
  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer: {
          name: data.get("name"),
          phone: data.get("phone"),
          email: data.get("email"),
          address: data.get("address"),
        },
        fulfillment_type: data.get("fulfillment_type"),
        requested_time: data.get("requested_time"),
        notes: data.get("notes"),
        items: cart.map(({ id, quantity }) => ({ id, quantity })),
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Could not place the order.");
    TreatsCart.writeCart([]);
    window.location.assign(`/order/success/${result.order_number}`);
  } catch (error) {
    formError.textContent = error.message;
    button.disabled = false;
    button.textContent = "Place order";
    checkoutForm.classList.add("shake");
    setTimeout(() => checkoutForm.classList.remove("shake"), 500);
  }
});

window.addEventListener("cart:updated", renderCart);
renderCart();
