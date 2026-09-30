import sudoku_logic


UNIQUE_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


def test_create_empty_board_has_nine_rows_and_columns():
    """An empty board is a 9-by-9 grid filled with zeroes."""
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(value == sudoku_logic.EMPTY for row in board for value in row)


def test_deep_copy_does_not_share_rows_with_original_board():
    """Changing a copied board does not change the source board."""
    board = sudoku_logic.create_empty_board()
    copied_board = sudoku_logic.deep_copy(board)

    copied_board[0][0] = 5

    assert board[0][0] == sudoku_logic.EMPTY


def test_is_safe_rejects_row_column_and_box_conflicts():
    """A number already in the row, column, or 3-by-3 box is not safe."""
    row_board = sudoku_logic.create_empty_board()
    row_board[0][0] = 5
    column_board = sudoku_logic.create_empty_board()
    column_board[0][0] = 5
    box_board = sudoku_logic.create_empty_board()
    box_board[1][1] = 5

    assert not sudoku_logic.is_safe(row_board, 0, 1, 5)
    assert not sudoku_logic.is_safe(column_board, 1, 0, 5)
    assert not sudoku_logic.is_safe(box_board, 2, 2, 5)


def test_count_solutions_detects_a_unique_solution_without_mutating_board():
    """A standard Sudoku puzzle has one solution and is left unchanged."""
    board = sudoku_logic.deep_copy(UNIQUE_PUZZLE)

    assert sudoku_logic.count_solutions(board) == 1
    assert board == UNIQUE_PUZZLE


def test_count_solutions_stops_at_limit_for_multiple_solutions():
    """An empty board has multiple solutions; counting stops at the limit."""
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(board) == 2
    assert sudoku_logic.count_solutions(board, limit=1) == 1


def test_count_solutions_rejects_invalid_givens():
    """Conflicting givens have no solutions and remain unchanged."""
    board = sudoku_logic.create_empty_board()
    board[0][0] = 5
    board[0][1] = 5
    original = sudoku_logic.deep_copy(board)

    assert sudoku_logic.count_solutions(board) == 0
    assert board == original


def test_generate_puzzle_returns_valid_solution_and_requested_clues():
    """Puzzle clues match the solution, whose rows, columns, and boxes are valid."""
    puzzle, solution = sudoku_logic.generate_puzzle(clues=40)

    expected_digits = set(range(1, sudoku_logic.SIZE + 1))
    assert all(set(row) == expected_digits for row in solution)
    assert all(
        {solution[row][col] for row in range(sudoku_logic.SIZE)} == expected_digits
        for col in range(sudoku_logic.SIZE)
    )
    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                solution[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert box == expected_digits

    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == 40
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert all(
        puzzle[row][col] in (sudoku_logic.EMPTY, solution[row][col])
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
    )