const UI_SHELL_PATH = '/ui/components/app-shell.html';
const UI_SECTION_PATHS = [
  '/ui/sections/home.html',
  '/ui/sections/upload.html',
  '/ui/sections/documents.html',
  '/ui/sections/jobs.html',
  '/ui/sections/search.html',
  '/ui/sections/identity.html',
  '/ui/sections/admin.html',
  '/ui/sections/help.html',
  '/ui/sections/not-found.html',
  '/ui/sections/logs.html'
];

async function fetchUiFragment(path) {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`Could not load UI fragment ${path}`);
  return response.text();
}

async function loadUiFragments() {
  const root = document.getElementById('uiShellRoot');
  if (!root) throw new Error('Missing UI shell root.');

  const [shell, ...sections] = await Promise.all([
    fetchUiFragment(UI_SHELL_PATH),
    ...UI_SECTION_PATHS.map(fetchUiFragment)
  ]);

  root.innerHTML = shell;
  const main = document.getElementById('appMain');
  if (!main) throw new Error('Missing app main region.');
  main.innerHTML = sections.join('\n');
}
