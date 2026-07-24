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
