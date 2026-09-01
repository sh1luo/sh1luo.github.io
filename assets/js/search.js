(() => {
  const containers = [...document.querySelectorAll('[data-site-search]')];
  if (!containers.length) return;

  let indexPromise;

  const normalize = (value) => String(value || '').toLocaleLowerCase('zh-Hans');

  const loadIndex = (url) => {
    if (!indexPromise) {
      indexPromise = fetch(url, { credentials: 'same-origin' }).then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      }).then((data) => (Array.isArray(data) ? data : []));
    }
    return indexPromise;
  };

  const instances = containers.map((container) => {
    const input = container.querySelector('input[type="search"]');
    const panel = container.querySelector('.header-search-panel');
    const status = container.querySelector('.header-search-status');
    const results = container.querySelector('.header-search-results');
    const indexUrl = container.dataset.searchIndex || '/index.json';
    let articles;
    let requestVersion = 0;

    if (!input || !panel || !status || !results) return null;

    const setOpen = (open) => {
      panel.hidden = !open;
      input.setAttribute('aria-expanded', String(open));
    };

    const renderMatches = (keyword) => {
      const matches = articles.filter((article) => {
        const text = [article.title, article.description, ...(article.tags || [])]
          .map(normalize)
          .join(' ');
        return text.includes(keyword);
      }).slice(0, 8);

      status.textContent = matches.length
        ? `找到 ${matches.length} 篇匹配文章。`
        : '没有找到匹配的文章。';

      matches.forEach((article) => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        const title = document.createElement('h3');
        const meta = document.createElement('p');
        const summary = document.createElement('p');

        link.href = article.url;
        title.textContent = article.title;
        meta.className = 'search-result-meta';
        meta.textContent = [article.date, ...(article.tags || [])].filter(Boolean).join(' · ');
        summary.textContent = article.description;

        link.append(title, meta, summary);
        item.append(link);
        results.append(item);
      });
    };

    const search = () => {
      const keyword = normalize(input.value).trim();
      const currentVersion = ++requestVersion;
      results.replaceChildren();
      setOpen(true);

      if (keyword.length < 2) {
        status.textContent = '输入至少两个字符。';
        return;
      }

      status.textContent = '正在搜索…';
      loadIndex(indexUrl)
        .then((data) => {
          if (currentVersion !== requestVersion) return;
          articles = data;
          renderMatches(keyword);
        })
        .catch(() => {
          if (currentVersion !== requestVersion) return;
          status.textContent = '搜索索引加载失败，请刷新页面后重试。';
        });
    };

    input.addEventListener('focus', search);
    input.addEventListener('input', search);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
        input.blur();
      }
      if (event.key === 'ArrowDown') {
        const firstResult = results.querySelector('a');
        if (firstResult) {
          event.preventDefault();
          firstResult.focus();
        }
      }
    });

    return { container, close: () => setOpen(false) };
  }).filter(Boolean);

  document.addEventListener('click', (event) => {
    instances.forEach((instance) => {
      if (!instance.container.contains(event.target)) instance.close();
    });
  });
})();
