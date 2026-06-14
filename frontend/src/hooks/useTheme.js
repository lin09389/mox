import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const getSystemTheme = () => {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useTheme = create(
  persist(
    (set, get) => ({
      theme: 'system', // 'light' | 'dark' | 'system'
      resolvedTheme: 'light', // 'light' | 'dark' (actual applied theme)

      setTheme: (newTheme) => {
        const resolved = newTheme === 'system' ? getSystemTheme() : newTheme

        if (typeof window !== 'undefined') {
          const root = window.document.documentElement
          root.classList.remove('light', 'dark')
          root.classList.add(resolved)
          
          // Also set data-theme attribute for some third-party components if needed
          root.setAttribute('data-theme', resolved)
        }

        set({ theme: newTheme, resolvedTheme: resolved })
      },

      toggleTheme: () => {
        const { resolvedTheme } = get()
        const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark'
        get().setTheme(newTheme)
      },

      initTheme: () => {
        const { theme } = get()
        get().setTheme(theme)

        // Add event listener for system theme changes
        if (typeof window !== 'undefined') {
          const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
          const handleChange = () => {
            if (get().theme === 'system') {
              get().setTheme('system')
            }
          }
          mediaQuery.addEventListener('change', handleChange)
        }
      },
    }),
    {
      name: 'mox-theme-storage',
      // Only persist the theme preference, not the resolved theme
      partialize: (state) => ({ theme: state.theme }),
    }
  )
)
