import { useState } from 'react';
import { Modal, Text, Stack, TextInput, Table, Accordion, Kbd, Group, List } from '@mantine/core';
import { HOTKEY_COMBOS } from '../../lib/hotkeyMap';

interface Props {
  opened: boolean;
  onClose: () => void;
}

// Flatten combos into a searchable list
const ALL_COMBOS = Object.entries(HOTKEY_COMBOS).flatMap(([first, seconds]) =>
  Object.entries(seconds).map(([second, label]) => ({
    keys: `Shift + ${first} + ${second}`,
    label,
    searchText: `${first} ${second} ${label}`.toLowerCase(),
  }))
);

export function HelpModal({ opened, onClose }: Props) {
  const [search, setSearch] = useState('');

  const filteredCombos = search
    ? ALL_COMBOS.filter((c) => c.searchText.includes(search.toLowerCase()))
    : ALL_COMBOS;

  return (
    <Modal opened={opened} onClose={onClose} title="Help" size="lg" centered>
      <Accordion defaultValue="instructions" variant="contained">
        <Accordion.Item value="instructions">
          <Accordion.Control>
            <Text fw={600}>Instructions</Text>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="lg">
              {/* Keyboard shortcuts table */}
              <Table verticalSpacing={6} horizontalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th w={200}>Action</Table.Th>
                    <Table.Th>Key</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Play / Pause</Text></Table.Td>
                    <Table.Td><Kbd>Space</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Step 1 frame</Text></Table.Td>
                    <Table.Td><Kbd>Left</Kbd> / <Kbd>Right</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Step 5 frames</Text></Table.Td>
                    <Table.Td><Kbd>Shift</Kbd> + <Kbd>Left</Kbd> / <Kbd>Right</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Step 10 frames</Text></Table.Td>
                    <Table.Td><Kbd>Ctrl</Kbd> + <Kbd>Left</Kbd> / <Kbd>Right</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Step 50 frames</Text></Table.Td>
                    <Table.Td><Kbd>Shift</Kbd> + <Kbd>Ctrl</Kbd> + <Kbd>Left</Kbd> / <Kbd>Right</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Speed 1x / 2x / 4x / 0.5x</Text></Table.Td>
                    <Table.Td><Kbd>A</Kbd> / <Kbd>Z</Kbd> / <Kbd>E</Kbd> / <Kbd>S</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">New annotation</Text></Table.Td>
                    <Table.Td><Kbd>Enter</Kbd> (while paused)</Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Delete annotation</Text></Table.Td>
                    <Table.Td><Kbd>Delete</Kbd> / <Kbd>Backspace</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Save edit</Text></Table.Td>
                    <Table.Td><Kbd>Enter</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Cancel edit</Text></Table.Td>
                    <Table.Td><Kbd>Escape</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Change label while editing</Text></Table.Td>
                    <Table.Td><Kbd>Ctrl</Kbd> + <Kbd>Enter</Kbd></Table.Td>
                  </Table.Tr>
                  <Table.Tr>
                    <Table.Td><Text size="sm">Save annotations to file</Text></Table.Td>
                    <Table.Td><Kbd>Ctrl</Kbd> + <Kbd>S</Kbd></Table.Td>
                  </Table.Tr>
                </Table.Tbody>
              </Table>

              {/* Workflow tips */}
              <div>
                <Text fw={600} mb={4}>Workflow</Text>
                <List size="sm" spacing={4}>
                  <List.Item>Click <b>Open Video</b> to load an MP4 file.</List.Item>
                  <List.Item>Click <b>Load JSON</b> to resume from a saved annotation file.</List.Item>
                  <List.Item>Navigate to a frame, press <Kbd>Enter</Kbd> or use a hotkey combo to annotate.</List.Item>
                  <List.Item>Click an event in the sidebar to edit its timestamp with arrow keys.</List.Item>
                  <List.Item>Annotations autosave to browser storage. Use <Kbd>Ctrl</Kbd>+<Kbd>S</Kbd> to download the JSON file.</List.Item>
                </List>
              </div>
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value="hotkeys">
          <Accordion.Control>
            <Text fw={600}>Action Creation Hotkeys</Text>
          </Accordion.Control>
          <Accordion.Panel>
            <Text size="sm" c="dimmed" mb="sm">
              Hold <Kbd>Shift</Kbd> and press two keys in sequence (within 1 second) to quickly create an annotation.
            </Text>
            <TextInput
              placeholder="Search hotkeys (e.g. drive, rebound, shift + d)"
              size="sm"
              mb="sm"
              value={search}
              onChange={(e) => setSearch(e.currentTarget.value)}
            />
            <Table highlightOnHover verticalSpacing={4} horizontalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th w={180}>Hotkey</Table.Th>
                  <Table.Th>Action</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredCombos.map((combo) => (
                  <Table.Tr key={combo.keys}>
                    <Table.Td>
                      <Group gap={4}>
                        {combo.keys.split(' + ').map((k, i) => (
                          <span key={i}>
                            {i > 0 && <Text span size="xs" c="dimmed"> + </Text>}
                            <Kbd size="sm">{k}</Kbd>
                          </span>
                        ))}
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{combo.label}</Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Modal>
  );
}
