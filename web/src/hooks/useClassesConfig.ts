import { useState, useEffect } from 'react';
import { loadConfig } from '../lib/configLoader';
import type { ClassesConfig } from '../types/config';

/**
 * Shared hook for loading classes.json config.
 * Cached after first load — subsequent calls return immediately.
 */
export function useClassesConfig(): ClassesConfig | null {
  const [config, setConfig] = useState<ClassesConfig | null>(null);

  useEffect(() => {
    loadConfig().then(setConfig);
  }, []);

  return config;
}
