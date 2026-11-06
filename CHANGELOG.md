# Changelog

All notable project updates are recorded here. Entries describe repository changes and distinguish implemented work from validation that has actually been run.

## [Unreleased]

### Changed
- Use the supplied 6×5 gameplay video as the reference for the board layout.
- Document the 4×3 and 5×4 variants as sharing the same overall board region, with larger cards as the grid contains fewer rows and columns.
- Scale the solver's result tiles according to the detected column count so the displayed board keeps a consistent overall width: 4×3 largest, 5×4 intermediate, and 6×5 smallest.

### Validation
- Not yet run in this update. Windows gameplay calibration against the reference video remains outstanding.
