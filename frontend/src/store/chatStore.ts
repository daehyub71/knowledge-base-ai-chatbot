import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, ChatSession, Source } from '@/types';

interface ChatState {
  // Current session
  currentSession: ChatSession | null;
  sessions: ChatSession[];

  // UI state
  isLoading: boolean;
  error: string | null;

  // Actions
  createSession: () => void;
  addMessage: (role: 'user' | 'assistant', content: string, sources?: Source[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearCurrentSession: () => void;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
}

const generateId = () => Math.random().toString(36).substring(2, 15);

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      currentSession: null,
      sessions: [],
      isLoading: false,
      error: null,

      createSession: () => {
        const newSession: ChatSession = {
          id: generateId(),
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set((state) => ({
          currentSession: newSession,
          sessions: [newSession, ...state.sessions],
        }));
      },

      addMessage: (role, content, sources) => {
        const message: ChatMessage = {
          id: generateId(),
          role,
          content,
          timestamp: new Date(),
          sources,
        };

        set((state) => {
          if (!state.currentSession) return state;

          const updatedSession = {
            ...state.currentSession,
            messages: [...state.currentSession.messages, message],
            updatedAt: new Date(),
          };

          return {
            currentSession: updatedSession,
            sessions: state.sessions.map((s) =>
              s.id === updatedSession.id ? updatedSession : s
            ),
          };
        });
      },

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      clearCurrentSession: () => {
        const state = get();
        if (state.currentSession) {
          const clearedSession = {
            ...state.currentSession,
            messages: [],
            updatedAt: new Date(),
          };
          set({
            currentSession: clearedSession,
            sessions: state.sessions.map((s) =>
              s.id === clearedSession.id ? clearedSession : s
            ),
          });
        }
      },

      switchSession: (sessionId) => {
        const session = get().sessions.find((s) => s.id === sessionId);
        if (session) {
          set({ currentSession: session });
        }
      },

      deleteSession: (sessionId) => {
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== sessionId),
          currentSession:
            state.currentSession?.id === sessionId ? null : state.currentSession,
        }));
      },
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSession: state.currentSession,
      }),
    }
  )
);
