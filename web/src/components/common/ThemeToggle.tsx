import { ActionIcon, Tooltip } from '@mantine/core';
import { IconSun, IconMoon } from '@tabler/icons-react';
import { useUIStore } from '../../stores/useUIStore';

export function ThemeToggle() {
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);

  return (
    <Tooltip label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
      <ActionIcon variant="subtle" onClick={toggleTheme} size="lg">
        {theme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
      </ActionIcon>
    </Tooltip>
  );
}
