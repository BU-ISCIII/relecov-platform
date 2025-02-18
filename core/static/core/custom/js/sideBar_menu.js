document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.querySelector(".sidebar");
  const contentWrapper = document.querySelector("#content-wrapper");
  const openBtn = document.getElementById("open-btn");
  const closeBtn = document.getElementById("close-btn");

  if (!sidebar || !contentWrapper) return; // Evita errores si no existen

  closeBtn?.addEventListener("click", function () {
      sidebar.classList.add("collapsed");
      openBtn.style.display = "flex"; // Mostrar el botón de apertura
  });

  openBtn?.addEventListener("click", function () {
      sidebar.classList.remove("collapsed");
      openBtn.style.display = "none"; // Ocultar el botón de apertura
  });
});