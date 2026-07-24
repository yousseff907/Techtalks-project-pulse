import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
    accessToken: string | null;
    hasHydrated: boolean;

    setAccessToken: (token: string) => void;
    clearAccessToken: () => void;
    setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            accessToken: null,
            hasHydrated: false,

            setAccessToken: (token) => set({ accessToken: token }),
            clearAccessToken: () => set({ accessToken: null }),
            setHasHydrated: (value) => set({ hasHydrated: value }),
        }),
        {
            name: "project-pulse-auth",

            onRehydrateStorage: () => {
                return (state) => {
                    state?.setHasHydrated(true);
                };
            },
        }
    )
);