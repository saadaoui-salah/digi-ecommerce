/* The coupon form of the admin.
 *
 * The staff fill in either a percentage or a discounted price and the other
 * one is filled in for them, from the price of the product they picked.
 */
(function () {
  const percentage = document.querySelector("#id_percentage");
  const price = document.querySelector("#id_discount_price");
  const product = document.querySelector("#id_product");

  if (!percentage || !price || !product) return;

  // The price of the product is fetched once and kept until another product
  // is picked.
  let reference = { id: null, value: null };

  function round(value) {
    return Math.round(value * 100) / 100;
  }

  function priceOfProduct() {
    const id = product.value;
    if (!id) return Promise.resolve(null);
    if (reference.id === id) return Promise.resolve(reference.value);

    return fetch(`/api/products/${id}/`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        const value = data ? Number(data.price_from) : null;
        reference = { id, value };
        return value;
      })
      .catch(() => null);
  }

  percentage.addEventListener("input", () => {
    const value = Number(percentage.value);
    if (!value) return;

    priceOfProduct().then((base) => {
      if (!base) return;
      price.value = round(base * (1 - value / 100)).toFixed(2);
    });
  });

  price.addEventListener("input", () => {
    const value = Number(price.value);
    if (!value) return;

    priceOfProduct().then((base) => {
      if (!base) return;
      percentage.value = round((1 - value / base) * 100).toFixed(2);
    });
  });
})();
