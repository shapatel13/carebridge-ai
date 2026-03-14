import { create } from 'zustand'

interface ThemeState {
  isDark: boolean
  toggle: () => void
}

export const useTheme = create<ThemeState>((set) => ({
  isDark: localStorage.getItem('carebridge-dark') === 'true',
  toggle: () =>
    set((state) => {
      const next = !state.isDark
      localStorage.setItem('carebridge-dark', String(next))
      return { isDark: next }
    }),
}))
