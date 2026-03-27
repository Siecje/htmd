async function goToRandomPost() {
    const response = await fetch('/posts.json');
    const allPosts = await response.json();

    const visited = new Set(JSON.parse(localStorage.getItem('visitedPosts')) || []);

    let pool = allPosts.filter(url => !visited.has(url));

    // Fallback: If everything is read, use everything EXCEPT the current page
    if (pool.length === 0) {
        const currentPath = window.location.pathname;
        pool = allPosts.filter(url => url !== currentPath);
    }

    if (pool.length > 0) {
        const randomTarget = pool[Math.floor(Math.random() * pool.length)];
        window.location.href = randomTarget;
    }
}

function markCurrentPostAsVisited () {
  const currentPost = window.location.pathname;
  const visited = new Set(JSON.parse(localStorage.getItem('visitedPosts')) || []);
  if (!visited.has(currentPost)) {
    visited.add(currentPost);
    localStorage.setItem('visitedPosts', JSON.stringify([...visited]));
  }
}

(function addHeadingAnchors(options = {}) {
  const {
    selector = 'h2,h3,h4,h5,h6',
    icon = '🔗',
    iconClass = 'heading-link-icon',
    copyOnClick = false,
    usePushState = false
  } = options;

  const slugify = s =>
    s.toString().trim().toLowerCase()
      .replace(/—/g, '-')
      .replace(/&/g, '-and-')
      .replace(/[^a-z0-9\- ]+/g, '')
      .replace(/\s+/g, '-')
      .replace(/\-+/g, '-')
      .replace(/^\-|\-$/g, '');

  document.querySelectorAll(selector).forEach(heading => {
    const text = heading.textContent.trim();
    if (!text) {
      return;
    }

    let id = heading.id;
    if (!id) {
      id = slugify(text) || ('section-' + Math.random().toString(36).slice(2, 8));
      let suffix = 1;
      while (document.getElementById(id)) {
        id = id.replace(/-\d+$/, '') + '-' + suffix++;
      }
      heading.id = id;
    }

    if (heading.querySelector(`.${iconClass}`)) {
      return;
    }

    const a = document.createElement('a');
    a.href = '#' + id;
    a.className = iconClass;
    a.setAttribute('aria-label', `Link to ${text}`);
    a.title = `Link to ${text}`;
    // a.innerText = icon;
    a.innerHTML = '<svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" focusable="false" role="img"><path fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" d="M10.59 13.41a3 3 0 0 0 4.24 0l3-3a3 3 0 0 0-4.24-4.24l-1.06 1.06M13.41 10.59a3 3 0 0 0-4.24 0l-3 3a3 3 0 0 0 4.24 4.24l1.06-1.06"/></svg>';

    // inline fallbacks
    a.style.textDecoration = 'none';
    a.style.color = '#1a73e8';
    a.style.cursor = 'pointer';
    a.style.fontSize = '0.9em';
    a.style.transition = 'opacity .12s ease, color .12s ease';


    a.addEventListener('click', async (e) => {
      e.preventDefault();
      const newHash = '#' + id;
      if (usePushState) {
        history.pushState(null, '', newHash);
      }
      else {
        history.replaceState(null, '', newHash);
      }

      heading.setAttribute('tabindex', '-1');
      heading.focus({ preventScroll: true });

      if (copyOnClick && navigator.clipboard) {
        try {
          await navigator.clipboard.writeText(
            location.origin + location.pathname + location.search + newHash
          );
        }
        catch (err) { /* ignore */ }
      }
    });

    heading.appendChild(a);
  });
})();
