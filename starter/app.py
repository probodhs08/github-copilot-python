import random

from flask import Flask, render_template, jsonify, request
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None,
    'hints_used': 0,
    'difficulty': None,
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    clues = request.args.get('clues')
    difficulty = request.args.get('difficulty')
    try:
        if clues is not None:
            clue_count = int(clues)
            puzzle, solution = sudoku_logic.generate_puzzle(clue_count)
            active_difficulty = next(
                (
                    name.title()
                    for name, (minimum, maximum) in sudoku_logic.DIFFICULTY_CLUE_RANGES.items()
                    if minimum <= clue_count <= maximum
                ),
                'Custom',
            )
        elif difficulty is not None:
            puzzle, solution = sudoku_logic.generate_puzzle_for_difficulty(difficulty)
            active_difficulty = difficulty.strip().title()
        else:
            puzzle, solution = sudoku_logic.generate_puzzle(35)
            active_difficulty = 'Medium'
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['hints_used'] = 0
    CURRENT['difficulty'] = active_difficulty
    return jsonify({'puzzle': puzzle})

@app.route('/check', methods=['POST'])
def check_solution():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400

    board = data.get('board')
    solution = CURRENT.get('solution')

    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    # Validate that the submitted board is a 9x9 grid.
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(
            not isinstance(row, list)
            or len(row) != sudoku_logic.SIZE
            for row in board
        )
        or any(
            not isinstance(value, int)
            or value < sudoku_logic.EMPTY
            or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return jsonify({'error': 'A valid 9-by-9 board is required'}), 400

    incorrect = []
    empty = []

    # Check ALL 81 cells.
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            value = board[row][col]

            if value == sudoku_logic.EMPTY:
                empty.append([row, col])
            elif value != solution[row][col]:
                incorrect.append([row, col])

    # The puzzle is solved only when there are NO
    # empty cells and NO incorrect cells.
    solved = len(empty) == 0 and len(incorrect) == 0

    return jsonify({
        'incorrect': incorrect,
        'empty': empty,
        'solved': solved,
    })

@app.route('/hint', methods=['POST'])
def get_hint():
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(not isinstance(row, list) or len(row) != sudoku_logic.SIZE for row in board)
        or any(
            not isinstance(value, int) or value < sudoku_logic.EMPTY or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return jsonify({'error': 'A valid 9-by-9 board is required'}), 400

    available_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
        and board[row][col] == sudoku_logic.EMPTY
    ]
    if not available_cells:
        return jsonify({'error': 'No empty cells available for a hint'}), 409

    row, col = random.choice(available_cells)
    CURRENT['hints_used'] += 1
    return jsonify({
        'row': row,
        'col': col,
        'value': solution[row][col],
        'hints_used': CURRENT['hints_used'],
    })

if __name__ == '__main__':
    app.run(debug=True)