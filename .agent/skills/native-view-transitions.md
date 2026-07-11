# Native View Transitions Skill

Use this skill when adding or reviewing page navigation animations in the no-build browser UI.

## Goal

Use browser-native transitions to make navbar navigation feel smooth while keeping the UI accessible, lightweight, and dependency-free.

## Preferred API

Use `document.startViewTransition()` for same-document route changes when supported.

Pattern:

```js
function runRouteTransition(updateView) {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion || !document.startViewTransition) {
    updateView();
    return;
  }
  document.startViewTransition(updateView);
}
```

Use the History API for route navigation:

```js
function navigateTo(path) {
  if (window.location.pathname === path) return;
  window.history.pushState({}, "", path);
  runRouteTransition(() => renderRoute(path));
}
```

## CSS Guidance

Keep transitions subtle:

```css
::view-transition-old(root) {
  animation: page-out 160ms ease both;
}

::view-transition-new(root) {
  animation: page-in 220ms ease both;
}

@keyframes page-out {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(6px); }
}

@keyframes page-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Route Animation Rules

- Animate changes between navbar sections.
- Do not animate every small API response update with a full page transition.
- Do not trap focus during transitions.
- After rendering a new route, move focus to the page heading.
- Keep animation durations short, generally under 250ms.
- Avoid large motion, rotation, or flashing effects.
- Avoid transition names on many dynamic table rows unless there is a clear need.

## Fallback Rules

- If `document.startViewTransition` is missing, update the route immediately.
- CSS fallback may use a small `.is-entering` class with opacity/translate.
- If reduced motion is requested, skip transform animations.

## Not-Found Navigation

Unknown `/home/*` paths should render a not-found page inside the app shell. The not-found page should provide:

| Element | Requirement |
| --- | --- |
| Heading | Clear "Page not found" message. |
| Explanation | State that the section does not exist. |
| Action | Link or button back to `/home`. |
| Optional action | Link to `/home/upload` or `/home/documents`. |

## Verification Checklist

- Navigation is smooth in browsers with View Transition API support.
- Navigation still works when View Transition API is unavailable.
- `prefers-reduced-motion: reduce` disables meaningful motion.
- Browser back and forward buttons render the correct section.
- Refreshing a nested `/home/*` path loads the app shell and correct section.
