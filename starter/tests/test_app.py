import app as sudoku_app
import sudoku_logic


def test_index_renders_the_sudoku_page():
    """The home route serves the page containing the game board and controls."""
    response = sudoku_app.app.test_client().get("/")

    assert response.status_code == 200
    assert b"Sudoku Game" in response.data
    assert b"sudoku-board" in response.data


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
    assert sudoku_app.CURRENT == {"puzzle": puzzle, "solution": solution}


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
    assert response.get_json() == {"incorrect": [[2, 4]]}