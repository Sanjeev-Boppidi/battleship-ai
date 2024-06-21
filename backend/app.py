from flask import Flask, request, jsonify
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BOARD_SIZE = 10

SHIPS = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2
}

HUNT_MODE = 'hunt'
TARGET_MODE = 'target'
DIRECTIONS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
OPPOSITE_DIRECTION = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
NEXT_DIRECTION = {'right': 'left', 'left': 'up', 'up': 'down', 'down': 'right'}


mode = HUNT_MODE
target_queue = []
hit_list = []
direction = None
first_hit = None
last_hit = None
tried_opposite = False

def create_empty_board():
    return [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


player_board = create_empty_board()
ai_board = create_empty_board()

# Store ship positions
player_ships = {}
ai_ships = {}

player_ships_sunk = 0
ai_ships_sunk = 0



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
    positions = []
    if direction == 'H':
        for c in range(col, col + ship_length):
            board[row][c] = 'P'
            positions.append((row, c))
    else:  # direction == 'V'
        for r in range(row, row + ship_length):
            board[r][col] = 'P'
            positions.append((r, col))
    return positions

def place_all_ships_randomly(board, ship_dict):
    for ship, length in SHIPS.items():
        placed = False
        while not placed:
            direction = random.choice(['H', 'V'])
            row, col = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
            if can_place_ship(board, length, row, col, direction):
                positions = place_ship(board, length, row, col, direction)
                ship_dict[ship] = positions
                placed = True

# Only place ships on AI board initially
place_all_ships_randomly(ai_board, ai_ships)

@app.route('/api/init', methods=['GET'])
def initialize_boards():
    global player_board, ai_board, player_ships, ai_ships, hit_list, player_ships_sunk, ai_ships_sunk
    player_board = create_empty_board()  # Reset player board
    ai_board = create_empty_board()  # Reset AI board and place ships
    ai_ships = {}
    place_all_ships_randomly(ai_board, ai_ships)
    player_ships = {}
    hit_list = []
    player_ships_sunk = 0
    ai_ships_sunk = 0
    return jsonify({'playerBoard': player_board, 'aiBoard': create_empty_board()})

@app.route('/api/player_place_ship', methods=['POST'])
def player_place_ship():
    data = request.get_json()
    ship_type = data['shipType']
    row, col = data['row'], data['col']
    direction = data['direction']
    ship_length = SHIPS[ship_type]

    if can_place_ship(player_board, ship_length, row, col, direction):
        positions = place_ship(player_board, ship_length, row, col, direction)
        player_ships[ship_type] = positions
        return jsonify({'playerBoard': player_board, 'success': True})
    else:
        return jsonify({'error': 'Cannot place ship here', 'success': False}), 400

@app.route('/api/player_move', methods=['POST'])
def player_move():
    global ai_ships_sunk
    data = request.get_json()
    row, col = data['row'], data['col']
    cell_state = 'miss'

    if ai_board[row][col] == 'P':
        ai_board[row][col] = 'X'
        cell_state = 'hit'
        for ship, positions in ai_ships.items():
            if is_ship_sunk(positions, ai_board):
                mark_ship_as_sunk(positions, ai_board)
                ai_ships_sunk += 1
    elif ai_board[row][col] == '':
        ai_board[row][col] = 'O'

    # Create a display version of ai_board that hides unhit ship positions
    display_ai_board = [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if ai_board[r][c] in ['X', 'O', 'S']:
                display_ai_board[r][c] = ai_board[r][c]

    winner = check_winner(ai_ships_sunk, 'Player')

    return jsonify({'aiBoard': display_ai_board, 'cellState': cell_state, 'winner': winner})

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

def is_ship_sunk(ship_positions, board):
    return all(board[r][c] == 'X' for r, c in ship_positions)

def mark_ship_as_sunk(ship_positions, board):
    for r, c in ship_positions:
        board[r][c] = 'S'

def check_winner(ships_sunk, player):
    if ships_sunk == len(SHIPS):  # Check if all ships are sunk
        return player
    return None

@app.route('/api/ai_move', methods=['GET'])
def ai_move():
    global mode, target_queue, direction, first_hit, last_hit, tried_opposite, hit_list, player_ships_sunk

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
            hit_list.append((row, col))
        else:
            player_board[row][col] = 'O'

    elif mode == TARGET_MODE:
        if direction:
            row, col = get_next_cell_in_direction(*last_hit, direction)
            if row is None or player_board[row][col] in ['X', 'O', 'S']:
                direction = NEXT_DIRECTION[direction]
                last_hit = first_hit
                
                row, col = get_next_cell_in_direction(*last_hit, direction)
                if row is None or player_board[row][col] in ['X', 'O', 'S']:
                    direction = None
        if not direction:
            if not target_queue:
                while hit_list:
                    next_hit = hit_list.pop(0)
                    if any(player_board[r][c] == 'P' for r, c, _ in get_adjacent_cells(*next_hit)):
                        first_hit = next_hit
                        last_hit = next_hit
                        target_queue = get_adjacent_cells(*next_hit)
                        direction = None
                        break
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
            
            hit_list.append((row, col))
            for ship, positions in player_ships.items():
                if is_ship_sunk(positions, player_board):
                    mark_ship_as_sunk(positions, player_board)
                    player_ships_sunk += 1
                    for pos in positions:
                        if pos in hit_list:
                            hit_list.remove(pos)
            if not direction:
                direction = next(dir for dir, (dr, dc) in DIRECTIONS.items() if (row + dr, col + dc) == first_hit)
        else:
            player_board[row][col] = 'O'
            if direction and not tried_opposite:
                direction = OPPOSITE_DIRECTION[direction]
                last_hit = first_hit
                tried_opposite = True
            else:
                direction = None

    winner = check_winner(player_ships_sunk, 'AI')

    return jsonify({'playerBoard': player_board, 'winner': winner})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
