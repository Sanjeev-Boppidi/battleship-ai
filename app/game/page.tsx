"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './page.module.css';

const BOARD_SIZE = 10;
const SHIPS: { [key: string]: number } = {
  carrier: 5,
  battleship: 4,
  cruiser: 3,
  submarine: 3,
  destroyer: 2,
};

const GameBoard: React.FC = () => {
  const [playerBoard, setPlayerBoard] = useState<string[][]>(Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill('')));
  const [aiBoard, setAiBoard] = useState<string[][]>(Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill('')));
  const [playerTurn, setPlayerTurn] = useState(false);
  const [selectedShip, setSelectedShip] = useState<string | null>(null);
  const [shipDirection, setShipDirection] = useState<'H' | 'V'>('H');
  const [placingShips, setPlacingShips] = useState(true);
  const [hoverCells, setHoverCells] = useState<{ row: number, col: number }[]>([]);

  const handleCellClick = (row: number, col: number, isAiBoard: boolean) => {
    console.log(`Cell clicked: row=${row}, col=${col}, isAiBoard=${isAiBoard}`);
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
        setPlayerTurn(false);
        makeAiMove();
      })
      .catch(error => {
        console.error('There was an error making the player move!', error);
      });
  };

  const makeAiMove = () => {
    axios.get('http://localhost:8080/api/ai_move')
      .then(response => {
        setPlayerBoard(response.data.playerBoard);
        setPlayerTurn(true);
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

  return (
    <div>
      <div className={styles.controls}>
        <h2>Place your ships</h2>
        <div>
          {Object.keys(SHIPS).map(ship => (
            <button key={ship} onClick={() => setSelectedShip(ship)}>
              {ship} ({SHIPS[ship]})
            </button>
          ))}
        </div>
        <div>
          <button onClick={() => setShipDirection('H')}>Horizontal</button>
          <button onClick={() => setShipDirection('V')}>Vertical</button>
        </div>
        <button onClick={startGame}>Start Game</button>
      </div>
      <div className={styles.gameBoard}>
        <div className={styles.board}>
          {playerBoard.map((row, rowIndex) =>
            row.map((cell, colIndex) => {
              const isHovered = hoverCells.some(cell => cell.row === rowIndex && cell.col === colIndex);
              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className={`${styles.cell} ${cell} ${isHovered ? styles.hover : ''}`}
                  onClick={() => handleCellClick(rowIndex, colIndex, false)}
                  onMouseEnter={() => handleCellMouseEnter(rowIndex, colIndex)}
                  onMouseLeave={handleCellMouseLeave}
                >
                  {cell}
                </div>
              );
            })
          )}
        </div>
        {!placingShips && (
          <div className={styles.board}>
            {aiBoard.map((row, rowIndex) =>
              row.map((cell, colIndex) =>
                <div key={`${rowIndex}-${colIndex}`} className={`${styles.cell} ${cell}`} onClick={() => handleCellClick(rowIndex, colIndex, true)}>
                  {cell}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GameBoard;
