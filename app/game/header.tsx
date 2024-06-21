import React from 'react';
import styles from './page.module.css';

const Header: React.FC = () => {
    return (
        <header className={`${styles.header}`}>
      <p>BATTLESHIP AI</p>
    </header>
    )
};

export default Header;
