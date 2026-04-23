import { create } from "zustand";
import { persist } from "zustand/middleware";

export const ACCENT_COLORS = [
  { name: "Синий",      value: "#1677ff", dark: "#3c8ffc" },
  { name: "Фиолетовый", value: "#722ed1", dark: "#9254de" },
  { name: "Зелёный",   value: "#52c41a", dark: "#73d13d" },
  { name: "Красный",   value: "#f5222d", dark: "#ff4d4f" },
  { name: "Оранжевый", value: "#fa8c16", dark: "#ffa940" },
  { name: "Бирюзовый", value: "#13c2c2", dark: "#36cfc9" },
  { name: "Розовый",   value: "#eb2f96", dark: "#f759ab" },
  { name: "Индиго",    value: "#2f54eb", dark: "#597ef7" },
];

interface ThemeState {
  isDark: boolean;
  accentColor: string;
  toggleDark: () => void;
  setAccentColor: (color: string) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      accentColor: "#1677ff",
      toggleDark: () => set((state) => ({ isDark: !state.isDark })),
      setAccentColor: (color) => set({ accentColor: color }),
    }),
    { name: "docflow-theme" }
  )
);
