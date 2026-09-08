(() => {
  const containers = [...document.querySelectorAll('[data-site-search]')];
  if (!containers.length) return;

  const normalize = (value) => String(value || '').normalize('NFKC').toLocaleLowerCase('zh-Hans');
  const batchSize = 8;
  let indexPromise;

  const loadIndex = (url) => {
    if (!indexPromise) {
      indexPromise = fetch(url, { credentials: 'same-origin' })
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then((data) => {
          if (!Array.isArray(data)) throw new Error('Invalid search index');
          return data.map((article) => ({
            ...article,
            fields: [article.title, (article.tags || []).join(' '), article.description, article.content]
              .map(normalize),
          }));
        })
        .catch((error) => {
          indexPromise = undefined;
          throw error;
        });
    }
    return indexPromise;
  };

  containers.forEach((container) => {
    const input = container.querySelector('input[type="search"]');
    const panel = container.querySelector('.header-search-panel');
    const status = container.querySelector('.header-search-status');
    const results = container.querySelector('.header-search-results');
    const more = container.querySelector('.search-more');
    const indexUrl = container.dataset.searchIndex || '/index.json';
    let requestVersion = 0;
    let matches = [];
    let shown = 0;
    let terms = [];

    if (!input || !panel || !status || !results || !more) return;

    const setOpen = (open) => {
      panel.hidden = !open;
      input.setAttribute('aria-expanded', String(open));
      if (!open) ++requestVersion;
    };

    const renderNext = () => {
      const next = matches.slice(shown, shown + batchSize);
      next.forEach(({ article }) => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        const title = document.createElement('h3');
        const meta = document.createElement('p');
        const summary = document.createElement('p');

        link.href = article.url;
        title.textContent = article.title;
        meta.className = 'search-result-meta';
        meta.textContent = [article.date, ...(article.tags || [])].filter(Boolean).join(' · ');
        const body = String(article.content || '').normalize('NFKC').replace(/\s+/g, ' ');
        const offset = terms.map((term) => normalize(body).indexOf(term)).find((position) => position >= 0);
        const start = Math.max(0, (offset ?? 0) - 35);
        summary.textContent = offset === undefined
          ? article.description
          : `${start ? '…' : ''}${body.slice(start, start + 150)}${body.length > start + 150 ? '…' : ''}`;

        link.append(title, meta, summary);
        item.append(link);
        results.append(item);
      });
      shown += next.length;
      more.hidden = shown >= matches.length;
      status.textContent = matches.length
        ? `找到 ${matches.length} 篇匹配文章，已显示 ${shown} 篇。`
        : '没有找到匹配的文章。';
    };

    const search = () => {
      const keyword = normalize(input.value).trim();
      const currentVersion = ++requestVersion;
      results.replaceChildren();
      more.hidden = true;
      matches = [];
      shown = 0;
      setOpen(true);

      if (keyword.length < 2) {
        status.textContent = '输入至少两个字符。';
        return;
      }

      terms = keyword.split(/\s+/);
      status.textContent = '正在搜索…';
      loadIndex(indexUrl)
        .then((articles) => {
          if (currentVersion !== requestVersion) return;
          matches = articles.map((article) => {
            const scores = terms.map((term) => {
              const field = article.fields.findIndex((text) => text.includes(term));
              return field < 0 ? 0 : [100, 30, 10, 1][field];
            });
            return { article, score: scores.every(Boolean) ? scores.reduce((a, b) => a + b, 0) : 0 };
          }).filter(({ score }) => score > 0)
            .sort((a, b) => b.score - a.score || b.article.date.localeCompare(a.article.date));
          renderNext();
        })
        .catch(() => {
          if (currentVersion !== requestVersion) return;
          status.textContent = '搜索索引加载失败，请重新输入以重试。';
        });
    };

    more.addEventListener('click', () => {
      const firstNew = shown;
      renderNext();
      results.children[firstNew]?.querySelector('a').focus();
    });
    input.addEventListener('focus', search);
    input.addEventListener('input', (event) => {
      if (!event.isComposing) search();
    });
    input.addEventListener('compositionend', search);
    container.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        input.focus();
        setOpen(false);
      }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        const links = [...results.querySelectorAll('a')];
        const current = links.indexOf(document.activeElement);
        const target = event.key === 'ArrowDown' ? links[current + 1] : links[current - 1];
        if (target || (event.key === 'ArrowUp' && current === 0)) {
          event.preventDefault();
          (target || input).focus();
        }
      }
    });
    container.addEventListener('focusout', (event) => {
      if (!container.contains(event.relatedTarget)) setOpen(false);
    });
    document.addEventListener('click', (event) => {
      if (!container.contains(event.target)) setOpen(false);
    });
  });
})();
