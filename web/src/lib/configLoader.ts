import type { ClassesConfig } from '../types/config';

let cachedConfig: ClassesConfig | null = null;

export async function loadConfig(): Promise<ClassesConfig> {
  if (cachedConfig) return cachedConfig;
  const res = await fetch('/classes.json');
  cachedConfig = await res.json();
  return cachedConfig!;
}

export function getSubtypes(config: ClassesConfig, label: string): string[] {
  return config.subtypes[label] ?? config.subtypes['default'] ?? [];
}

export function getThirdLevel(config: ClassesConfig, label: string): string[] {
  return config.third[label] ?? config.third['default'] ?? [];
}
