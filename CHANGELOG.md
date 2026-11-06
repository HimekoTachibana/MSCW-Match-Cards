# Changelog

All notable project updates are recorded here. Entries describe repository changes and distinguish implemented work from validation that has actually been run.

## [Unreleased]

### Added
- Add a PyInstaller spec and GitHub Actions workflow to build standalone Windows x64 and Linux x64 test archives and publish them as GitHub prereleases.
- Add Linux/X11 game-window discovery through `wmctrl` and ordinary screen capture.

### Changed
- Document Linux runtime dependencies and the glibc 2.35+ build baseline for Debian 12/13, Fedora/Bazzite, and Arch/CachyOS families.

### Limitations
- Linux Wayland sessions are not supported by the current window discovery/capture implementation; use an X11 session.
- Compatibility across every listed distribution and live gameplay capture have not yet been verified.

### Validation
- GitHub Actions build and unit-test results are pending for this update.
