# Release checklist

Run by the `devops` subagent in `/build-tool` Stage 7, before anything is
published. Record a result (pass / fail / accepted-with-reason) for every item in
the release notes. Security signs off on the results. The human approves the
publish.

## 1. Source
- [ ] All slices for this release are merged to `main`; no open PRs in scope.
- [ ] Building from a **clean checkout** of `main` (not a working tree with local
      changes).
- [ ] `design/` and `docs/` match what shipped (no stale specs).

## 2. Quality
- [ ] Type-check passes.
- [ ] All tests pass.
- [ ] Production build succeeds with no warnings you haven't explained.
- [ ] Preview checked: key screens load, no console errors, light/dark and
      phone-width views work (if applicable).

## 3. Dependencies
- [ ] Package audit run (e.g. `npm audit`).
- [ ] No high/critical advisory in **shipped** (runtime) dependencies.
- [ ] Dev-only advisories either fixed or listed as accepted, with the reason.
- [ ] Versions pinned via the lockfile.

## 4. Security
- [ ] No secrets in the repo, build output, or client bundle.
- [ ] Content-Security-Policy set for the host, allowing only what the app loads.
- [ ] Standard headers set: HSTS (if HTTPS), `X-Content-Type-Options: nosniff`,
      `Referrer-Policy`, frame protections.
- [ ] `security-engineer` has signed off on this list.

## 5. Accessibility and SEO (web apps)
- [ ] Core flows usable by keyboard; contrast meets WCAG 2.2 AA.
- [ ] Images have correct `alt` (decorative images use `alt=""`).
- [ ] Title, description, canonical URL, social preview, `robots.txt`, sitemap.

## 6. Deploy
- [ ] Human's explicit publish approval recorded (who, when).
- [ ] Deployed from the clean `main` build.
- [ ] Smoke test on the live URL passes.
- [ ] Rollback path known and tested (previous build or revert).

## 7. After
- [ ] Release notes posted: commit/version, what shipped, results of this list,
      live URL, approval record.
- [ ] Follow-ups filed as tasks.
