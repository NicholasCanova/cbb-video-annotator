import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import '@mantine/core/styles.css';
import { theme } from './config/defaultTheme';
import { useUIStore } from './stores/useUIStore';
import App from './App';

function Root() {
  const colorScheme = useUIStore((s) => s.theme);

  return (
    <MantineProvider theme={theme} defaultColorScheme={colorScheme} forceColorScheme={colorScheme}>
      <App />
    </MantineProvider>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ColorSchemeScript defaultColorScheme="light" />
    <Root />
  </StrictMode>
);
