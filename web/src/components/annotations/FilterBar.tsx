import { Autocomplete, Group, ActionIcon } from '@mantine/core';
import { IconX } from '@tabler/icons-react';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useClassesConfig } from '../../hooks/useClassesConfig';

export function FilterBar() {
  const filter = useAnnotationStore((s) => s.filter);
  const setFilter = useAnnotationStore((s) => s.setFilter);
  const config = useClassesConfig();

  return (
    <Group gap={4}>
      <Autocomplete
        placeholder="Filter actions..."
        value={filter}
        onChange={setFilter}
        data={config?.labels ?? []}
        size="xs"
        style={{ flex: 1 }}
      />
      {filter && (
        <ActionIcon variant="subtle" size="sm" onClick={() => setFilter('')}>
          <IconX size={14} />
        </ActionIcon>
      )}
    </Group>
  );
}
