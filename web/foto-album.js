(() => {
  "use strict";

  const tabs = [...document.querySelectorAll(".year-tab")];
  const panels = [...document.querySelectorAll(".year-panel")];
  const cards = [...document.querySelectorAll(".photo-card")];
  const viewer = document.querySelector(".viewer");
  if (!viewer) return;

  const image = viewer.querySelector(".viewer-image");
  const caption = viewer.querySelector(".viewer-caption");
  const previous = viewer.querySelector(".viewer-previous");
  const next = viewer.querySelector(".viewer-next");
  let activeIndex = 0;
  let returnFocus = null;

  function showYear(year, focusTab = false) {
    tabs.forEach((tab) => {
      const selected = tab.dataset.year === year;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focusTab) tab.focus();
    });
    panels.forEach((panel) => { panel.hidden = panel.dataset.year !== year; });
  }

  function displayPhoto(index) {
    activeIndex = (index + cards.length) % cards.length;
    const link = cards[activeIndex];
    const thumbnail = link.querySelector("img");
    image.src = link.href;
    image.alt = thumbnail.alt;
    caption.textContent = thumbnail.alt;
    previous.disabled = cards.length < 2;
    next.disabled = cards.length < 2;
  }

  cards.forEach((card, index) => {
    card.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (!cards.length) return;
      returnFocus = card;
      displayPhoto(index);
      viewer.showModal();
      viewer.querySelector(".viewer-close").focus();
    });
  });

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => showYear(tab.dataset.year));
    tab.addEventListener("keydown", (event) => {
      let destination = null;
      if (event.key === "ArrowRight") destination = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft") destination = (index - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") destination = 0;
      if (event.key === "End") destination = tabs.length - 1;
      if (destination !== null) {
        event.preventDefault();
        showYear(tabs[destination].dataset.year, true);
      }
    });
  });

  previous.addEventListener("click", () => displayPhoto(activeIndex - 1));
  next.addEventListener("click", () => displayPhoto(activeIndex + 1));
  viewer.querySelector(".viewer-close").addEventListener("click", () => viewer.close());
  viewer.querySelector(".viewer-home").addEventListener("click", () => viewer.close());
  viewer.addEventListener("click", (event) => {
    if (event.target === viewer) viewer.close();
  });
  viewer.addEventListener("close", () => {
    image.removeAttribute("src");
    if (returnFocus?.isConnected) returnFocus.focus();
  });
  document.addEventListener("keydown", (event) => {
    if (!viewer.open || !cards.length) return;
    if (event.key === "ArrowLeft") displayPhoto(activeIndex - 1);
    if (event.key === "ArrowRight") displayPhoto(activeIndex + 1);
  });
})();