# Changelog

All notable project updates are recorded here. Entries describe repository changes and distinguish implemented work from validation that has actually been run.

## [Unreleased]

### Changed
- Set the [user-provided 6×5 gameplay video](https://www.youtube.com/watch?v=xqS7pS4uSZE) as the canonical visual reference for the Match Cards board.
- Document the expected 4×3 and 5×4 layouts as using the same overall board area, with larger cards as the grid contains fewer rows and columns.
- Keep the result view's card sizing proportional to the detected column count: 4×3 largest, 5×4 intermediate, and 6×5 smallest.

### Validation
- Documentation updated; no automated tests or live Windows gameplay calibration were run for this documentation-only change.
- Validate the board bounds, card spacing, and card dimensions against captures from all three modes before treating the layout assumptions as confirmed.
