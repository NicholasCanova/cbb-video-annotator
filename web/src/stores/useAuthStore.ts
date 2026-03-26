import { create } from 'zustand';

interface AuthState {
  username: string | null;
  loading: boolean;
  setUsername: (u: string | null) => void;
  setLoading: (l: boolean) => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  username: null,
  loading: true, // starts true until we check session
  setUsername: (u) => set({ username: u }),
  setLoading: (l) => set({ loading: l }),
}));
