# Wasabi theme maintenance notes

This directory is a vendored Hermit base theme and retains the upstream MIT license.

The live site intentionally owns its product-specific templates, CSS, and JavaScript in the repository root:

- `layouts/` contains the active page and partial overrides.
- `assets/css/custom.css` contains site-specific components.
- `assets/js/main.js` contains the active accessible navigation and article controls.

Treat updates to `themes/hermit/` as a manual vendor update: review the upstream diff, preserve the root overrides, run `make check`, and preview locally before merging. Do not copy generated `resources/_gen/` files back into Git.
