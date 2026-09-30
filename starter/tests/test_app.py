import app as sudoku_app
import sudoku_logic


def valid_solution():
    return [
        [
            (row * 3 + row // 3 + col) % sudoku_logic.SIZE + 1
            for col in range(sudoku_logic.SIZE)
        ]
        for row in range(sudoku_logic.SIZE)
    ]


def test_index_renders_the_sudoku_page():
    """The home route serves the page containing the game board and controls."""
    response = sudoku_app.app.test_client().get("/")

    assert response.status_code == 200
    assert b"Sudoku Game" in response.data
    assert b"sudoku-board" in response.data
    assert b'id="hint"' in response.data
    assert b'id="hints-used"' in response.data
    assert b'id="timer"' in response.data


def test_new_game_returns_puzzle_and_stores_solution(monkeypatch):
    """The new-game route uses the default clue count and saves the generated game."""
    puzzle = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    solution = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    requested_clues = []

    def generate_puzzle(clues):
        requested_clues.append(clues)
        return puzzle, solution

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", generate_puzzle)
    response = sudoku_app.app.test_client().get("/new")

    assert response.status_code == 200
    assert response.get_json() == {"puzzle": puzzle}
    assert requested_clues == [35]
    assert sudoku_app.CURRENT == {
        "puzzle": puzzle,
        "solution": solution,
        "hints_used": 0,
        "difficulty": "Medium",
    }


def test_new_game_accepts_a_clue_count(monkeypatch):
    """The new-game route forwards the clues query parameter to the generator."""
    requested_clues = []

    def generate_puzzle(clues):
        requested_clues.append(clues)
        return [], []

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", generate_puzzle)
    response = sudoku_app.app.test_client().get("/new?clues=50")

    assert response.status_code == 200
    assert requested_clues == [50]


def test_new_game_accepts_a_difficulty(monkeypatch):
    requested_difficulties = []

    def generate_puzzle_for_difficulty(difficulty):
        requested_difficulties.append(difficulty)
        return [], []

    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle_for_difficulty",
        generate_puzzle_for_difficulty,
    )
    response = sudoku_app.app.test_client().get("/new?difficulty=hard")

    assert response.status_code == 200
    assert requested_difficulties == ["hard"]
    assert sudoku_app.CURRENT["difficulty"] == "Hard"


def test_new_game_clues_parameter_takes_precedence_over_difficulty(monkeypatch):
    requested_clues = []

    def generate_puzzle(clues):
        requested_clues.append(clues)
        return [], []

    def generate_puzzle_for_difficulty(_difficulty):
        raise AssertionError("Explicit clues should take precedence")

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", generate_puzzle)
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle_for_difficulty",
        generate_puzzle_for_difficulty,
    )
    response = sudoku_app.app.test_client().get(
        "/new?clues=50&difficulty=hard"
    )

    assert response.status_code == 200
    assert requested_clues == [50]
    assert sudoku_app.CURRENT["difficulty"] == "Easy"


def test_new_game_rejects_invalid_difficulty():
    response = sudoku_app.app.test_client().get("/new?difficulty=expert")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "difficulty must be Easy, Medium, or Hard"
    }


def test_index_includes_difficulty_selector():
    response = sudoku_app.app.test_client().get("/")

    assert b'id="difficulty"' in response.data
    assert b">Easy<" in response.data
    assert b">Medium<" in response.data
    assert b">Hard<" in response.data


def test_check_without_game_returns_error():
    """Checking before starting a game returns the existing 400 error response."""
    sudoku_app.CURRENT["solution"] = None
    response = sudoku_app.app.test_client().post("/check", json={"board": []})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_returns_coordinates_of_cells_that_differ():
    """The check route reports each board cell that differs from the solution."""
    solution = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    board = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    board[2][4] = 7
    sudoku_app.CURRENT["solution"] = solution

    response = sudoku_app.app.test_client().post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[2, 4]], "solved": False}


def test_check_marks_an_incomplete_board_unsolved():
    solution = valid_solution()
    board = [row[:] for row in solution]
    board[0][0] = sudoku_logic.EMPTY
    sudoku_app.CURRENT["solution"] = solution

    response = sudoku_app.app.test_client().post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[0, 0]], "solved": False}


def test_check_marks_a_full_but_incorrect_board_unsolved():
    solution = valid_solution()
    board = [row[:] for row in solution]
    board[0][0] = board[0][1]
    sudoku_app.CURRENT["solution"] = solution

    response = sudoku_app.app.test_client().post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[0, 0]], "solved": False}


def test_check_marks_a_correctly_solved_board_without_exposing_solution():
    solution = valid_solution()
    sudoku_app.CURRENT["solution"] = solution

    response = sudoku_app.app.test_client().post(
        "/check", json={"board": solution}
    )

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [], "solved": True}


def test_hint_returns_one_correct_empty_cell_without_exposing_solution():
    puzzle = sudoku_logic.create_empty_board()
    solution = [[(row + col) % sudoku_logic.SIZE + 1 for col in range(sudoku_logic.SIZE)]
                for row in range(sudoku_logic.SIZE)]
    board = sudoku_logic.create_empty_board()
    board[0][0] = 9
    sudoku_app.CURRENT.update(puzzle=puzzle, solution=solution, hints_used=0)

    response = sudoku_app.app.test_client().post("/hint", json={"board": board})

    assert response.status_code == 200
    data = response.get_json()
    assert set(data) == {"row", "col", "value", "hints_used"}
    assert (data["row"], data["col"]) != (0, 0)
    assert data["value"] == solution[data["row"]][data["col"]]
    assert data["hints_used"] == 1
    assert sudoku_app.CURRENT["hints_used"] == 1
    assert board[0][0] == 9


def test_hint_does_not_overwrite_existing_entries_and_uses_only_original_blanks():
    puzzle = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    puzzle[4][6] = sudoku_logic.EMPTY
    solution = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    solution[4][6] = 7
    board = [row[:] for row in puzzle]
    board[4][6] = sudoku_logic.EMPTY
    sudoku_app.CURRENT.update(puzzle=puzzle, solution=solution, hints_used=0)

    response = sudoku_app.app.test_client().post("/hint", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "row": 4,
        "col": 6,
        "value": 7,
        "hints_used": 1,
    }
    assert board[4][6] == sudoku_logic.EMPTY


def test_hint_returns_conflict_when_no_empty_eligible_cells_remain():
    puzzle = sudoku_logic.create_empty_board()
    solution = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    board = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    sudoku_app.CURRENT.update(puzzle=puzzle, solution=solution, hints_used=2)

    response = sudoku_app.app.test_client().post("/hint", json={"board": board})

    assert response.status_code == 409
    assert response.get_json() == {"error": "No empty cells available for a hint"}
    assert sudoku_app.CURRENT["hints_used"] == 2


def test_hint_without_game_returns_error():
    sudoku_app.CURRENT.update(puzzle=None, solution=None, hints_used=0)

    response = sudoku_app.app.test_client().post(
        "/hint", json={"board": sudoku_logic.create_empty_board()}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_hint_requires_a_valid_board():
    sudoku_app.CURRENT.update(
        puzzle=sudoku_logic.create_empty_board(),
        solution=[[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)],
        hints_used=0,
    )

    response = sudoku_app.app.test_client().post("/hint", json={"board": []})

    assert response.status_code == 400
    assert response.get_json() == {"error": "A valid 9-by-9 board is required"}