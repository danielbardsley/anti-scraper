# DESIGN.md — Base-Path Awareness

## Overview
The current `proof-of-work` demo assumes root hosting.
That is visible in:
- root-relative static asset references in HTML
- root-relative API calls in browser JS
- backend routes mounted directly at `/`

To support reverse-proxy or Funnel publication under `/proof-of-work`, the application must become base-path aware.

## Proposed configuration
Add an application setting such as:

- `POW_BASE_PATH`

Examples:
- `""` → root mode
- `"/proof-of-work"` → subpath mode

Normalization rules:
- must be empty or start with `/`
- should not end with `/` unless it is exactly `/`
- internally normalize `/` to empty string

## Backend design

### Route mounting strategy
Two acceptable implementation patterns:

#### Option A — prefix all routes and mounts
Apply the base path directly when mounting:
- static files mounted at `<basePath>/static`
- routes registered at `<basePath>/...`

#### Option B — sub-application mount
Create an inner FastAPI app and mount it under the configured base path on an outer app.

Preferred option:
- **sub-application mount**, because it keeps route definitions readable and local development clean.

Example shape:
- outer app handles optional mounting
- inner app contains current routes like `/`, `/healthz`, `/v1/...`, `/static/...`
- outer app mounts inner app at `/proof-of-work` when configured

## Frontend design

### Asset path strategy
The HTML must not hardcode `/static/...` when deployed under a subpath.

Preferred options:
- inject a `<base>` tag into HTML
- or template/replace a `__BASE_PATH__` placeholder into asset URLs

Safer preferred option:
- explicit base-path variable injection, because `<base>` can have side effects.

### API path strategy
The frontend JS should use a single helper to compose URLs:

```js
buildAppUrl("/v1/config")
```

Where `buildAppUrl` prepends the configured base path.

### Base-path source for frontend
Recommended approach:
- inject the base path into the page as a global variable, dataset attribute, or config field
- also expose it from `/v1/config` for debugging/visibility

Suggested HTML approach:

```html
<script>
  window.APP_BASE_PATH = "/proof-of-work";
</script>
```

## Cookie/session considerations
The session cookie path should be considered carefully.

Current behavior likely uses path `/`.
That may still be acceptable, but if isolation is preferred the cookie path may be set to the effective base path.

Design choice to evaluate during implementation:
- keep cookie path `/` for simplicity and compatibility
- or scope it to `<basePath>/`

The spec does not require stricter cookie scoping, but the decision should be explicit.

## Testing strategy

### Backend/API tests
Add tests for:
- root mode routes
- subpath mode routes
- static asset delivery under subpath
- config reporting base path

### UI contract tests
Verify that returned HTML/JS references the configured base path correctly.

### Browser-flow tests
At minimum ensure that:
- challenge fetch path is correct under subpath
- proof submit path is correct under subpath

## Docs changes
README should include:
- what base-path hosting is for
- how to set `POW_BASE_PATH`
- example local subpath deployment
- example Tailscale Serve/Funnel mapping

## Risks
- missing one root-relative frontend path breaks the app under subpath
- cookie behavior may be surprising if path scoping changes
- static asset references can silently regress without tests
