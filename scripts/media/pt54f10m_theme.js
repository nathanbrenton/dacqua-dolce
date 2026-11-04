/* PT54-F10M: local Aesthetic Lab. Option values come from the current storefront's theme source. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const toggle = byId('media-theme-toggle');
  const panel = byId('media-theme-lab');
  const close = byId('media-theme-close');
  const logoImage = byId('media-footer-logo');
  const logoFallback = byId('media-footer-logo-fallback');
  const fields = {theme: byId('media-theme-color'), appearance: byId('media-theme-appearance'),
    typography: byId('media-theme-typography'), logo: byId('media-theme-logo')};
  const key = 'dacqua-media-manager-aesthetic-lab-v1';
  let options;
  const getStored = () => {
    try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch { return {}; }
  };
  const save = values => {
    try { localStorage.setItem(key, JSON.stringify(values)); } catch { /* private browsing */ }
  };
  const safeValues = values => {
    const allowed = {theme: options.themes, appearance: options.appearance,
      typography: options.typography, logo: options.logos};
    const result = {};
    for (const name of Object.keys(fields)) {
      result[name] = allowed[name].some(item => item.id === values[name])
        ? values[name] : options.defaults[name];
    }
    return result;
  };
  const apply = values => {
    const setting = safeValues(values);
    for (const [name, select] of Object.entries(fields)) select.value = setting[name];
    document.documentElement.dataset.theme = setting.theme;
    document.documentElement.dataset.appearance = setting.appearance;
    document.documentElement.dataset.typography = setting.typography;
    logoImage.src = '/site-logo?id=' + encodeURIComponent(setting.logo);
    logoImage.hidden = false;
    logoFallback.hidden = true;
    return setting;
  };
  const setOpen = open => {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
  };
  const init = async () => {
    const response = await fetch('/api/theme-options', {cache: 'no-store'});
    if (!response.ok) throw new Error('Cannot load storefront theme options');
    options = await response.json();
    const data = {theme: options.themes, appearance: options.appearance,
      typography: options.typography, logo: options.logos};
    for (const [name, select] of Object.entries(fields)) {
      select.replaceChildren();
      for (const item of data[name]) {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.label + (item.detail ? ' — ' + item.detail : '');
        select.append(option);
      }
      select.addEventListener('change', () => {
        const values = {};
        for (const [k, control] of Object.entries(fields)) values[k] = control.value;
        save(apply(values));
      });
    }
    apply(getStored());
    toggle.addEventListener('click', () => setOpen(panel.hidden));
    close.addEventListener('click', () => setOpen(false));
    byId('media-theme-reset').addEventListener('click', () => {
      save(apply(options.defaults));
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !panel.hidden) { setOpen(false); toggle.focus(); }
    });
    document.addEventListener('click', event => {
      if (!panel.hidden && !panel.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });
    logoImage.addEventListener('error', () => { logoImage.hidden = true; logoFallback.hidden = false; });
  };
  init().catch(error => {
    toggle.disabled = true;
    toggle.title = 'Theme options unavailable: ' + error.message;
  });
})();
