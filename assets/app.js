/* ECG preloader. Holds long enough to actually see a beat on first load,
   then gets out of the way on every page after that. */
(function () {
  var el = document.getElementById('preload');
  if (!el) return;

  var seen = false;
  try { seen = sessionStorage.getItem('ds-seen') === '1'; } catch (e) {}
  var hold = seen ? 300 : 1500;
  var t0 = Date.now();

  function bye() {
    setTimeout(function () {
      el.classList.add('gone');
      try { sessionStorage.setItem('ds-seen', '1'); } catch (e) {}
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 450);
    }, Math.max(0, hold - (Date.now() - t0)));
  }

  if (document.readyState === 'complete') bye();
  else window.addEventListener('load', bye);

  /* never trap the page if something stalls */
  setTimeout(function () { el.classList.add('gone'); }, 6000);
})();

/* Structure cards: "what this part actually is" expands in place.
   Detail ships visible, so with JS off nothing is hidden. */
(function () {
  var btns = [].slice.call(document.querySelectorAll('.st-more'));
  if (!btns.length) return;

  btns.forEach(function (b) {
    var d = document.getElementById(b.getAttribute('aria-controls'));
    if (!d) return;
    d.hidden = true;
    b.addEventListener('click', function () {
      var open = b.getAttribute('aria-expanded') === 'true';
      b.setAttribute('aria-expanded', String(!open));
      d.hidden = open;
    });
  });
})();

/* Home page anatomy picker. Panels ship visible so the page still works with
   JS off; this hides them and turns the tiles into an accordion. */
(function () {
  var root = document.getElementById('anatomy');
  if (!root) return;

  var tiles = [].slice.call(root.querySelectorAll('.tile[data-sys]'));
  var panels = [].slice.call(root.querySelectorAll('.panel[data-panel]'));
  if (!tiles.length || !panels.length) return;

  panels.forEach(function (p) { p.hidden = true; });
  root.classList.add('animate');

  var open = null;

  function show(id, scroll) {
    tiles.forEach(function (t) {
      var on = t.getAttribute('data-sys') === id;
      t.setAttribute('aria-expanded', String(on));
      var lbl = t.querySelector('.tile-open');
      if (lbl) lbl.textContent = on ? 'Close' : 'Open';
    });
    panels.forEach(function (p) { p.hidden = p.getAttribute('data-panel') !== id; });
    open = id;
    if (window.history.replaceState) {
      window.history.replaceState(null, '', '#' + id);
    }
    if (scroll) {
      var p = root.querySelector('.panel[data-panel="' + id + '"]');
      if (p) p.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function hide() {
    tiles.forEach(function (t) { t.setAttribute('aria-expanded', 'false'); });
    panels.forEach(function (p) { p.hidden = true; });
    open = null;
    if (window.history.replaceState) {
      window.history.replaceState(null, '', window.location.pathname);
    }
  }

  tiles.forEach(function (t) {
    t.addEventListener('click', function () {
      var id = t.getAttribute('data-sys');
      if (open === id) { hide(); } else { show(id, true); }
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && open) hide();
  });

  var hash = (window.location.hash || '').replace('#', '');
  if (hash && panels.some(function (p) { return p.getAttribute('data-panel') === hash; })) {
    show(hash, false);
  }
})();

(function () {
  var box = document.getElementById('q');
  var out = document.getElementById('results');
  if (!box || !out || !window.INDEX) return;

  var base = document.body.getAttribute('data-base') || '';

  function render(items) {
    if (!items.length) { out.innerHTML = ''; return; }
    out.innerHTML = items.slice(0, 9).map(function (it) {
      return '<li><a href="' + base + it.url + '"><span class="k">' +
        it.kind + '</span>' + it.name + '</a></li>';
    }).join('');
  }

  function search(term) {
    term = term.trim().toLowerCase();
    if (term.length < 2) { out.innerHTML = ''; return; }
    var starts = [], contains = [];
    for (var i = 0; i < window.INDEX.length; i++) {
      var it = window.INDEX[i];
      var hay = (it.name + ' ' + (it.alt || '')).toLowerCase();
      var pos = hay.indexOf(term);
      if (pos === 0) starts.push(it);
      else if (pos > 0) contains.push(it);
    }
    render(starts.concat(contains));
  }

  box.addEventListener('input', function () { search(box.value); });
  box.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { box.value = ''; out.innerHTML = ''; box.blur(); }
    if (e.key === 'Enter') {
      var first = out.querySelector('a');
      if (first) window.location.href = first.getAttribute('href');
    }
  });
})();
