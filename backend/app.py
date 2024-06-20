from flask import Flask, request, jsonify
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BOARD_SIZE = 10

SHIPS = {
    "carrier": 5,
    "battleship": 4,
    "cruiser": 3,
    "submarine": 3,
    "destroyer": 2
}

HUNT_MODE = 'hunt'
TARGET_MODE = 'target'
DIRECTIONS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
OPPOSITE_DIRECTION = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
NEXT_DIRECTION = {'right': 'left', 'left': 'up', 'up': 'down', 'down': 'right'}

# Initial state
mode = HUNT_MODE
target_queue = []
direction = None
first_hit = None
last_hit = None
tried_opposite = False

def get_random_cell():
    return random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)

def get_adjacent_cells(row, col):
    adjacent_cells = []
    for dir, (dr, dc) in DIRECTIONS.items():
        r, c = row + dr, col + dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            adjacent_cells.append((r, c, dir))
    return adjacent_cells

def get_next_cell_in_direction(row, col, direction):
    dr, dc = DIRECTIONS[direction]
    r, c = row + dr, col + dc
    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        return r, c
    return None, None

def collect_ship_cells(row, col):
    # Collect all cells of the ship
    ship_cells = [(row, col)]
    for dr, dc in DIRECTIONS.values():
        r, c = row, col
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and player_board[r][c] in ['X', 'P']:
            if (r, c) not in ship_cells:
                ship_cells.append((r, c))
            r += dr
            c += dc
        r, c = row, col
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and player_board[r][c] in ['X', 'P']:
            if (r, c) not in ship_cells:
                ship_cells.append((r, c))
            r -= dr
            c -= dc
    return ship_cells

def mark_ship_as_sunk(ship_cells):
    for r, c in ship_cells:
        player_board[r][c] = 'S'

def is_ship_sunk(ship_cells):
    for r, c in ship_cells:
        if player_board[r][c] == 'P':
            return False
    return True

def create_empty_board():
    return [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

player_board = create_empty_board()
ai_board = create_empty_board()

def can_place_ship(board, ship_length, row, col, direction):
    if direction == 'H':
        if col + ship_length > BOARD_SIZE:
            return False
        return all(board[row][c] == '' for c in range(col, col + ship_length))
    else:  # direction == 'V'
        if row + ship_length > BOARD_SIZE:
            return False
        return all(board[r][col] == '' for r in range(row, row + ship_length))

def place_ship(board, ship_length, row, col, direction):
    if direction == 'H':
        for c in range(col, col + ship_length):
            board[row][c] = 'P'
    else:  # direction == 'V'
        for r in range(row, row + ship_length):
            board[r][col] = 'P'
    return board

def place_all_ships_randomly(board):
    for ship, length in SHIPS.items():
        placed = False
        while not placed:
            direction = random.choice(['H', 'V'])
            row, col = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
            if can_place_ship(board, length, row, col, direction):
                place_ship(board, length, row, col, direction)
                placed = True

# Only place ships on AI board initially
place_all_ships_randomly(ai_board)

@app.route('/api/init', methods=['GET'])
def initialize_boards():
    global player_board, ai_board
    player_board = create_empty_board()  # Reset player board
    ai_board = create_empty_board()  # Reset AI board and place ships
    place_all_ships_randomly(ai_board)
    return jsonify({'playerBoard': player_board, 'aiBoard': create_empty_board()})

@app.route('/api/player_place_ship', methods=['POST'])
def player_place_ship():
    data = request.get_json()
    ship_type = data['shipType']
    row, col = data['row'], data['col']
    direction = data['direction']
    ship_length = SHIPS[ship_type]

    if can_place_ship(player_board, ship_length, row, col, direction):
        place_ship(player_board, ship_length, row, col, direction)
        # Mark the placed cells as 'placed'
        for i in range(ship_length):
            if direction == 'H':
                player_board[row][col + i] = 'P'
            else:  # direction == 'V'
                player_board[row + i][col] = 'P'
        return jsonify({'playerBoard': player_board, 'success': True})
    else:
        return jsonify({'error': 'Cannot place ship here', 'success': False}), 400


@app.route('/api/player_move', methods=['POST'])
def player_move():
    data = request.get_json()
    row, col = data['row'], data['col']
    cell_state = 'miss'

    if ai_board[row][col] == 'P':
        ai_board[row][col] = 'X'
        cell_state = 'hit'
    else:
        ai_board[row][col] = 'O'

    display_ai_board = create_empty_board()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if ai_board[r][c] == 'X':
                display_ai_board[r][c] = 'hit'
            elif ai_board[r][c] == 'O':
                display_ai_board[r][c] = 'miss'

    return jsonify({'cellState': cell_state, 'aiBoard': display_ai_board})

@app.route('/api/ai_move', methods=['GET'])
def ai_move():
    global mode, target_queue, direction, first_hit, last_hit, tried_opposite

    if mode == HUNT_MODE:
        row, col = get_random_cell()
        while player_board[row][col] in ['X', 'O', 'S']:
            row, col = get_random_cell()
        
        if player_board[row][col] == 'P':
            player_board[row][col] = 'X'
            mode = TARGET_MODE
            first_hit = (row, col)
            last_hit = (row, col)
            target_queue = get_adjacent_cells(row, col)
        else:
            player_board[row][col] = 'O'

    elif mode == TARGET_MODE:
        if direction:
            row, col = get_next_cell_in_direction(*last_hit, direction)
            if row is None or player_board[row][col] in ['X', 'O', 'S']:
                direction = NEXT_DIRECTION[direction]
                last_hit = first_hit
                tried_opposite = True
                row, col = get_next_cell_in_direction(*last_hit, direction)
                if row is None or player_board[row][col] in ['X', 'O', 'S']:
                    direction = None
        if not direction:
            if not target_queue:
                mode = HUNT_MODE
                return ai_move()
            row, col, direction = target_queue.pop(0)
            while player_board[row][col] in ['X', 'O', 'S']:
                if not target_queue:
                    mode = HUNT_MODE
                    return ai_move()
                row, col, direction = target_queue.pop(0)
            tried_opposite = False
        
        if player_board[row][col] == 'P':
            player_board[row][col] = 'X'
            last_hit = (row, col)
            ship_cells = collect_ship_cells(first_hit[0], first_hit[1])
            if is_ship_sunk(ship_cells):
                mark_ship_as_sunk(ship_cells)
                mode = HUNT_MODE
            elif not direction:
                direction = next(dir for dir, (dr, dc) in DIRECTIONS.items() if (row + dr, col + dc) == first_hit)
        else:
            player_board[row][col] = 'O'
            if direction and not tried_opposite:
                direction = NEXT_DIRECTION[direction]
                last_hit = first_hit
                tried_opposite = True
            else:
                direction = None

    return jsonify({'playerBoard': player_board})


if __name__ == '__main__':
    app.run(debug=True,port=8080)
    



