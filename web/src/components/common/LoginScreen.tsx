import { useState } from 'react';
import { Center, Card, Stack, TextInput, PasswordInput, Button, Text, Title } from '@mantine/core';
import { login } from '../../lib/api';
import { useAuthStore } from '../../stores/useAuthStore';

export function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const setAuthUsername = useAuthStore((s) => s.setUsername);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(username, password);
      setAuthUsername(result.username);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Center h="100vh" bg="var(--mantine-color-body)">
      <Card shadow="md" radius="md" w={360} p="xl">
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <Title order={3} ta="center">CBB Video Annotator</Title>
            <Text size="sm" c="dimmed" ta="center">Sign in to start annotating</Text>

            {error && <Text c="red" size="sm" ta="center">{error}</Text>}

            <TextInput
              label="Username"
              placeholder="e.g. nick"
              value={username}
              onChange={(e) => setUsername(e.currentTarget.value)}
              required
              autoFocus
            />

            <PasswordInput
              label="Password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              required
            />

            <Button type="submit" fullWidth loading={loading}>
              Sign In
            </Button>
          </Stack>
        </form>
      </Card>
    </Center>
  );
}
