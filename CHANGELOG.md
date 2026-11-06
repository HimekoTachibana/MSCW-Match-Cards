# Changelog

All notable project updates are recorded here. Entries describe repository changes and distinguish implemented work from validation that has actually been run.

## [Unreleased]\n\n### Added\n- Add a PyInstaller spec and GitHub Actions workflow to build standalone Windows x64 and Linux x64 test archives and publish them as GitHub prereleases.\n- Add Linux/X11 window discovery through `wmctrl` and ordinary screen capture.\n\n### Changed\n- Document Linux runtime dependencies and distro baseline (glibc 2.35+), including Debian 12/13, Fedora/Bazzite, and Arch/CachyOS families.\n\n### Limitations\n- Linux Wayland sessions are not supported by the current window discovery/capture implementation; use an X11 session.\n- Build and runtime validation will be reported from the actual CI run; compatibility across every distro is not yet verified.\n

### Changed
- Set the [user-provided 6×5 gameplay video](https://www.youtube.com/watch?v=xqS7pS4uSZE) as the canonical visual reference for the Match Cards board.
- Document the expected 4×3 and 5×4 layouts as using the same overall board area, with larger cards as the grid contains fewer rows and columns.
- Keep the result view's card sizing proportional to the detected column count: 4×3 largest, 5×4 intermediate, and 6×5 smallest.

### Validation
- Documentation updated; no automated tests or live Windows gameplay calibration were run for this documentation-only change.
- Validate the board bounds, card spacing, and card dimensions against captures from all three modes before treating the layout assumptions as confirmed.
