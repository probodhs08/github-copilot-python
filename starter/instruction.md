## Project Standards

- Write readable Python with focused, modular functions and meaningful names.
- Add type hints where they improve clarity; handle expected errors with useful messages.
- Keep changes maintainable and narrowly scoped. Preserve working APIs and Sudoku behavior unless a requirement calls for a change.
- Keep dependencies minimal; prefer the standard library and existing project tools.
- Cover behavior changes with focused tests. Run `python -m pytest` from `starter/` before considering a change complete.
- Build responsive interfaces with semantic HTML, keyboard support, visible focus, accessible names, and sufficient contrast in light and dark themes.
- Do not rely on color alone for status or errors; provide text or accessible state.
- Treat browser storage as public, user-controlled data. Store only required preferences and leaderboard metadata; never store puzzle solutions, secrets, or trusted game state there.
- Preserve existing files and screenshots unless the task explicitly requires changing them. Do not commit or push changes unless asked.
