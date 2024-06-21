import React from 'react';
import styles from './page.module.css';

const Footer: React.FC = () => {
    return (
        <footer className={styles.footer}>
         <p>
                <a href="http://localhost:3000" target="_blank" rel="noopener ">
                    Battleship AI
                </a> by Sanjeev Boppidi
            </p>
    </footer>
    );
};

export default Footer;
