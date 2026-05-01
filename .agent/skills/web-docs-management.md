# Skill: Web Documentation Management

## Description

This skill defines the strict rules and procedures for maintaining and updating the official documentation website located in the `docs/` directory. It ensures that any changes to the content preserve the premium aesthetic, structural integrity, and interactive features of the site.

---

## 🚫 INVIOLABLE RULES (CRITICAL)

1.  **NO CSS/JS ALTERATIONS**: You are strictly forbidden from modifying `docs/assets/css/main.css` or `docs/assets/js/main.js` unless explicitly instructed by a HUMAN to change the design system.
2.  **NO STRUCTURAL BREAKAGE**: Do not remove or rename the `container`, `docs-layout`, `sidebar`, or `content-section` classes. These are core to the layout.
3.  **TEMPLATE ADHERENCE**: All new pages MUST follow the exact HTML structure of `docs/pages/introduction.html`.
4.  **LINK INTEGRITY**: Before committing, verify that all relative paths (e.g., `../assets/css/main.css`) are correct for the file's depth.
5.  **NO PLACEHOLDERS**: Never use "To be added" or "Coming soon". If the information is not ready, do not create the page.

---

## Content Update Procedure

### 1. Modifying Existing Pages
- Use `replace_file_content` or `multi_replace_file_content`.
- Only modify the content inside the `<section class="content-section">` tag.
- Preserve all existing headings (`h1`, `h2`, `h3`) unless the information they categorize has fundamentally changed.
- Maintain the syntax highlighting colors in `<pre><code>` blocks.

### 2. Adding New Pages
- Copy `docs/pages/introduction.html` as a template.
- Update the `<title>` tag.
- Update the `active` class in the `<nav class="nav-links">` and the `.sidebar-nav`.
- Add the new page link to the sidebar of **ALL** existing pages to maintain navigation consistency.

### 3. Updating the Sidebar
- If a new section or page is added, the sidebar in `docs/index.html` (if applicable) and ALL files in `docs/pages/` must be synchronized.
- Ensure the `href` paths are correct:
    - In `index.html`: `pages/filename.html`
    - In `pages/*.html`: `filename.html`

---

## UI/UX Standards

- **Typography**: Use `<strong>` for emphasis and `<code class="inline-code">` for technical terms.
- **Lists**: Use standard `<ul>` with `<li>`. For "check" style lists, use the inline style: `<span style="color: var(--primary); font-weight: bold;">✓</span>`.
- **Code Blocks**: Always wrap code in `<pre><code>` and use the project's color palette for manual highlighting if needed.
- **Callouts**: For important notes, use:
    ```html
    <div style="background: rgba(99, 102, 241, 0.1); padding: 1.5rem; border-left: 4px solid var(--primary); border-radius: 8px; margin-bottom: 2rem;">
        <strong>Title:</strong> Description
    </div>
    ```

---

## Verification Checklist (Mandatory before Commit)

- [ ] Does the page look "premium" and follow the dark mode theme?
- [ ] Are all relative links (`../assets/...`) functional?
- [ ] Is the `active` class correctly assigned in the navigation?
- [ ] Did I avoid modifying `main.css` or `main.js`?
- [ ] Is the new content accurate according to the latest v0.9.0 changes?
