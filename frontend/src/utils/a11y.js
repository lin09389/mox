export const FOCUSABLE_ROW_CLASS =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 focus-visible:ring-inset'

export function handleRowKeyDown(event, onActivate) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    onActivate()
  }
}