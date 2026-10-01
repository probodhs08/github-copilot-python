// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_KEY = 'sudoku-top-10';
const THEME_KEY = 'sudoku-theme';
const VALID_DIFFICULTIES = ['Easy', 'Medium', 'Hard', 'Custom'];
let puzzle = [];
let currentDifficulty = 'medium';
let hintsUsed = 0;
let gameCompleted = false;
let boardWasFull = false;
let completionCheckPending = false;
let timerStartedAt = null;
let elapsedTimeMs = 0;
let timerInterval = null;
let completionMetadata = null;
let scoreSubmitted = false;

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        e.target.classList.remove('incorrect', 'missing');
        e.target.removeAttribute('aria-invalid');
        e.target.setAttribute(
          'aria-label',
          `Row ${i + 1}, column ${j + 1}, editable cell`
        );
        checkForAutomaticCompletion();
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className = 'sudoku-cell prefilled';
        inp.title = 'Prefilled clue';
        inp.setAttribute(
          'aria-label',
          `Row ${i + 1}, column ${j + 1}, prefilled clue ${val}, locked`
        );
      } else {
        inp.value = '';
        inp.disabled = false;
        inp.className = 'sudoku-cell';
        inp.removeAttribute('title');
        inp.setAttribute('aria-label', `Row ${i + 1}, column ${j + 1}, editable cell`);
      }
    }
  }
}

function formatElapsedTime(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimerDisplay() {
  const elapsed = timerStartedAt === null
    ? elapsedTimeMs
    : performance.now() - timerStartedAt;
  document.getElementById('timer').textContent = formatElapsedTime(elapsed);
}

function resetTimer() {
  if (timerInterval !== null) clearInterval(timerInterval);
  timerInterval = null;
  timerStartedAt = null;
  elapsedTimeMs = 0;
  updateTimerDisplay();
}

function startTimer(difficulty) {
  resetTimer();
  currentDifficulty = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
  timerStartedAt = performance.now();
  timerInterval = setInterval(updateTimerDisplay, 250);
}

function stopTimer() {
  if (timerStartedAt !== null) {
    elapsedTimeMs = Math.floor(performance.now() - timerStartedAt);
    timerStartedAt = null;
  }
  if (timerInterval !== null) clearInterval(timerInterval);
  timerInterval = null;
  updateTimerDisplay();
}

function readCurrentBoard() {
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = [];
  for (let row = 0; row < SIZE; row++) {
    board[row] = [];
    for (let col = 0; col < SIZE; col++) {
      const value = inputs[row * SIZE + col].value;
      board[row][col] = value ? parseInt(value, 10) : 0;
    }
  }
  return board;
}

function isBoardFull(board) {
  return board.every(row => row.every(value => value !== 0));
}

function setMessage(text, state = 'error') {
  const message = document.getElementById('message');
  message.dataset.state = state;
  message.textContent = text;
}

function checkForAutomaticCompletion() {
  if (gameCompleted) return;

  const isFull = isBoardFull(readCurrentBoard());
  if (!isFull) {
    boardWasFull = false;
    return;
  }
  if (!boardWasFull) {
    boardWasFull = true;
    return checkSolution(true);
  }
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  resetTimer();
  gameCompleted = false;
  boardWasFull = false;
  completionCheckPending = false;
  completionMetadata = null;
  window.completionMetadata = null;
  hintsUsed = 0;
  scoreSubmitted = false;
  document.getElementById('score-entry').hidden = true;
  document.getElementById('player-name').value = '';
  document.getElementById('score-error').textContent = '';
  document.getElementById('check-solution').disabled = false;
  document.getElementById('hint').disabled = false;
  document.getElementById('hints-used').innerText = 'Hints used: 0';

  try {
    const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Unable to start a new game.');

    renderPuzzle(data.puzzle);
    startTimer(difficulty);
    document.getElementById('message').innerText = '';
    checkForAutomaticCompletion();
  } catch (error) {
    setMessage(error.message);
  }
}

async function useHint() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = readCurrentBoard();

  const hintButton = document.getElementById('hint');
  const editableInputs = Array.from(inputs).filter(input => !input.disabled);
  hintButton.disabled = true;
  editableInputs.forEach(input => { input.disabled = true; });
  try {
    const res = await fetch('/hint', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board})
    });
    const data = await res.json();
    if (data.error) {
      setMessage(data.error);
      return;
    }

    const index = data.row * SIZE + data.col;
    const hintedInput = inputs[index];
    hintedInput.value = data.value;
    hintedInput.disabled = true;
    hintedInput.className = 'sudoku-cell hinted';
    hintedInput.title = 'Hinted cell';
    hintedInput.setAttribute(
      'aria-label',
      `Row ${data.row + 1}, column ${data.col + 1}, hinted value ${data.value}, locked`
    );
    document.getElementById('hints-used').innerText = `Hints used: ${data.hints_used}`;
    hintsUsed = data.hints_used;
    setMessage('');
    await checkForAutomaticCompletion();
  } catch (_error) {
    setMessage('Unable to get a hint. Please try again.');
  } finally {
    editableInputs.forEach(input => {
      if (!gameCompleted && !input.classList.contains('hinted')) input.disabled = false;
    });
    if (!gameCompleted) hintButton.disabled = false;
  }
}

function completeGame(inputs) {
  if (gameCompleted) return;
  gameCompleted = true;
  stopTimer();
  completionMetadata = {
    elapsed_ms: elapsedTimeMs,
    elapsed_seconds: Math.floor(elapsedTimeMs / 1000),
    difficulty: currentDifficulty,
    hints_used: hintsUsed,
  };
  window.completionMetadata = completionMetadata;
  Array.from(inputs).forEach(input => { input.disabled = true; });
  document.getElementById('check-solution').disabled = true;
  document.getElementById('hint').disabled = true;
  setMessage(`Congratulations! You solved it in ${formatElapsedTime(elapsedTimeMs)}.`, 'success');
  document.getElementById('score-entry').hidden = false;
  document.getElementById('player-name').focus();
}

async function checkSolution(automatic = false) {
    if (gameCompleted) {
        return;
    }

    const boardDiv = document.getElementById('sudoku-board');
    const inputs = boardDiv.getElementsByTagName('input');
    const board = readCurrentBoard();

    if (automatic && !isBoardFull(board)) {
        return;
    }

    // Prevent another check while this request is running.
    completionCheckPending = true;

    try {
        const response = await fetch('/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                board: board
            })
        });

        if (!response.ok) {
            throw new Error(`Check request failed: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            setMessage(data.error);
            return;
        }

        const incorrectCells = Array.isArray(data.incorrect)
            ? data.incorrect
            : [];

        const emptyCells = Array.isArray(data.empty)
            ? data.empty
            : [];

        // Clear previous validation.
        for (let index = 0; index < inputs.length; index++) {
            const input = inputs[index];

            if (input.disabled) {
                continue;
            }

            input.classList.remove('incorrect', 'missing');
            input.removeAttribute('aria-invalid');

            const row = Number(input.dataset.row);
            const col = Number(input.dataset.col);

            input.setAttribute(
                'aria-label',
                `Row ${row + 1}, column ${col + 1}, editable cell`
            );
        }

        // Highlight ALL incorrect filled cells.
        for (const [row, col] of incorrectCells) {
            const index = row * SIZE + col;
            const input = inputs[index];

            if (!input || input.disabled) {
                continue;
            }

            input.classList.add('incorrect');
            input.setAttribute('aria-invalid', 'true');

            input.setAttribute(
                'aria-label',
                `Incorrect entry, row ${row + 1}, column ${col + 1}`
            );
        }

        // Highlight ALL empty cells.
        for (const [row, col] of emptyCells) {
            const index = row * SIZE + col;
            const input = inputs[index];

            if (!input || input.disabled) {
                continue;
            }

            input.classList.add('missing');
            input.setAttribute('aria-invalid', 'true');

            input.setAttribute(
                'aria-label',
                `Missing entry, row ${row + 1}, column ${col + 1}`
            );
        }

        // Success ONLY when the entire board is correct.
        if (
            data.solved === true &&
            incorrectCells.length === 0 &&
            emptyCells.length === 0
        ) {
            completeGame(inputs);
            return;
        }

        // Incomplete/incorrect puzzle.
        const messages = [];

        if (incorrectCells.length > 0) {
            messages.push(
                `${incorrectCells.length} filled ${
                    incorrectCells.length === 1 ? 'cell is' : 'cells are'
                } incorrect`
            );
        }

        if (emptyCells.length > 0) {
            messages.push(
                `${emptyCells.length} ${
                    emptyCells.length === 1 ? 'cell is' : 'cells are'
                } empty`
            );
        }

        if (messages.length > 0) {
            setMessage(`${messages.join('. ')}.`);
        } else {
            setMessage('The puzzle is not solved yet.');
        }

    } catch (error) {
        console.error('Check Solution error:', error);
        setMessage('Unable to check the puzzle. Please try again.');
    } finally {
        completionCheckPending = false;
    }
}

function formatScoreTime(milliseconds) {
  return formatElapsedTime(milliseconds);
}

function readLeaderboard() {
  let storedScores;
  try {
    const saved = localStorage.getItem(LEADERBOARD_KEY);
    storedScores = saved ? JSON.parse(saved) : [];
  } catch (_error) {
    return [];
  }

  if (!Array.isArray(storedScores)) return [];
  return storedScores
    .filter(score => (
      score
      && typeof score.name === 'string'
      && score.name.trim().length > 0
      && Number.isFinite(score.elapsed_ms)
      && score.elapsed_ms >= 0
      && VALID_DIFFICULTIES.includes(score.difficulty)
      && Number.isInteger(score.hints_used)
      && score.hints_used >= 0
    ))
    .map(score => ({
      name: score.name.trim().slice(0, 40),
      elapsed_ms: score.elapsed_ms,
      difficulty: score.difficulty,
      hints_used: score.hints_used,
    }))
    .sort((first, second) => first.elapsed_ms - second.elapsed_ms)
    .slice(0, 10);
}

function renderLeaderboard() {
  const scores = readLeaderboard();
  const body = document.getElementById('leaderboard-body');
  const emptyState = document.getElementById('leaderboard-empty');
  body.replaceChildren();
  emptyState.hidden = scores.length > 0;

  scores.forEach((score, index) => {
    const row = body.insertRow();
    [
      String(index + 1),
      score.name,
      formatScoreTime(score.elapsed_ms),
      score.difficulty,
      String(score.hints_used),
    ].forEach(value => {
      row.insertCell().textContent = value;
    });
  });
}

function saveScore(event) {
  event.preventDefault();
  if (scoreSubmitted || !gameCompleted || !completionMetadata) return;

  const nameInput = document.getElementById('player-name');
  const name = nameInput.value.trim();
  const error = document.getElementById('score-error');
  if (!name) {
    error.textContent = 'Enter a name before saving your score.';
    nameInput.setAttribute('aria-invalid', 'true');
    nameInput.focus();
    return;
  }

  const score = {
    name: name.slice(0, 40),
    elapsed_ms: completionMetadata.elapsed_ms,
    difficulty: completionMetadata.difficulty,
    hints_used: completionMetadata.hints_used,
  };
  const scores = readLeaderboard();
  scores.push(score);
  scores.sort((first, second) => first.elapsed_ms - second.elapsed_ms);
  const topScores = scores.slice(0, 10);

  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(topScores));
  } catch (_error) {
    error.textContent = 'Unable to save scores in this browser.';
    return;
  }

  scoreSubmitted = true;
  renderLeaderboard();
  document.getElementById('score-entry').hidden = true;
  if (topScores.includes(score)) {
    setMessage('Your score was added to the leaderboard.', 'success');
  } else {
    setMessage('Your time did not place in the Top 10.');
  }
}

function applyTheme(theme) {
  const selectedTheme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = selectedTheme;
  const button = document.getElementById('theme-toggle');
  button.setAttribute('aria-pressed', String(selectedTheme === 'dark'));
  button.textContent = selectedTheme === 'dark' ? 'Light mode' : 'Dark mode';
}

function initializeTheme() {
  let savedTheme = 'light';
  try {
    savedTheme = localStorage.getItem(THEME_KEY) || 'light';
  } catch (_error) {
    savedTheme = 'light';
  }
  applyTheme(savedTheme);
}

function toggleTheme() {
  const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
  try {
    localStorage.setItem(THEME_KEY, nextTheme);
  } catch (_error) {
    setMessage('Theme changed but could not be saved.');
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();
  renderLeaderboard();
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('difficulty').addEventListener('change', newGame);
  const checkButton = document.getElementById('check-solution');

  checkButton.disabled = false;

  checkButton.addEventListener('click', () => {
      checkSolution(false);
  });
  document.getElementById('hint').addEventListener('click', useHint);
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
  document.getElementById('score-form').addEventListener('submit', saveScore);
  document.getElementById('player-name').addEventListener('input', event => {
    event.target.removeAttribute('aria-invalid');
    document.getElementById('score-error').textContent = '';
  });
  // initialize
  newGame();
});