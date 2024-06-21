"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './page.module.css';
import 'react-bootstrap';
import Header from './header';
import Footer from './footer';

const BOARD_SIZE = 10;
const SHIPS: { [key: string]: number } = {
  Carrier: 5,
  Battleship: 4,
  Cruiser: 3,
  Submarine: 3,
  Destroyer: 2,
};

const GameBoard: React.FC = () => {
  const [playerBoard, setPlayerBoard] = useState<string[][]>(Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill('')));
  const [aiBoard, setAiBoard] = useState<string[][]>(Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill('')));
  const [playerTurn, setPlayerTurn] = useState(false);
  const [selectedShip, setSelectedShip] = useState<string | null>(null);
  const [shipDirection, setShipDirection] = useState<'H' | 'V'>('H');
  const [placingShips, setPlacingShips] = useState(true);
  const [hoverCells, setHoverCells] = useState<{ row: number, col: number }[]>([]);
  const [availableShips, setAvailableShips] = useState<string[]>(Object.keys(SHIPS));
  const [winner, setWinner] = useState<string | null>(null);

  const handleCellClick = (row: number, col: number, isAiBoard: boolean) => {
    if (!isAiBoard && placingShips && selectedShip) {
      placeShip(row, col);
    } else if (isAiBoard && playerTurn) {
      makePlayerMove(row, col);
    }
  };

  const handleCellMouseEnter = (row: number, col: number) => {
    if (placingShips && selectedShip) {
      const length = SHIPS[selectedShip];
      const cells = [];
      for (let i = 0; i < length; i++) {
        if (shipDirection === 'H' && col + i < BOARD_SIZE) {
          cells.push({ row, col: col + i });
        } else if (shipDirection === 'V' && row + i < BOARD_SIZE) {
          cells.push({ row: row + i, col });
        }
      }
      setHoverCells(cells);
    }
  };

  const handleCellMouseLeave = () => {
    setHoverCells([]);
  };

  const placeShip = (row: number, col: number) => {
    axios.post('http://localhost:8080/api/player_place_ship', {
      shipType: selectedShip,
      row,
      col,
      direction: shipDirection
    }).then(response => {
      if (response.data.success) {
        setPlayerBoard(response.data.playerBoard);
        setAvailableShips(prevShips => prevShips.filter(ship => ship !== selectedShip));
        setSelectedShip(null);
        setHoverCells([]);
      } else {
        alert('Cannot place ship here');
      }
    }).catch(error => {
      console.error('Error placing ship:', error);
    });
  };

  const makePlayerMove = (row: number, col: number) => {
    axios.post('http://localhost:8080/api/player_move', { row, col })
      .then(response => {
        setAiBoard(response.data.aiBoard);
        if (response.data.winner) {
          setWinner(response.data.winner);
        } else {
          setPlayerTurn(false);
          makeAiMove();
        }
      })
      .catch(error => {
        console.error('There was an error making the player move!', error);
      });
  };

  const makeAiMove = () => {
    axios.get('http://localhost:8080/api/ai_move')
      .then(response => {
        setPlayerBoard(response.data.playerBoard);
        if (response.data.winner) {
          setWinner(response.data.winner);
        } else {
          setPlayerTurn(true);
        }
      })
      .catch(error => {
        console.error('There was an error making the AI move!', error);
      });
  };

  useEffect(() => {
    axios.get('http://localhost:8080/api/init')
      .then(response => {
        setAiBoard(response.data.aiBoard);
      })
      .catch(error => {
        console.error('There was an error initializing the boards!', error);
      });
  }, []);

  const startGame = () => {
    setPlacingShips(false);
    setPlayerTurn(true);
  };

  const toggleShipDirection = () => {
    setShipDirection(prevDirection => (prevDirection === 'H' ? 'V' : 'H'));
  };

  const getCellClass = (cell: string) => {
    switch (cell) {
      case '':
        return styles.empty;
      case 'S':
        return styles.sunk;
      case 'O':
        return styles.miss;
      case 'P':
        return styles.ship;
      case 'X':
        return styles.hit;
      default:
        return '';
    }
  };

  const winnerModal = (winner: string) => {
    if (winner === "Player") {
      return (
        <div className="d-flex">
          <div><i className="fa-solid fa-circle-exclamation me-2 pt-3 pb-3 fontsize-5 text-warning"></i></div>
          <div className="ms-2 fontsize-3 fw-bold text-muted">
            Congratulations! You won the game.
          </div>
        </div>
      );
    } else if (winner === "AI") {
      return (
        <div className="d-flex">
          <div><i className="fa-solid fa-circle-exclamation me-2 pt-3 pb-3 fontsize-5 text-warning"></i></div>
          <div className="ms-2 fontsize-3 fw-bold text-muted">
            Sorry! You lost the game.
          </div>
        </div>
      );
    }
  };

  return (
    <div>
      <Header />
      {winner && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            {winnerModal("Player")}
            <br />
            <button onClick={() => window.location.reload()} className={styles.closeButton}>Play Again</button>
          </div>
        </div>
      )}
      {placingShips && (
      <div className={styles.controls}>
        <div className=''>
          <h1>Select your ship</h1>
        </div>
        <div>
          {availableShips.map(ship => (
            <button
              key={ship}
              onClick={() => setSelectedShip(ship)}
              className={`${styles.shipButton} ${selectedShip === ship ? styles.selectedShip : ''}`}
              style={{
                width: `${SHIPS[ship] * 40}px`, // Assuming each cell is 40px wide
              }}
            >
              {ship}
            </button>
          ))}
        </div>
        <br />
        <button className={styles.rotateButton} onClick={toggleShipDirection}>
          Rotate Ship
        </button>
        <br />
        <br /><br />
      </div>
      
      )}
      
      <div className={styles.gameBoard}>
        <div>
          <h1 className={styles.fleet}>Your Fleet</h1>
        <div className={styles.board}>
          {playerBoard.map((row, rowIndex) =>
            row.map((cell, colIndex) => {
              const isHovered = hoverCells.some(cell => cell.row === rowIndex && cell.col === colIndex);
              const isClickable = cell === '';
              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className={`${styles.cell} ${getCellClass(cell)} ${isHovered ? styles.hover : ''} ${isClickable ? '' : styles.nonClickable}`}
                  onClick={() => isClickable && handleCellClick(rowIndex, colIndex, false)}
                  onMouseEnter={() => isClickable && handleCellMouseEnter(rowIndex, colIndex)}
                  onMouseLeave={() => isClickable && handleCellMouseLeave()}
                />
              );
            })
          )}
        </div>
        </div>
        <div className={styles.board}>
          {placingShips && (
            <div className={styles.instructionsContainer}>
              <div className={styles.instructions}>
                <p>Instructions:</p>
                <ol>
                  <li>1. Select a ship by clicking on its button.</li>
                  <li>2. Click on the board to place the ship.</li>
                  <li>3. Once all ships are placed, click "Start Game" to begin.</li>
                  <li>4. Click on the cells of the enemy's map to find and destroy all five enemy ships.</li>
                  <li>5. The computer will fire on your ships immediately after you fire on its ships.</li>
                  <li>6. The game ends when all ships on one side are sunk.</li>
                </ol>
              </div>
            </div>
          )}
        </div>
        {!placingShips && (
          <div>
            <h1 className={styles.fleet} >Enemy Fleet</h1>
          <div className={styles.board}>
            
            {aiBoard.map((row, rowIndex) =>
              row.map((cell, colIndex) => {
                const isClickable = cell === '';
                return (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className={`${styles.cell} ${getCellClass(cell)} ${isClickable ? '' : styles.nonClickable}`}
                    onClick={() => isClickable && handleCellClick(rowIndex, colIndex, true)}
                  />
                );
              })
            )}
          </div>
          </div>
        )}
      </div>
      <div className={styles.controls}>
        {availableShips.length === 0 && placingShips && (
          <button onClick={startGame} className={styles.startButton}>Start Game</button>
        )}
      </div>
      <Footer />
    </div>
    
  );
};

export default GameBoard;
