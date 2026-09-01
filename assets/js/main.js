(() => {
  const menuButton = document.getElementById('menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  const tocButton = document.getElementById('toc-btn');
  const toc = document.getElementById('toc');
  const imageButton = document.getElementById('img-btn');
  const featuredImage = document.getElementById('featured-image');

  const setMenuOpen = (open) => {
    if (!menuButton || !mobileMenu) return;
    menuButton.setAttribute('aria-expanded', String(open));
    mobileMenu.hidden = !open;
    mobileMenu.classList.toggle('is-open', open);
  };

  menuButton?.addEventListener('click', () => {
    setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
  });

  document.addEventListener('click', (event) => {
    if (!menuButton || !mobileMenu || mobileMenu.hidden) return;
    if (!mobileMenu.contains(event.target) && !menuButton.contains(event.target)) setMenuOpen(false);
  });

  const setFeaturedImageOpen = (open) => {
    if (!imageButton || !featuredImage) return;
    imageButton.setAttribute('aria-expanded', String(open));
    featuredImage.classList.toggle('show-bg-img', open);
  };

  imageButton?.addEventListener('click', () => {
    setFeaturedImageOpen(imageButton.getAttribute('aria-expanded') !== 'true');
  });
  featuredImage?.addEventListener('click', () => setFeaturedImageOpen(false));
  featuredImage?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setFeaturedImageOpen(false);
    }
  });

  tocButton?.addEventListener('click', () => {
    if (!toc) return;
    const open = !toc.classList.contains('show-toc');
    toc.classList.toggle('show-toc', open);
    tocButton.setAttribute('aria-expanded', String(open));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    setMenuOpen(false);
    setFeaturedImageOpen(false);
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 760) setMenuOpen(false);
  });
})();
