import copy
import random

SIZE = 9
EMPTY = 0
MIN_CLUES = 17
DIFFICULTY_CLUE_RANGES = {
    "easy": (45, 81),
    "medium": (35, 44),
    "hard": (25, 34),
}
DIFFICULTY_GENERATION_ATTEMPTS = 10

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def _has_valid_givens(board):
    if len(board) != SIZE or any(len(row) != SIZE for row in board):
        return False

    rows = [set() for _ in range(SIZE)]
    columns = [set() for _ in range(SIZE)]
    boxes = [set() for _ in range(SIZE)]

    for row in range(SIZE):
        for col in range(SIZE):
            value = board[row][col]
            if not isinstance(value, int) or value < EMPTY or value > SIZE:
                return False
            if value == EMPTY:
                continue

            box = (row // 3) * 3 + col // 3
            if value in rows[row] or value in columns[col] or value in boxes[box]:
                return False
            rows[row].add(value)
            columns[col].add(value)
            boxes[box].add(value)

    return True

def _find_empty_cell(board):
    best_cell = None
    best_candidates = None

    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] != EMPTY:
                continue

            candidates = [
                num for num in range(1, SIZE + 1)
                if is_safe(board, row, col, num)
            ]
            if not candidates:
                return row, col, candidates
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_cell = (row, col)
                best_candidates = candidates
                if len(candidates) == 1:
                    return row, col, candidates

    if best_cell is None:
        return None
    return best_cell[0], best_cell[1], best_candidates

def count_solutions(board, limit=2):
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if not _has_valid_givens(board):
        return 0

    working_board = deep_copy(board)
    solution_count = 0

    def search():
        nonlocal solution_count
        if solution_count >= limit:
            return

        empty_cell = _find_empty_cell(working_board)
        if empty_cell is None:
            solution_count += 1
            return

        row, col, candidates = empty_cell
        for candidate in candidates:
            working_board[row][col] = candidate
            search()
            working_board[row][col] = EMPTY
            if solution_count >= limit:
                return

    search()
    return solution_count

def remove_cells(board, clues):
    attempts = SIZE * SIZE - clues
    while attempts > 0:
        row = random.randrange(SIZE)
        col = random.randrange(SIZE)
        if board[row][col] != EMPTY:
            board[row][col] = EMPTY
            attempts -= 1

def generate_puzzle(clues=35):
    if not isinstance(clues, int) or clues < MIN_CLUES or clues > SIZE * SIZE:
        raise ValueError(f"clues must be between {MIN_CLUES} and {SIZE * SIZE}")

    board = create_empty_board()
    if not fill_board(board):
        raise RuntimeError("Unable to generate a complete Sudoku solution")

    solution = deep_copy(board)
    cells = [
        (row, col)
        for row in range(SIZE)
        for col in range(SIZE)
    ]
    random.shuffle(cells)
    removed = 0
    for row, col in cells:
        if SIZE * SIZE - removed <= clues:
            break

        board[row][col] = EMPTY
        if count_solutions(board) == 1:
            removed += 1
        else:
            board[row][col] = solution[row][col]

    puzzle = deep_copy(board)
    return puzzle, solution

def generate_puzzle_for_difficulty(difficulty):
    if not isinstance(difficulty, str):
        raise ValueError("difficulty must be Easy, Medium, or Hard")

    difficulty = difficulty.strip().lower()
    if difficulty not in DIFFICULTY_CLUE_RANGES:
        raise ValueError("difficulty must be Easy, Medium, or Hard")

    min_clues, max_clues = DIFFICULTY_CLUE_RANGES[difficulty]
    for _ in range(DIFFICULTY_GENERATION_ATTEMPTS):
        puzzle, solution = generate_puzzle(clues=min_clues)
        clue_count = sum(value != EMPTY for row in puzzle for value in row)
        if min_clues <= clue_count <= max_clues:
            return puzzle, solution

    raise RuntimeError(f"Unable to generate a {difficulty} puzzle")
