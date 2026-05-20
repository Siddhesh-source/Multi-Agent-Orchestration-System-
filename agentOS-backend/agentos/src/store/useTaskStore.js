import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

/**
 * useTaskStore — Zustand store for active task state
 *
 * Tracks the currently selected/active task, streaming events,
 * and submission state for the AgentOS UI.
 */
const useTaskStore = create(
    devtools(
        (set, get) => ({
            // ─── Active Task ─────────────────────────────────────────────
            activeTaskId: null,
            activeTask: null,

            setActiveTaskId: (id) => set({ activeTaskId: id }, false, 'setActiveTaskId'),
            setActiveTask: (task) => set({ activeTask: task }, false, 'setActiveTask'),
            clearActiveTask: () =>
                set({ activeTaskId: null, activeTask: null }, false, 'clearActiveTask'),

            // ─── Streaming Events ─────────────────────────────────────────
            events: [],

            appendEvent: (event) =>
                set(
                    (state) => ({ events: [...state.events, event] }),
                    false,
                    'appendEvent'
                ),

            clearEvents: () => set({ events: [] }, false, 'clearEvents'),

            // ─── Submission State ─────────────────────────────────────────
            isSubmitting: false,
            submitError: null,

            setSubmitting: (value) =>
                set({ isSubmitting: value }, false, 'setSubmitting'),
            setSubmitError: (error) =>
                set({ submitError: error }, false, 'setSubmitError'),
            clearSubmitError: () =>
                set({ submitError: null }, false, 'clearSubmitError'),
        }),
        { name: 'AgentOS:TaskStore' }
    )
)

export default useTaskStore
