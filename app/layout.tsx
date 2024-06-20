// app/layout.tsx
import '../app/globals.css';

export const metadata = {
  title: 'Battleship AI Game',
  description: 'A simple Battleship AI game using Next.js and Python',
};

const RootLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
};

export default RootLayout;
