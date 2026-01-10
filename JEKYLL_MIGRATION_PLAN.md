# 🏗️ Jekyll Migration & Site Restructure Plan

We are converting the static site to Jekyll to centralize layout logic, fix navigation, and integrate Google Analytics.

## 📦 Phase 1: Scaffolding & Assets
*Goal: Create the Jekyll structure and move static assets to their new home.*

- [ ] **Initialize Directories:** Create the following folders if they don't exist:
    - `_layouts`
    - `_includes`
    - `_posts`
    - `assets/css`
    - `assets/js`
    - `tools`
- [ ] **Create Config:** Create `_config.yml` with:
    ```yaml
    title: CPH50 Control
    description: "Charger automation and telemetry"
    baseurl: "/cph50-control" # or "" depending on custom domain
    url: "https://scerruti.github.io"
    theme: null
    ```
- [ ] **Migrate JS:** Move `dashboard.js` to `assets/js/dashboard.js`.
- [ ] **Migrate CSS:** Move any inline/external styles to `assets/css/main.css`.

## 🧩 Phase 2: Layouts & Components
*Goal: Create the "Single Source of Truth" for navigation and analytics.*

- [ ] **Create Analytics Include:** Create `_includes/analytics.html`.
    - *Action:* Paste the Google Analytics (GA4) snippet here.
- [ ] **Create Navigation Include:** Create `_includes/nav.html`.
    - *Content:*
    ```html
    <nav>
      <a href="{{ '/' | relative_url }}">⚡ Status</a>
      <a href="{{ '/history/' | relative_url }}">📊 History</a>
      <a href="{{ '/tools/label/' | relative_url }}">🏷️ Labeling</a>
      <a href="{{ '/blog/' | relative_url }}">📝 Blog</a>
    </nav>
    ```
- [ ] **Create Default Layout:** Create `_layouts/default.html`.
    - *Structure:* Standard HTML5 boilerplate that injects `{% include analytics.html %}` in the `<head>` and `{% include nav.html %}` at the top of the `<body>`.

## 🔄 Phase 3: Page Restructuring
*Goal: Move pages to their new "User-Centric" locations using Front Matter.*

- [ ] **Migrate Live Dashboard (New Root):**
    - *Source:* `dashboard.html`
    - *Dest:* `index.html`
    - *Front Matter:*
    ```yaml
    ---
    layout: default
    title: Live Status
    permalink: /
    ---
    ```
    - *Note:* Ensure the `<script>` tag now points to `/assets/js/dashboard.js`.

- [ ] **Migrate Analytics (New History):**
    - *Source:* `index.html` (the old root)
    - *Dest:* `history.html`
    - *Front Matter:*
    ```yaml
    ---
    layout: default
    title: Charging History
    permalink: /history/
    ---
    ```

- [ ] **Migrate Labeling Tool:**
    - *Source:* `label-simple.html`
    - *Dest:* `tools/label.html`
    - *Front Matter:* `layout: default`, `title: Labeling Tool`

## 📝 Phase 4: Blog Migration
*Goal: Move blog posts to the `_posts` collection.*

- [ ] **Migrate Posts:** Move all files from `blog/posts/*.html` to `_posts/`.
    - *Naming:* Rename to `YYYY-MM-DD-slug.md` (e.g., `2026-01-09-the-6am-problem.md`).
    - *Front Matter:* Add `layout: post` and `title` to each.
- [ ] **Create Blog Index:** Create `blog/index.html`.
    - *Logic:* Use a Liquid `{% for post in site.posts %}` loop to list the articles.

## ✅ Phase 5: Verification
- [ ] Run `jekyll serve` locally.
- [ ] Verify the "Live Status" is now the homepage.
- [ ] Verify the Navigation Bar appears on every page.
- [ ] Verify Google Analytics tag appears in the source code of every page.
