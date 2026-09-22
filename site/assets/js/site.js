/* Pathfinder Driveways & Construction — site behaviour. No dependencies. */
(function () {
  'use strict';

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var panel = document.getElementById('mobile-nav');
  if (toggle && panel) {
    // While the full-screen menu is open, the page behind it can't be reached by keyboard or screen reader.
    var behind = document.querySelectorAll('main, .site-footer, .quick-contact');
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      panel.hidden = !open;
      document.body.classList.toggle('is-locked', open);
      behind.forEach(function (el) { if (open) el.setAttribute('inert', ''); else el.removeAttribute('inert'); });
    };
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) { setOpen(false); toggle.focus(); }
    });
    panel.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });
    var desktop = window.matchMedia('(min-width: 1080px)');
    var onResize = function (mq) { if (mq.matches) setOpen(false); };
    // Safari < 14 only has the older addListener API; calling addEventListener there would stop the whole script.
    if (desktop.addEventListener) desktop.addEventListener('change', onResize); else if (desktop.addListener) desktop.addListener(onResize);
  }

  /* ---------- WhatsApp: pre-written message naming the service being viewed ---------- */
  var waLinks = Array.prototype.slice.call(document.querySelectorAll('[data-wa]'));
  var waBase = waLinks.length ? waLinks[0].getAttribute('href').split('?')[0] : '';
  var waDefault = document.body.getAttribute('data-wa-topic') || '';
  var WA_TOPICS = {
    paving: 'paving', tarmac: 'tarmac construction', construction: 'building or renovation work',
    renovations: 'renovation work', pavers: 'pavers', other: ''
  };
  function setWaTopic(topic) {
    var text = 'Hello Pathfinder, I would like a quote for ' + (topic || 'my project') + '.';
    waLinks.forEach(function (a) { a.href = waBase + '?text=' + encodeURIComponent(text); });
  }
  setWaTopic(waDefault);

  // Services page: follow whichever service section is on screen.
  var waBlocks = Array.prototype.slice.call(document.querySelectorAll('main [data-wa-topic]'));
  if (waBlocks.length && 'IntersectionObserver' in window) {
    var ratios = new Map();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { ratios.set(e.target, e.intersectionRatio); });
      var best = null, bestRatio = 0.1;
      ratios.forEach(function (r, el) { if (r > bestRatio) { best = el; bestRatio = r; } });
      setWaTopic(best ? best.getAttribute('data-wa-topic') : waDefault);
    }, { threshold: [0, 0.1, 0.25, 0.5, 0.75, 1] });
    waBlocks.forEach(function (b) { io.observe(b); });
  }

  // Keyboard users: never leave the focused element hidden under the floating WhatsApp button (WCAG 2.4.11).
  var waFloat = document.querySelector('.wa-float');
  if (waFloat) {
    document.addEventListener('focusin', function (e) {
      if (waFloat.contains(e.target)) return;
      // The browser scrolls a newly focused element into view after this event, so check once that has happened.
      setTimeout(function () {
        var a = e.target.getBoundingClientRect(), b = waFloat.getBoundingClientRect();
        if (a.bottom > b.top && a.top < b.bottom && a.right > b.left && a.left < b.right) {
          window.scrollBy(0, a.bottom - b.top + 16);
        }
      }, 0);
    });
  }

  /* ---------- Enquiry form ---------- */
  var form = document.querySelector('.enquiry-form');
  var SERVICE_LABELS = {
    paving: 'Paving', tarmac: 'Tarmac construction', construction: 'Building & renovations',
    renovations: 'Building & renovations', pavers: 'Pavers (supply only)', other: 'Something else'
  };

  function focusFirstField() {
    if (!form) return;
    var first = form.querySelector('input, select, textarea');
    if (first) first.focus({ preventScroll: true });
  }

  document.querySelectorAll('[data-focus-form]').forEach(function (link) {
    link.addEventListener('click', function () {
      if (form && link.getAttribute('href') === '#enquiry') setTimeout(focusFirstField, 350);
    });
  });

  if (form) {
    var field = function (name) { return form.querySelector('[name="' + name + '"]'); };
    // Prefill from links such as contact/index.html?service=tarmac or ?product=Hexagonal%20Pavers
    var params = new URLSearchParams(window.location.search);
    var service = params.get('service');
    var product = params.get('product');
    if (service === 'renovations') service = 'construction';
    if (product) service = 'pavers';
    if (service && field('service').querySelector('option[value="' + service + '"]')) field('service').value = service;
    if (product && !field('message').value) field('message').value = 'I would like a quote for ' + product + '.\n\n';
    if (product) setWaTopic(product);
    else if (service && WA_TOPICS[service]) setWaTopic(WA_TOPICS[service]);
    field('service').addEventListener('change', function () {
      setWaTopic(WA_TOPICS[field('service').value] || waDefault);
    });

    var status = form.querySelector('.form-status');
    var submit = form.querySelector('[type="submit"]');
    var submitLabel = submit.textContent;
    var email = form.getAttribute('data-email');

    var messages = {
      name: 'Enter your name.',
      phone: 'Enter a phone number we can reach you on.',
      email: 'Enter a valid email address, or leave this blank.',
      service: 'Choose the service you need.',
      message: 'Tell us a little about your project.'
    };

    var setError = function (input, text) {
      var err = document.getElementById(input.id + '-error');
      input.setAttribute('aria-invalid', text ? 'true' : 'false');
      if (err) err.textContent = text || '';
    };

    var validate = function (input) {
      var value = input.value.trim();
      var bad = (input.required && !value) ||
        (input.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) ||
        (input.type === 'tel' && value && value.replace(/\D/g, '').length < 7);
      setError(input, bad ? messages[input.name] : '');
      return !bad;
    };

    form.querySelectorAll('input, select, textarea').forEach(function (input) {
      input.addEventListener('blur', function () { if (input.getAttribute('aria-invalid') === 'true' || input.value) validate(input); });
      input.addEventListener('input', function () { if (input.getAttribute('aria-invalid') === 'true') validate(input); });
    });

    // Status messages are built with text nodes and links, never innerHTML, because they can echo visitor input.
    var setStatus = function (state, text, links) {
      status.setAttribute('data-state', state || '');
      status.textContent = text || '';
      (links || []).forEach(function (l, i) {
        status.appendChild(document.createTextNode(i === 0 ? ' ' : i === links.length - 1 ? ' or ' : ', '));
        var a = document.createElement('a');
        a.href = l.href;
        a.textContent = l.label;
        if (l.external) { a.target = '_blank'; a.rel = 'noopener'; }
        status.appendChild(a);
      });
      if (links && links.length) status.appendChild(document.createTextNode('.'));
    };

    var busy = function (on) {
      submit.disabled = on;
      submit.setAttribute('aria-busy', String(on));
      submit.textContent = on ? 'Sending…' : submitLabel;
    };

    var summary = function () {
      var d = new FormData(form);
      return [
        'Name: ' + d.get('name'),
        'Phone: ' + d.get('phone'),
        'Email: ' + (d.get('email') || '-'),
        'Service: ' + (SERVICE_LABELS[d.get('service')] || d.get('service')),
        'Project location: ' + (d.get('location') || '-'),
        '',
        d.get('message')
      ].join('\n');
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      setStatus('', '');
      var fields = Array.prototype.slice.call(form.querySelectorAll('input, select, textarea'));
      var invalid = fields.filter(function (f) { return !validate(f); });
      if (invalid.length) {
        setStatus('error', 'Please check the highlighted field' + (invalid.length > 1 ? 's' : '') + '.');
        invalid[0].focus();
        return;
      }

      var subject = 'Website enquiry: ' + (SERVICE_LABELS[field('service').value] || 'Project') + ' - ' + field('name').value.trim();
      var mailto = 'mailto:' + email + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(summary());
      var fallbacks = [
        { label: 'send it from your email app', href: mailto },
        { label: 'WhatsApp us', href: waLinks.length ? waLinks[0].href : 'tel:+263242788113', external: true },
        { label: 'call 0242 788 113', href: 'tel:+263242788113' }
      ];

      var endpoint = form.getAttribute('data-endpoint');
      if (!endpoint) {
        // No sending script configured: hand the enquiry to the visitor's email app.
        window.location.href = mailto;
        setStatus('success', 'Your email app should now open with your enquiry ready to send. If it doesn’t, you can', fallbacks.slice(1));
        return;
      }

      busy(true);
      fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (res) {
          return res.json().catch(function () { return {}; }).then(function (data) { return { res: res, data: data }; });
        })
        .then(function (r) {
          if (r.res.ok && r.data.ok) {
            form.reset();
            setStatus('success', r.data.message || 'Thank you. Your enquiry has been sent.');
          } else if (r.res.status === 422 && r.data.message) {
            setStatus('error', r.data.message);
          } else {
            setStatus('error', (r.data.message || 'Sorry, your enquiry could not be sent just now.') + ' You can', fallbacks);
          }
        })
        .catch(function () {
          setStatus('error', 'Sorry, your enquiry could not be sent just now. You can', fallbacks);
        })
        .then(function () { busy(false); });
    });
  }

  /* ---------- Projects: filter ---------- */
  var grid = document.querySelector('.project-grid');
  if (grid) {
    var items = Array.prototype.slice.call(grid.children);
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.filter-btn'));
    var empty = document.getElementById('projects-empty');
    var emptyTitle = document.getElementById('empty-title');
    var emptyCta = document.getElementById('empty-cta');
    var filterStatus = document.getElementById('filter-status');
    var emptyBase = emptyCta.getAttribute('href').split('#')[0];

    var count = function (key) {
      return key === 'all' ? items.length : items.filter(function (li) {
        return li.getAttribute('data-categories').split(' ').indexOf(key) > -1;
      }).length;
    };
    buttons.forEach(function (b) {
      var n = document.createElement('span');
      n.className = 'filter-count';
      n.textContent = '(' + count(b.getAttribute('data-filter')) + ')';
      b.appendChild(n);
    });

    var applyFilter = function (key, updateUrl) {
      if (!buttons.some(function (b) { return b.getAttribute('data-filter') === key; })) key = 'all';
      var shown = 0;
      items.forEach(function (li) {
        var match = key === 'all' || li.getAttribute('data-categories').split(' ').indexOf(key) > -1;
        li.hidden = !match;
        if (match) shown++;
      });
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-filter') === key)); });
      var btn = document.querySelector('.filter-btn[data-filter="' + key + '"]');
      var label = key === 'all' ? 'all' : (btn.getAttribute('data-noun') || btn.firstChild.textContent.trim());
      empty.hidden = shown > 0;
      if (!shown) {
        emptyTitle.textContent = label + ' projects are coming soon';
        emptyCta.setAttribute('href', emptyBase + '?service=' + key + '#enquiry');
      }
      filterStatus.textContent = 'Showing ' + shown + ' ' + (key === 'all' ? '' : label.toLowerCase() + ' ') + 'project' + (shown === 1 ? '' : 's') + '.';
      if (updateUrl) {
        var url = new URL(window.location.href);
        if (key === 'all') url.searchParams.delete('filter'); else url.searchParams.set('filter', key);
        url.hash = '';
        history.replaceState(null, '', url);
      }
    };
    buttons.forEach(function (b) {
      b.addEventListener('click', function () { applyFilter(b.getAttribute('data-filter'), true); });
    });
    applyFilter(new URLSearchParams(window.location.search).get('filter') || 'all', false);
  }

  /* ---------- Projects: detail dialog ---------- */
  var dialog = document.getElementById('project-dialog');
  if (dialog && typeof dialog.showModal === 'function') {
    var img = document.getElementById('dialog-img');
    var thumbs = document.getElementById('dialog-thumbs');
    var cta = document.getElementById('dialog-cta');
    var ctaBase = cta.getAttribute('href').split('#')[0];
    var opener = null;

    var showImage = function (data) {
      img.src = data.large;
      img.srcset = data.srcset;
      img.sizes = '(min-width: 1000px) 60rem, 100vw';
      img.alt = data.alt;
      img.width = data.w;
      img.height = data.h;
    };

    var openProject = function (article, trigger) {
      var p = JSON.parse(article.getAttribute('data-project'));
      opener = trigger || null;
      document.getElementById('dialog-title').textContent = p.title;
      document.getElementById('dialog-tag').textContent = p.tag;
      document.getElementById('dialog-service').textContent = p.service.charAt(0).toUpperCase() + p.service.slice(1);
      document.getElementById('dialog-location').textContent = p.location;
      document.getElementById('dialog-location-row').hidden = !p.location;
      document.getElementById('dialog-desc').textContent = p.description;
      cta.setAttribute('href', ctaBase + '?service=' + p.category + '#enquiry');
      setWaTopic(p.service.charAt(0).toLowerCase() + p.service.slice(1) + ' (similar to your ' + p.title + ' project)');
      showImage(p.images[0]);
      thumbs.innerHTML = '';
      thumbs.hidden = p.images.length < 2;
      if (p.images.length > 1) {
        p.images.forEach(function (im, i) {
          var li = document.createElement('li');
          var b = document.createElement('button');
          b.type = 'button';
          b.setAttribute('aria-label', 'Show photo ' + (i + 1) + ' of ' + p.images.length);
          b.setAttribute('aria-current', String(i === 0));
          var t = document.createElement('img');
          t.src = im.thumb; t.alt = ''; t.width = 80; t.height = 53;
          b.appendChild(t);
          b.addEventListener('click', function () {
            showImage(im);
            thumbs.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-current', String(x === b)); });
          });
          li.appendChild(b);
          thumbs.appendChild(li);
        });
      }
      dialog.showModal();
      dialog.scrollTop = 0;
      if (history.replaceState) history.replaceState(null, '', '#' + article.id);
    };

    document.querySelectorAll('[data-open-project]').forEach(function (b) {
      b.addEventListener('click', function () { openProject(b.closest('article'), b); });
    });
    dialog.querySelector('[data-close-dialog]').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener('close', function () {
      setWaTopic(waDefault);
      if (history.replaceState) history.replaceState(null, '', window.location.pathname + window.location.search);
      if (opener) opener.focus();
    });

    // Open straight to a project when arriving from a "View Project" link, e.g. projects/#winston-park
    var target = window.location.hash && document.getElementById(window.location.hash.slice(1));
    if (target && target.hasAttribute('data-project')) {
      var li = target.closest('li');
      if (li && li.hidden) applyFilterAll();
      target.scrollIntoView({ block: 'center' });
      openProject(target, target.querySelector('[data-open-project]'));
    }
  }

  function applyFilterAll() {
    var all = document.querySelector('.filter-btn[data-filter="all"]');
    if (all) all.click();
  }
})();
