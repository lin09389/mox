import { useMemo } from 'react'
import { useModels } from '../../hooks/queries'

const FALLBACK_MODELS = [
  'gpt-4',
  'gpt-3.5-turbo',
  'claude-3-opus-20240229',
  'abab2.5-chat',
  'llama3',
  'qwen3:4b',
  'qwen:4b',
  'gemma3:4b',
]

const CUSTOM_VALUE = '__custom__'

export default function ModelSelect({
  value = '',
  onChange,
  disabled = false,
  className = '',
  id,
  name,
}) {
  const { data: apiModels = [], isLoading } = useModels()

  const options = useMemo(() => {
    const merged = [...new Set([...FALLBACK_MODELS, ...apiModels, value].filter(Boolean))]
    return merged.sort((a, b) => a.localeCompare(b))
  }, [apiModels, value])

  const selectValue = value && options.includes(value) ? value : CUSTOM_VALUE
  const showCustomInput = selectValue === CUSTOM_VALUE

  return (
    <div className={`space-y-2 ${className}`}>
      <select
        id={id}
        name={name}
        className="input-field font-mono appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]"
        value={selectValue}
        onChange={(event) => {
          const next = event.target.value
          if (next === CUSTOM_VALUE) {
            onChange?.('')
            return
          }
          onChange?.(next)
        }}
        disabled={disabled || isLoading}
      >
        {options.map((model) => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
        <option value={CUSTOM_VALUE}>自定义模型…</option>
      </select>
      {showCustomInput && (
        <input
          className="input-field font-mono"
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          placeholder="输入模型 ID，如 llama3 / gpt-4"
          disabled={disabled}
        />
      )}
    </div>
  )
}