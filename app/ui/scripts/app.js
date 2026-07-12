      const API_BASE = "/api/v1";
      const HOME_BASE = '/home';
      const TOKEN_STORAGE_KEY = 'dococr.keycloak.tokens';
      const PKCE_VERIFIER_KEY = 'dococr.pkce.verifier';
      const OAUTH_STATE_KEY = 'dococr.oauth.state';
      const OAUTH_MODE_KEY = 'dococr.oauth.mode';
      const SILENT_AUTH_ATTEMPT_KEY = 'dococr.oauth.silent_attempted';
      const SIGN_IN_MESSAGE = 'Sign in with Keycloak before using protected document, job, search, or admin actions.';
      const identityKeys = ['demoSub', 'demoEmail', 'demoName', 'demoRoles'];
      const terminalJobStatuses = new Set(['completed', 'failed', 'cancelled']);
      const publicRoutes = new Set(['/home', '/home/help', '/home/not-found']);
      const routes = {
        '/home': { page: 'homePage', nav: 'home' },
        '/home/upload': { page: 'uploadPage', nav: 'upload' },
        '/home/documents': { page: 'documentsPage', nav: 'documents' },
        '/home/jobs': { page: 'jobsPage', nav: 'jobs' },
        '/home/search': { page: 'searchPage', nav: 'search' },
        '/home/identity': { page: 'identityPage', nav: 'identity' },
        '/home/admin': { page: 'adminPage', nav: 'admin' },
        '/home/logs': { page: 'logsPage', nav: 'logs' },
        '/home/help': { page: 'helpPage', nav: 'help' },
        '/home/not-found': { page: 'notFoundPage', nav: null }
      };

      let pollTimer = null;
      let authConfig = { provider: 'local' };
      let tokenSet = loadTokenSet();
      let currentMe = null;
      let selectedDocumentId = '';
      let selectedJobId = '';
      let documentsCache = [];
      let documentsLoaded = false;
      let jobsLoaded = false;
      let routeLoaded = false;
      let authReady = false;
      let toastTimer = null;
      const initialPath = window.location.pathname;

      const $ = (id) => document.getElementById(id);
      const $$ = (selector) => Array.from(document.querySelectorAll(selector));
      const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      function escapeHtml(value) {
        return String(value ?? '')
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;')
          .replaceAll('"', '&quot;')
          .replaceAll("'", '&#039;');
      }

      function format(value) {
        if (typeof value === 'string') return value;
        return JSON.stringify(value, null, 2);
      }

      function writeOutput(id, value) {
        const output = $(id);
        if (output) output.textContent = format(value);
      }

      function notify(message, type = 'info') {
        clearTimeout(toastTimer);
        const output = $('toastRegion');
        output.innerHTML = `<div class='toast ${escapeHtml(type)}'>${escapeHtml(message)}</div>`;
        toastTimer = setTimeout(() => {
          output.innerHTML = '';
        }, 5200);
      }

      function setError(id, message = '') {
        const output = $(id);
        if (output) output.textContent = message;
      }

      function logRequest(method, path, status, value) {
        const log = $('apiLog');
        if (!log) return;
        const entry = `[${new Date().toLocaleTimeString()}] ${method} ${path} -> ${status}\n${format(value)}`;
        log.textContent = log.textContent === 'No requests yet.' ? entry : `${entry}\n\n${log.textContent}`;
      }

      function apiErrorMessage(data, status) {
        if (status === 401 && data && data.error && data.error.code === 'AUTH_UNAUTHORIZED') return SIGN_IN_MESSAGE;
        if (data && data.error) return `${data.error.code}: ${data.error.message}`;
        if (data && data.error_description) return data.error_description;
        if (data && data.detail) return typeof data.detail === 'string' ? data.detail : format(data.detail);
        return `Request failed with status ${status}`;
      }

      async function parseResponse(response) {
        const text = await response.text();
        try {
          return text ? JSON.parse(text) : null;
        } catch (_error) {
          return text;
        }
      }

      async function request(path, options = {}) {
        const method = options.method || 'GET';
        const { auth = true, ...fetchOptions } = options;
        if (auth && authConfig.provider === 'keycloak' && !isSignedIn()) {
          showSignInRequired();
          throw new Error(SIGN_IN_MESSAGE);
        }
        const headers = { ...(auth ? await authHeaders() : {}), ...(fetchOptions.headers || {}) };
        const response = await fetch(path, { ...fetchOptions, headers });
        const data = await parseResponse(response);
        logRequest(method, path, response.status, data);
        if (!response.ok) {
          if (response.status === 401) showSignInRequired();
          throw new Error(apiErrorMessage(data, response.status));
        }
        return data;
      }

      async function withBusy(buttonId, busyText, task) {
        const button = buttonId ? $(buttonId) : null;
        const original = button ? button.textContent : '';
        if (button) {
          button.disabled = true;
          button.textContent = busyText;
        }
        try {
          return await task();
        } finally {
          if (button) {
            button.disabled = false;
            button.textContent = original;
          }
        }
      }

      function loadingMarkup(count = 3) {
        return `<div class='skeleton-grid'>${Array.from({ length: count }, () => `<div class='skeleton-card'></div>`).join('')}</div>`;
      }

      function statusClass(status) {
        return String(status || 'pending').toLowerCase().replace(/[^a-z0-9_-]/g, '-');
      }

      function statusBadge(status) {
        const value = status || 'unknown';
        return `<span class='status ${escapeHtml(statusClass(value))}'>${escapeHtml(value)}</span>`;
      }

      function renderMetaItems(items) {
        return `
          <div class='card-meta'>
            ${items.map((item) => `
              <span class='meta-item'>
                <span class='meta-label'>${escapeHtml(item.label)}</span>
                <span class='meta-value${item.mono ? ' mono' : ''}'>${escapeHtml(item.value ?? '-')}</span>
              </span>`).join('')}
          </div>`;
      }

      function renderToolbar(title, accessory = '', subtitle = '') {
        return `
          <div class='toolbar'>
            <div>
              <h3>${title}</h3>
              ${subtitle ? `<p class='fine-print'>${subtitle}</p>` : ''}
            </div>
            ${accessory}
          </div>`;
      }

      function renderEntityCard(type, body, selected = false) {
        return `<article class='${escapeHtml(type)}-card${selected ? ' selected' : ''}'>${body}</article>`;
      }

      function formatDate(value) {
        if (!value) return '-';
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
      }

      function formatBytes(value) {
        const bytes = Number(value || 0);
        if (!bytes) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
      }

      function shortId(value) {
        const text = String(value || '');
        return text.length > 16 ? `${text.slice(0, 8)}...${text.slice(-6)}` : text;
      }

      function normalizePath(pathname) {
        if (!pathname.startsWith(HOME_BASE)) return '/home/not-found';
        if (pathname === HOME_BASE || pathname === `${HOME_BASE}/`) return HOME_BASE;
        return pathname.endsWith('/') ? pathname.slice(0, -1) : pathname;
      }

      function resolveRoute(pathname) {
        const normalized = normalizePath(pathname);
        if (routes[normalized]) return { path: normalized, unknownPath: null };
        return { path: '/home/not-found', unknownPath: normalized };
      }

      function isGuestUser() {
        return authReady && authConfig.provider === 'keycloak' && !isSignedIn();
      }

      function isPublicRoute(path) {
        return publicRoutes.has(path);
      }

      function canAccessRoute(path) {
        if (!authReady || isPublicRoute(path)) return true;
        if (path === '/home/admin') return hasAdminRole();
        return !isGuestUser();
      }

      function navigateTo(path, options = {}) {
        const { push = true, focus = true } = options;
        const update = () => renderRoute(path, { push, focus });
        if (document.startViewTransition && !prefersReducedMotion()) {
          document.startViewTransition(update);
          return;
        }
        update();
      }

      function renderRoute(path, options = {}) {
        const { push = true, focus = true } = options;
        const resolved = resolveRoute(path);
        const routePath = canAccessRoute(resolved.path) ? resolved.path : '/home';
        const route = routes[routePath];
        if (push && window.location.pathname !== path) {
          window.history.pushState({}, '', path);
        }
        if (routePath !== resolved.path && window.location.pathname !== HOME_BASE) {
          window.history.replaceState({}, '', HOME_BASE);
        }

        for (const section of $$('[data-page]')) {
          section.hidden = section.id !== route.page;
        }
        for (const link of $$('[data-nav]')) {
          if (link.dataset.nav === route.nav) link.setAttribute('aria-current', 'page');
          else link.removeAttribute('aria-current');
        }

        if (resolved.unknownPath) $('notFoundPath').textContent = resolved.unknownPath;
        if (routePath !== resolved.path && authReady) {
          notify(resolved.path === '/home/admin' ? 'Admin access requires the admin role.' : SIGN_IN_MESSAGE, 'error');
        }
        if (focus) focusPageHeading(route.page);
        afterRouteEnter(routePath);
        routeLoaded = true;
      }

      function focusPageHeading(pageId) {
        const heading = $(`${pageId}`).querySelector('h1');
        if (heading) heading.focus({ preventScroll: true });
      }

      function afterRouteEnter(routePath) {
        if (!authReady && !isPublicRoute(routePath)) return;
        if (!canAccessRoute(routePath)) return;
        if (routePath === '/home/documents' && !documentsLoaded) listDocuments();
        if (routePath === '/home/jobs' && !jobsLoaded) listJobs();
        if (routePath === '/home/admin') renderAdminAccessState();
      }

      function setupNavigation() {
        document.addEventListener('click', (event) => {
          const target = event.target instanceof Element ? event.target.closest('[data-navigate]') : null;
          if (!target) return;
          const path = target.getAttribute('data-navigate');
          if (!path) return;
          event.preventDefault();
          navigateTo(path);
        });
        window.addEventListener('popstate', () => navigateTo(window.location.pathname, { push: false }));
      }

      function setupTooltips() {
        const hideAll = () => $$('.tooltip.visible').forEach((tooltip) => tooltip.classList.remove('visible'));
        for (const trigger of $$('.tooltip-trigger')) {
          const tooltip = trigger.nextElementSibling;
          const show = () => {
            hideAll();
            if (tooltip) tooltip.classList.add('visible');
          };
          const hide = () => {
            if (tooltip) tooltip.classList.remove('visible');
          };
          trigger.addEventListener('focus', show);
          trigger.addEventListener('mouseenter', show);
          trigger.addEventListener('blur', hide);
          trigger.addEventListener('mouseleave', hide);
        }
        document.addEventListener('keydown', (event) => {
          if (event.key === 'Escape') hideAll();
        });
      }

      function localRoleList() {
        return $('demoRoles').value.split(',').map((role) => role.trim()).filter(Boolean);
      }

      function activeRoles() {
        if (currentMe && Array.isArray(currentMe.roles)) return currentMe.roles;
        const tokenPrincipal = authConfig.provider === 'keycloak' ? principalFromTokens() : null;
        if (tokenPrincipal && Array.isArray(tokenPrincipal.roles)) return tokenPrincipal.roles;
        if (authConfig.provider === 'local') return localRoleList();
        return [];
      }

      function hasAdminRole() {
        return activeRoles().includes('admin:manage');
      }

      function localAuthHeaders() {
        return {
          'x-demo-sub': $('demoSub').value.trim(),
          'x-demo-email': $('demoEmail').value.trim(),
          'x-demo-name': $('demoName').value.trim(),
          'x-demo-roles': $('demoRoles').value.trim()
        };
      }

      async function authHeaders() {
        if (authConfig.provider !== 'keycloak') return localAuthHeaders();
        const token = await ensureAccessToken();
        return token ? { Authorization: `Bearer ${token}` } : {};
      }

      function saveIdentity() {
        for (const key of identityKeys) localStorage.setItem(`dococr.${key}`, $(key).value);
        currentMe = null;
        writeOutput('identityOutput', { saved: true, headers: localAuthHeaders() });
        updateIdentityCards();
        updateAdminVisibility();
        notify('Local identity saved.', 'success');
      }

      function loadIdentity() {
        for (const key of identityKeys) {
          const stored = localStorage.getItem(`dococr.${key}`);
          if (stored !== null) $(key).value = stored;
        }
      }

      function loadTokenSet() {
        const raw = localStorage.getItem(TOKEN_STORAGE_KEY);
        if (!raw) return null;
        try {
          return JSON.parse(raw);
        } catch (_error) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          return null;
        }
      }

      function decodeJwtPayload(token) {
        if (!token) return null;
        const parts = token.split('.');
        if (parts.length < 2) return null;
        try {
          const encoded = parts[1].replaceAll('-', '+').replaceAll('_', '/');
          const padded = encoded.padEnd(Math.ceil(encoded.length / 4) * 4, '=');
          const binary = atob(padded);
          const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
          return JSON.parse(new TextDecoder().decode(bytes));
        } catch (_error) {
          return null;
        }
      }

      function extendRoles(roles, value) {
        if (Array.isArray(value)) roles.push(...value.map(String));
      }

      function cleanRoles(roles) {
        return Array.from(new Set(roles.map((role) => role.trim()).filter(Boolean))).sort();
      }

      function extractTokenRoles(claims) {
        const roles = [];
        const realmAccess = claims && claims.realm_access;
        if (realmAccess && typeof realmAccess === 'object') extendRoles(roles, realmAccess.roles);
        const resourceAccess = claims && claims.resource_access;
        const clientAccess = authConfig.client_id && resourceAccess && typeof resourceAccess === 'object'
          ? resourceAccess[authConfig.client_id]
          : null;
        if (clientAccess && typeof clientAccess === 'object') extendRoles(roles, clientAccess.roles);
        if (typeof claims.scope === 'string') roles.push(...claims.scope.split(' '));
        return cleanRoles(roles);
      }

      function principalFromTokens() {
        const claims = decodeJwtPayload((tokenSet && tokenSet.access_token) || (tokenSet && tokenSet.id_token));
        if (!claims || !claims.sub) return null;
        const fullName = [claims.given_name, claims.family_name].filter(Boolean).join(' ');
        const name = claims.name || fullName || claims.preferred_username || null;
        return {
          sub: String(claims.sub),
          email: claims.email ? String(claims.email) : null,
          name: name ? String(name) : null,
          tenant_id: String(claims.tenant_id || claims.tenant || 'default'),
          roles: extractTokenRoles(claims)
        };
      }

      function storeTokenSet(payload) {
        const previous = tokenSet || {};
        tokenSet = {
          access_token: payload.access_token,
          refresh_token: payload.refresh_token || previous.refresh_token,
          id_token: payload.id_token || previous.id_token,
          expires_at: Date.now() + Number(payload.expires_in || 60) * 1000
        };
        localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenSet));
      }

      function clearTokenSet() {
        tokenSet = null;
        localStorage.removeItem(TOKEN_STORAGE_KEY);
      }

      function base64UrlEncode(bytes) {
        const value = bytes instanceof ArrayBuffer ? new Uint8Array(bytes) : bytes;
        const binary = String.fromCharCode(...value);
        return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
      }

      function randomString() {
        const bytes = new Uint8Array(32);
        crypto.getRandomValues(bytes);
        return base64UrlEncode(bytes);
      }

      async function sha256(value) {
        return crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
      }

      async function fetchAuthConfig() {
        const response = await fetch(`${API_BASE}/auth/config`);
        const data = await parseResponse(response);
        logRequest('GET', `${API_BASE}/auth/config`, response.status, data);
        if (!response.ok) throw new Error(apiErrorMessage(data, response.status));
        authConfig = data;
      }

      function setAuthStatus(text, ok) {
        const status = $('authStatus');
        status.className = ok ? 'status completed' : 'status failed';
        status.textContent = text;
      }

      function isSignedIn() {
        if (authConfig.provider !== 'keycloak') return true;
        if (!tokenSet) return false;
        if (tokenSet.refresh_token) return true;
        return Boolean(tokenSet.access_token && Date.now() < Number(tokenSet.expires_at || 0) - 30000);
      }

      function updateAuthPrompt() {
        const needsSignIn = authConfig.provider === 'keycloak' && !isSignedIn();
        $('authPrompt').hidden = !needsSignIn;
        $('topLoginBtn').hidden = authConfig.provider !== 'keycloak' || isSignedIn();
        updateNavigationVisibility();
        if (authReady && !canAccessRoute(resolveRoute(window.location.pathname).path)) {
          navigateTo(HOME_BASE, { push: false, focus: false });
        }
      }

      function updateNavigationVisibility() {
        const guest = isGuestUser();
        for (const element of $$('[data-auth-only]')) element.hidden = guest;
        for (const link of $$('[data-navigate]')) {
          const path = link.getAttribute('data-navigate');
          if (path && !isPublicRoute(path) && !link.hasAttribute('data-admin-only')) link.hidden = guest;
        }
      }

      function showSignInRequired() {
        updateAuthPrompt();
        notify(SIGN_IN_MESSAGE, 'error');
      }

      function renderSeededAccount() {
        const account = authConfig.seeded_account;
        const output = $('seededAccount');
        if (!account) {
          output.hidden = true;
          output.innerHTML = '';
          return;
        }
        output.hidden = false;
        output.innerHTML = `
          <h3>Seeded local account</h3>
          ${renderMetaItems([
            { label: 'Username', value: account.username, mono: true },
            { label: 'Password', value: account.password, mono: true },
            { label: 'Email', value: account.email }
          ])}`;
      }

      function renderAuthConfig() {
        renderSeededAccount();
        if (authConfig.provider === 'keycloak') {
          $('authHint').textContent = `Using Keycloak realm ${authConfig.realm}. Sign in to receive a bearer token for protected API calls.`;
          $('localIdentityFields').hidden = true;
          $('loginBtn').hidden = false;
          updateAuthPrompt();
          return;
        }
        $('authHint').textContent = 'Using local demo auth. Protected API calls use the local identity values on this page.';
        $('localIdentityFields').hidden = false;
        $('loginBtn').hidden = true;
        updateAuthPrompt();
      }

      function refreshAuthUi() {
        if (authConfig.provider !== 'keycloak') {
          setAuthStatus('Local auth', true);
          $('loginBtn').disabled = true;
          $('logoutBtn').disabled = true;
          updateAuthPrompt();
          return;
        }
        const signedIn = isSignedIn();
        setAuthStatus(signedIn ? 'Signed in' : 'Signed out', signedIn);
        $('loginBtn').disabled = signedIn;
        $('logoutBtn').disabled = !signedIn;
        updateAuthPrompt();
      }

      async function beginAuthorization({ prompt = null } = {}) {
        if (authConfig.provider !== 'keycloak') return;
        const verifier = randomString();
        const challenge = base64UrlEncode(await sha256(verifier));
        const state = randomString();
        sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);
        sessionStorage.setItem(OAUTH_STATE_KEY, state);
        sessionStorage.setItem(OAUTH_MODE_KEY, prompt === 'none' ? 'silent' : 'interactive');

        const params = new URLSearchParams({
          client_id: authConfig.client_id,
          response_type: 'code',
          scope: authConfig.scopes || 'openid profile email',
          redirect_uri: window.location.origin + HOME_BASE,
          code_challenge: challenge,
          code_challenge_method: 'S256',
          state
        });
        if (prompt) params.set('prompt', prompt);
        window.location.assign(`${authConfig.authorization_url}?${params}`);
      }

      async function startLogin() {
        sessionStorage.removeItem(SILENT_AUTH_ATTEMPT_KEY);
        await beginAuthorization();
      }

      async function handleAuthCallback() {
        const url = new URL(window.location.href);
        const error = url.searchParams.get('error');
        const code = url.searchParams.get('code');
        const returnedState = url.searchParams.get('state');
        const expectedState = sessionStorage.getItem(OAUTH_STATE_KEY);
        const mode = sessionStorage.getItem(OAUTH_MODE_KEY);
        if (error) {
          sessionStorage.removeItem(PKCE_VERIFIER_KEY);
          sessionStorage.removeItem(OAUTH_STATE_KEY);
          sessionStorage.removeItem(OAUTH_MODE_KEY);
          window.history.replaceState({}, document.title, HOME_BASE);
          if (mode === 'silent' && (!expectedState || expectedState === returnedState)) return false;
          throw new Error(url.searchParams.get('error_description') || error);
        }
        if (!code) return;

        if (!expectedState || expectedState !== returnedState) throw new Error('OAuth state validation failed.');
        const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);
        if (!verifier) throw new Error('Missing PKCE verifier.');

        const body = new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: authConfig.client_id,
          code,
          redirect_uri: window.location.origin + HOME_BASE,
          code_verifier: verifier
        });
        const response = await fetch(authConfig.token_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body
        });
        const data = await parseResponse(response);
        logRequest('POST', authConfig.token_url, response.status, response.ok ? { token_received: true } : data);
        if (!response.ok) throw new Error(apiErrorMessage(data, response.status));

        storeTokenSet(data);
        currentMe = principalFromTokens();
        sessionStorage.removeItem(PKCE_VERIFIER_KEY);
        sessionStorage.removeItem(OAUTH_STATE_KEY);
        sessionStorage.removeItem(OAUTH_MODE_KEY);
        sessionStorage.removeItem(SILENT_AUTH_ATTEMPT_KEY);
        window.history.replaceState({}, document.title, HOME_BASE);
        return true;
      }

      async function syncKeycloakSession() {
        const url = new URL(window.location.href);
        if (tokenSet || url.searchParams.has('code') || url.searchParams.has('error')) return false;
        if (sessionStorage.getItem(SILENT_AUTH_ATTEMPT_KEY)) return false;
        sessionStorage.setItem(SILENT_AUTH_ATTEMPT_KEY, '1');
        await beginAuthorization({ prompt: 'none' });
        return true;
      }

      async function refreshAccessToken() {
        if (!tokenSet || !tokenSet.refresh_token || !authConfig.token_url) return null;
        const body = new URLSearchParams({
          grant_type: 'refresh_token',
          client_id: authConfig.client_id,
          refresh_token: tokenSet.refresh_token
        });
        const response = await fetch(authConfig.token_url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body
        });
        const data = await parseResponse(response);
        logRequest('POST', authConfig.token_url, response.status, response.ok ? { token_refreshed: true } : data);
        if (!response.ok) {
          clearTokenSet();
          currentMe = null;
          refreshAuthUi();
          updateIdentityCards();
          updateAdminVisibility();
          showSignInRequired();
          throw new Error(apiErrorMessage(data, response.status));
        }
        storeTokenSet(data);
        currentMe = principalFromTokens();
        refreshAuthUi();
        updateIdentityCards();
        updateAdminVisibility();
        return tokenSet.access_token;
      }

      async function ensureAccessToken() {
        if (authConfig.provider !== 'keycloak') return null;
        if (!tokenSet) return null;
        if (!tokenSet.access_token) return refreshAccessToken();
        if (Date.now() < Number(tokenSet.expires_at || 0) - 30000) return tokenSet.access_token;
        if (!tokenSet.refresh_token) {
          clearTokenSet();
          currentMe = null;
          refreshAuthUi();
          updateIdentityCards();
          updateAdminVisibility();
          return null;
        }
        return refreshAccessToken();
      }

      function logout() {
        const idToken = tokenSet && tokenSet.id_token;
        clearTokenSet();
        currentMe = null;
        refreshAuthUi();
        updateIdentityCards();
        updateAdminVisibility();
        writeOutput('identityOutput', 'Signed out locally.');
        if (authConfig.provider !== 'keycloak' || !authConfig.logout_url) return;
        const params = new URLSearchParams({
          client_id: authConfig.client_id,
          post_logout_redirect_uri: window.location.origin + HOME_BASE
        });
        if (idToken) params.set('id_token_hint', idToken);
        window.location.assign(`${authConfig.logout_url}?${params}`);
      }

      async function loadMe() {
        try {
          currentMe = await request(`${API_BASE}/me`);
          writeOutput('identityOutput', currentMe);
          updateIdentityCards();
          updateAdminVisibility();
          return currentMe;
        } catch (error) {
          currentMe = null;
          writeOutput('identityOutput', error.message);
          updateIdentityCards();
          updateAdminVisibility();
          throw error;
        }
      }

      function updateIdentityCards() {
        const principal = currentMe || (authConfig.provider === 'keycloak' ? principalFromTokens() : null) || (authConfig.provider === 'local' ? {
          sub: $('demoSub').value.trim(),
          email: $('demoEmail').value.trim(),
          name: $('demoName').value.trim(),
          roles: localRoleList()
        } : null);
        const badge = $('identityCardBadge');
        const title = $('identityCardTitle');
        const text = $('identityCardText');
        if (!principal) {
          badge.className = 'status pending';
          badge.textContent = 'Signed out';
          title.textContent = 'No identity loaded';
          text.textContent = 'Sign in or load the current identity to see document ownership.';
          return;
        }
        badge.className = hasAdminRole() ? 'status completed' : 'status ready';
        badge.textContent = hasAdminRole() ? 'Admin identity' : 'User identity';
        title.textContent = principal.name || principal.email || principal.sub || 'Current identity';
        text.textContent = `${principal.sub || 'unknown subject'} with ${activeRoles().length} role(s).`;
      }

      function updateAdminVisibility() {
        const visible = hasAdminRole();
        for (const element of $$('[data-admin-only]')) element.hidden = !visible;
        updateNavigationVisibility();
        renderAdminAccessState();
      }

      function renderAdminAccessState() {
        const state = $('adminAccessState');
        if (!state) return;
        const allowed = hasAdminRole();
        $('loadAdminBtn').disabled = !allowed;
        state.innerHTML = allowed
          ? `<span class='guidance-icon'>A</span><div><h2>Admin access available</h2><p class='hint'>This identity includes <span class='mono'>admin:manage</span>, so admin documents, jobs, and audit events can be loaded.</p></div>`
          : `<span class='guidance-icon'>!</span><div><h2>Admin access unavailable</h2><p class='hint'>The current identity does not include <span class='mono'>admin:manage</span>. Add the role on the Identity page if you are using local demo auth.</p></div>`;
      }

      async function initAuth() {
        try {
          await fetchAuthConfig();
          renderAuthConfig();
          if (authConfig.provider === 'keycloak') {
            await handleAuthCallback();
            if (await syncKeycloakSession()) return;
            if (isSignedIn()) {
              currentMe = principalFromTokens();
              updateIdentityCards();
              updateAdminVisibility();
              await ensureAccessToken().catch((error) => writeOutput('identityOutput', error.message));
            }
          }
          refreshAuthUi();
          if (isSignedIn()) await loadMe();
          else writeOutput('identityOutput', 'Sign in to call protected endpoints.');
        } catch (error) {
          clearTokenSet();
          currentMe = null;
          writeOutput('identityOutput', error.message);
          refreshAuthUi();
          setAuthStatus('Auth error', false);
          updateIdentityCards();
          updateAdminVisibility();
        }
        authReady = true;
        updateAuthPrompt();
        updateAdminVisibility();
        navigateTo(initialPath, { push: false, focus: false });
        await checkHealth();
      }

      async function checkHealth() {
        await Promise.all([
          request('/health', { auth: false }).catch(() => null),
          request('/ready', { auth: false }).catch(() => null)
        ]);
      }

      function setDocumentId(id) {
        selectedDocumentId = id || '';
        for (const fieldId of ['documentId', 'textDocumentId', 'searchDocumentId']) {
          const field = $(fieldId);
          if (field) field.value = selectedDocumentId;
        }
        renderSelectedDocumentSummary();
      }

      function setJobId(id) {
        selectedJobId = id || '';
        const field = $('jobId');
        if (field) field.value = selectedJobId;
      }

      function renderSelectedDocumentSummary() {
        const output = $('selectedDocumentSummary');
        if (!output) return;
        if (!selectedDocumentId) {
          output.className = 'empty-state';
          output.textContent = 'Select a document from the library to enable quick actions.';
          return;
        }
        const doc = documentsCache.find((item) => item.id === selectedDocumentId);
        output.className = 'success-state';
        output.innerHTML = doc
          ? `<h3>${escapeHtml(doc.original_filename)}</h3><p class='hint'>Selected document <span class='mono'>${escapeHtml(shortId(doc.id))}</span> is ready for text, downloads, search, or OCR actions.</p>${statusBadge(doc.status)}`
          : `<h3>Document selected</h3><p class='hint mono'>${escapeHtml(selectedDocumentId)}</p>`;
      }

      async function uploadDocument() {
        setError('uploadError');
        const file = $('uploadFile').files[0];
        if (!file) {
          setError('uploadError', 'Choose a PDF or image before uploading.');
          return;
        }
        await withBusy('uploadBtn', 'Uploading...', async () => {
          const formData = new FormData();
          formData.append('file', file);
          const language = $('languageHint').value.trim();
          if (language) formData.append('language_hint', language);
          try {
            const data = await request(`${API_BASE}/documents`, { method: 'POST', body: formData });
            writeOutput('uploadOutput', data);
            setDocumentId(data.document_id);
            setJobId(data.job_id);
            renderUploadResult(data);
            notify('Upload complete. OCR job created.', 'success');
            documentsLoaded = false;
            await listDocuments();
          } catch (error) {
            setError('uploadError', friendlyUploadError(error.message));
            writeOutput('uploadOutput', error.message);
            notify('Upload failed.', 'error');
          }
        });
      }

      function friendlyUploadError(message) {
        if (/role|permission|forbidden|unauthorized/i.exec(message)) return 'This identity cannot upload or start OCR. Check roles on the Identity page.';
        if (/size|too large/i.exec(message)) return 'The file is too large for the current API settings.';
        if (/type|mime|validation/i.exec(message)) return 'The file type or upload fields were not accepted.';
        return message;
      }

      function renderUploadResult(data) {
        $('uploadResult').className = 'success-state';
        $('uploadResult').innerHTML = `
          <h3>Document uploaded</h3>
          ${renderMetaItems([
            { label: 'Document ID', value: data.document_id, mono: true },
            { label: 'Job ID', value: data.job_id, mono: true }
          ])}
          <div class='actions'>
            <a class='btn secondary' href='/home/jobs' data-navigate='/home/jobs'>Track job</a>
            <a class='btn secondary' href='/home/documents' data-navigate='/home/documents'>View document</a>
          </div>`;
      }

      async function listDocuments() {
        $('documentsStatus').textContent = 'Loading';
        $('documentsOutput').className = '';
        $('documentsOutput').innerHTML = loadingMarkup();
        try {
          const data = await request(`${API_BASE}/documents?limit=50`);
          documentsCache = data.items || [];
          documentsLoaded = true;
          $('documentsStatus').textContent = `${documentsCache.length} shown`;
          renderDocuments(documentsCache);
        } catch (error) {
          documentsLoaded = false;
          $('documentsStatus').textContent = 'Error';
          $('documentsOutput').className = 'error-state';
          $('documentsOutput').textContent = error.message;
        }
      }

      function renderDocuments(items) {
        const output = $('documentsOutput');
        if (!items.length) {
          output.className = 'empty-state';
          output.innerHTML = `<h3>No documents yet</h3><p class='hint'>Upload a PDF or image to create your first searchable document.</p><a class='btn' href='/home/upload' data-navigate='/home/upload'>Upload a document</a>`;
          return;
        }
        output.className = 'document-grid';
        output.innerHTML = items.map((doc) => renderEntityCard('document', `
            ${renderToolbar(
              escapeHtml(doc.original_filename),
              statusBadge(doc.status),
              `<span class='mono'>${escapeHtml(doc.mime_type)} | ${escapeHtml(formatBytes(doc.size_bytes))}</span>`
            )}
            ${renderMetaItems([
              { label: 'Pages', value: doc.page_count ?? '-' },
              { label: 'Created', value: formatDate(doc.created_at) },
              { label: 'Document ID', value: shortId(doc.id), mono: true }
            ])}
            <div class='mini-actions'>
              <button class='secondary' data-doc-action='use' data-id='${escapeHtml(doc.id)}'>Select</button>
              <button class='secondary' data-doc-action='text' data-id='${escapeHtml(doc.id)}'>Read text</button>
              <button class='secondary' data-doc-action='ocr' data-id='${escapeHtml(doc.id)}'>Start OCR</button>
              <button class='secondary' data-doc-action='download' data-id='${escapeHtml(doc.id)}' data-name='${escapeHtml(doc.original_filename)}'>Original</button>
              <button class='secondary' data-doc-action='download-ocr' data-id='${escapeHtml(doc.id)}' data-name='ocr-${escapeHtml(doc.original_filename)}'>OCR file</button>
              <button class='danger' data-doc-action='delete' data-id='${escapeHtml(doc.id)}'>Delete</button>
            </div>
          `, doc.id === selectedDocumentId)).join('');
      }

      async function getText(id = $('textDocumentId').value.trim()) {
        if (!id) {
          writeOutput('textOutput', 'Select or enter a document ID first.');
          return;
        }
        setDocumentId(id);
        try {
          writeOutput('textOutput', 'Loading extracted text...');
          const data = await request(`${API_BASE}/documents/${encodeURIComponent(id)}/text`);
          writeOutput('textOutput', data.text || data);
        } catch (error) {
          writeOutput('textOutput', error.message);
        }
      }

      async function downloadFile(path, fallbackName, outputId = 'textOutput') {
        try {
          const response = await fetch(path, { headers: await authHeaders() });
          if (!response.ok) {
            const data = await parseResponse(response);
            logRequest('GET', path, response.status, data || 'download failed');
            throw new Error(apiErrorMessage(data, response.status));
          }
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = fallbackName || 'download';
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
          logRequest('GET', path, response.status, { downloaded: fallbackName, bytes: blob.size });
          notify('Download started.', 'success');
        } catch (error) {
          writeOutput(outputId, error.message);
          notify('Download failed.', 'error');
        }
      }

      async function deleteDocument(id) {
        if (!id || !confirm(`Delete document ${id}?`)) return;
        try {
          const data = await request(`${API_BASE}/documents/${encodeURIComponent(id)}`, { method: 'DELETE' });
          writeOutput('uploadOutput', data);
          notify('Document deleted.', 'success');
          if (selectedDocumentId === id) setDocumentId('');
          await listDocuments();
        } catch (error) {
          writeOutput('uploadOutput', error.message);
          notify('Delete failed.', 'error');
        }
      }

      async function getJob() {
        const jobId = $('jobId').value.trim();
        if (!jobId) {
          writeOutput('jobOutput', 'Enter a job ID first.');
          return null;
        }
        try {
          const data = await request(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`);
          writeOutput('jobOutput', data);
          setJobId(data.id);
          setDocumentId(data.document_id);
          renderJob(data);
          if (terminalJobStatuses.has(data.status)) stopPolling();
          return data;
        } catch (error) {
          writeOutput('jobOutput', error.message);
          $('jobSummary').className = 'error-state';
          $('jobSummary').textContent = error.message;
          return null;
        }
      }

      function renderJob(job) {
        const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
        $('jobSummary').className = 'success-state';
        $('jobSummary').innerHTML = `
          ${renderToolbar(`Job ${escapeHtml(shortId(job.id))}`, statusBadge(job.status))}
          <div class='progress-shell' aria-label='OCR progress'>
            <div class='progress-bar' style='width: ${progress}%'></div>
          </div>
          ${renderMetaItems([
            { label: 'Progress', value: `${progress}%` },
            { label: 'Attempt', value: `${job.attempt_count} / ${job.max_attempts}` },
            { label: 'Engine', value: job.engine },
            { label: 'Created', value: formatDate(job.created_at) },
            { label: 'Started', value: formatDate(job.started_at) },
            { label: 'Finished', value: formatDate(job.finished_at) }
          ])}
          ${job.error_message ? `<p class='error-text'>${escapeHtml(job.error_code || 'OCR error')}: ${escapeHtml(job.error_message)}</p>` : ''}`;
      }

      async function listJobs() {
        $('jobsOutput').className = '';
        $('jobsOutput').innerHTML = loadingMarkup(2);
        try {
          const data = await request(`${API_BASE}/jobs?limit=50`);
          jobsLoaded = true;
          renderJobs(data.items || []);
        } catch (error) {
          jobsLoaded = false;
          $('jobsOutput').className = 'error-state';
          $('jobsOutput').textContent = error.message;
        }
      }

      function renderJobs(items) {
        const output = $('jobsOutput');
        if (!items.length) {
          output.className = 'empty-state';
          output.textContent = 'No jobs yet. Upload a document or start OCR for a selected document.';
          return;
        }
        output.className = 'job-grid';
        output.innerHTML = items.map((job) => renderEntityCard('job', `
            ${renderToolbar(`<span class='mono'>${escapeHtml(shortId(job.id))}</span>`, statusBadge(job.status))}
            <p class='fine-print'>Document <span class='mono'>${escapeHtml(shortId(job.document_id))}</span> | ${escapeHtml(job.progress)}% | updated ${escapeHtml(formatDate(job.updated_at))}</p>
            <div class='mini-actions'>
              <button class='secondary' data-job-action='use' data-id='${escapeHtml(job.id)}' data-document-id='${escapeHtml(job.document_id)}'>Use job</button>
            </div>
          `)).join('');
      }

      function togglePolling() {
        if (pollTimer) {
          stopPolling();
          return;
        }
        getJob();
        pollTimer = setInterval(getJob, 2000);
        $('pollJobBtn').textContent = 'Stop polling';
        $('pollState').textContent = 'Polling every 2s';
      }

      function stopPolling() {
        if (!pollTimer) return;
        clearInterval(pollTimer);
        pollTimer = null;
        $('pollJobBtn').textContent = 'Start polling';
        $('pollState').textContent = 'Polling off';
      }

      async function startOcrForDocument(id = $('documentId').value.trim()) {
        if (!id) {
          writeOutput('jobOutput', 'Enter or select a document ID first.');
          return;
        }
        try {
          const data = await request(`${API_BASE}/documents/${encodeURIComponent(id)}/ocr`, { method: 'POST' });
          writeOutput('jobOutput', data);
          setDocumentId(data.document_id);
          setJobId(data.id);
          renderJob(data);
          jobsLoaded = false;
          notify('OCR job started.', 'success');
        } catch (error) {
          writeOutput('jobOutput', error.message);
          notify('Could not start OCR.', 'error');
        }
      }

      async function retryJob() {
        const jobId = $('jobId').value.trim();
        if (!jobId) {
          writeOutput('jobOutput', 'Enter a job ID first.');
          return;
        }
        try {
          const data = await request(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/retry`, { method: 'POST' });
          writeOutput('jobOutput', data);
          renderJob(data);
          notify('Job retry requested.', 'success');
        } catch (error) {
          writeOutput('jobOutput', error.message);
          notify('Retry failed.', 'error');
        }
      }

      async function cancelJob() {
        const jobId = $('jobId').value.trim();
        if (!jobId) {
          writeOutput('jobOutput', 'Enter a job ID first.');
          return;
        }
        try {
          const data = await request(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/cancel`, { method: 'POST' });
          writeOutput('jobOutput', data);
          renderJob(data);
          stopPolling();
          notify('Job cancelled.', 'success');
        } catch (error) {
          writeOutput('jobOutput', error.message);
          notify('Cancel failed.', 'error');
        }
      }

      function syncSearchScope() {
        $('searchDocumentField').hidden = $('searchScope').value !== 'selected';
      }

      async function searchDocuments() {
        const query = $('searchQuery').value.trim();
        const scoped = $('searchScope').value === 'selected';
        const documentId = $('searchDocumentId').value.trim();
        if (!query) {
          $('searchResults').className = 'error-state';
          $('searchResults').textContent = 'Enter a search query first.';
          return;
        }
        if (scoped && !documentId) {
          $('searchResults').className = 'error-state';
          $('searchResults').textContent = 'Select or enter a document ID for scoped search.';
          return;
        }
        const path = scoped
          ? `${API_BASE}/documents/${encodeURIComponent(documentId)}/search?q=${encodeURIComponent(query)}`
          : `${API_BASE}/search?q=${encodeURIComponent(query)}`;
        $('searchStatus').textContent = 'Searching';
        $('searchResults').className = '';
        $('searchResults').innerHTML = loadingMarkup(2);
        try {
          const data = await request(path);
          writeOutput('searchOutput', data);
          $('searchStatus').textContent = `${data.total ?? data.items?.length ?? 0} result(s)`;
          renderSearchResults(data.items || []);
        } catch (error) {
          $('searchStatus').textContent = 'Error';
          $('searchResults').className = 'error-state';
          $('searchResults').textContent = error.message;
          writeOutput('searchOutput', error.message);
        }
      }

      function renderSearchResults(items) {
        const output = $('searchResults');
        if (!items.length) {
          output.className = 'empty-state';
          output.innerHTML = '<h3>No matches yet</h3><p class="hint">Only processed documents are searchable. Try another phrase or check that OCR completed.</p>';
          return;
        }
        output.className = 'search-grid';
        output.innerHTML = items.map((hit) => renderEntityCard('search', `
            ${renderToolbar(escapeHtml(hit.document_filename), statusBadge(hit.status))}
            <p class='fine-print'>Page ${escapeHtml(hit.page_number)} | Document <span class='mono'>${escapeHtml(shortId(hit.document_id))}</span></p>
            <p>${escapeHtml(hit.snippet || hit.matched_text || '')}</p>
            <div class='mini-actions'>
              <button class='secondary' data-search-action='text' data-id='${escapeHtml(hit.document_id)}'>Open text</button>
            </div>
          `)).join('');
      }

      async function loadAdminData() {
        renderAdminAccessState();
        if (!hasAdminRole()) {
          $('adminOutput').className = 'error-state';
          $('adminOutput').textContent = 'Admin access is unavailable for this identity.';
          return;
        }
        await withBusy('loadAdminBtn', 'Loading...', async () => {
          $('adminOutput').className = '';
          $('adminOutput').innerHTML = loadingMarkup(3);
          try {
            const [documents, jobs, auditEvents] = await Promise.all([
              request(`${API_BASE}/admin/documents?limit=20`),
              request(`${API_BASE}/admin/jobs?limit=20`),
              request(`${API_BASE}/admin/audit-events?limit=20`)
            ]);
            renderAdminData(documents.items || [], jobs.items || [], auditEvents.items || []);
          } catch (error) {
            $('adminOutput').className = 'error-state';
            $('adminOutput').textContent = error.message;
          }
        });
      }

      function renderAdminData(documents, jobs, auditEvents) {
        $('adminOutput').className = 'admin-grid';
        $('adminOutput').innerHTML = `
          <section class='admin-card'>
            <h3>Admin documents (${documents.length})</h3>
            ${renderSimpleTable(documents, ['id', 'owner_sub', 'original_filename', 'status', 'created_at'])}
          </section>
          <section class='admin-card'>
            <h3>Admin jobs (${jobs.length})</h3>
            ${renderSimpleTable(jobs, ['id', 'document_id', 'status', 'progress', 'updated_at'])}
          </section>
          <section class='admin-card'>
            <h3>Audit events (${auditEvents.length})</h3>
            ${renderSimpleTable(auditEvents, ['id', 'actor_sub', 'action', 'resource_type', 'created_at'])}
          </section>`;
      }

      function renderSimpleTable(items, keys) {
        if (!items.length) return `<p class='hint'>No records returned.</p>`;
        return `
          <div class='table-wrap'>
            <table>
              <thead><tr>${keys.map((key) => `<th>${escapeHtml(key)}</th>`).join('')}</tr></thead>
              <tbody>
                ${items.map((item) => `<tr>${keys.map((key) => `<td>${escapeHtml(key.endsWith('_at') ? formatDate(item[key]) : item[key] ?? '-')}</td>`).join('')}</tr>`).join('')}
              </tbody>
            </table>
          </div>`;
      }

      function setupDropZone() {
        const dropZone = $('dropZone');
        const fileInput = $('uploadFile');
        fileInput.addEventListener('change', () => {
          const file = fileInput.files[0];
          $('uploadFileName').textContent = file ? `${file.name} (${formatBytes(file.size)})` : 'No file selected yet.';
        });
        for (const eventName of ['dragenter', 'dragover']) {
          dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add('drag-over');
          });
        }
        for (const eventName of ['dragleave', 'drop']) {
          dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'));
        }
        dropZone.addEventListener('drop', (event) => {
          event.preventDefault();
          if (!event.dataTransfer.files.length) return;
          fileInput.files = event.dataTransfer.files;
          fileInput.dispatchEvent(new Event('change'));
        });
      }

      function bindEvents() {
        for (const id of ['topLoginBtn', 'authPromptLoginBtn', 'loginBtn']) {
          const button = $(id);
          if (button) button.addEventListener('click', startLogin);
        }
        $('logoutBtn').addEventListener('click', logout);
        $('saveIdentityBtn').addEventListener('click', saveIdentity);
        $('meBtn').addEventListener('click', () => loadMe().catch((error) => notify(error.message, 'error')));
        $('healthBtn').addEventListener('click', checkHealth);
        $('clearLogBtn').addEventListener('click', () => writeOutput('apiLog', 'No requests yet.'));
        $('uploadBtn').addEventListener('click', uploadDocument);
        $('refreshDocsBtn').addEventListener('click', listDocuments);
        $('listDocsBtn').addEventListener('click', listDocuments);
        $('getTextBtn').addEventListener('click', () => getText());
        $('downloadOriginalBtn').addEventListener('click', () => {
          const id = $('textDocumentId').value.trim();
          if (id) downloadFile(`${API_BASE}/documents/${encodeURIComponent(id)}/download`, `${id}-original`);
        });
        $('downloadOcrBtn').addEventListener('click', () => {
          const id = $('textDocumentId').value.trim();
          if (id) downloadFile(`${API_BASE}/documents/${encodeURIComponent(id)}/ocr-download`, `${id}-ocr`);
        });
        $('listJobsBtn').addEventListener('click', listJobs);
        $('getJobBtn').addEventListener('click', getJob);
        $('pollJobBtn').addEventListener('click', togglePolling);
        $('startOcrBtn').addEventListener('click', () => startOcrForDocument());
        $('retryJobBtn').addEventListener('click', retryJob);
        $('cancelJobBtn').addEventListener('click', cancelJob);
        $('searchScope').addEventListener('change', syncSearchScope);
        $('searchBtn').addEventListener('click', searchDocuments);
        $('searchQuery').addEventListener('keydown', (event) => {
          if (event.key === 'Enter') searchDocuments();
        });
        $('loadAdminBtn').addEventListener('click', loadAdminData);
        for (const key of identityKeys) {
          $(key).addEventListener('input', () => {
            if (authConfig.provider === 'local') {
              currentMe = null;
              updateIdentityCards();
              updateAdminVisibility();
            }
          });
        }
        $('documentsOutput').addEventListener('click', handleDocumentAction);
        $('jobsOutput').addEventListener('click', handleJobAction);
        $('searchResults').addEventListener('click', handleSearchAction);
      }

      function handleDocumentAction(event) {
        const button = event.target instanceof Element ? event.target.closest('button[data-doc-action]') : null;
        if (!button) return;
        const id = button.dataset.id;
        const name = button.dataset.name;
        if (button.dataset.docAction === 'use') setDocumentId(id);
        if (button.dataset.docAction === 'text') {
          setDocumentId(id);
          getText(id);
        }
        if (button.dataset.docAction === 'ocr') startOcrForDocument(id);
        if (button.dataset.docAction === 'download') downloadFile(`${API_BASE}/documents/${encodeURIComponent(id)}/download`, name || `${id}-original`);
        if (button.dataset.docAction === 'download-ocr') downloadFile(`${API_BASE}/documents/${encodeURIComponent(id)}/ocr-download`, name || `${id}-ocr`);
        if (button.dataset.docAction === 'delete') deleteDocument(id);
      }

      function handleJobAction(event) {
        const button = event.target instanceof Element ? event.target.closest('button[data-job-action]') : null;
        if (!button) return;
        setJobId(button.dataset.id);
        setDocumentId(button.dataset.documentId);
        getJob();
      }

      function handleSearchAction(event) {
        const button = event.target instanceof Element ? event.target.closest('button[data-search-action]') : null;
        if (!button) return;
        setDocumentId(button.dataset.id);
        navigateTo('/home/documents');
        getText(button.dataset.id);
      }

      async function bootHomeUi() {
        await loadUiFragments();
        loadIdentity();
        setupNavigation();
        setupTooltips();
        setupDropZone();
        bindEvents();
        syncSearchScope();
        updateIdentityCards();
        updateAdminVisibility();
        navigateTo(isPublicRoute(resolveRoute(initialPath).path) ? initialPath : HOME_BASE, { push: false, focus: false });
        initAuth().then(() => {
          if (!routeLoaded) navigateTo(initialPath, { push: false, focus: false });
        });
      }

      bootHomeUi().catch((error) => {
        const root = document.getElementById('uiShellRoot');
        if (root) root.innerHTML = `<main class='shell'><section class='error-state'>${error.message}</section></main>`;
      });
