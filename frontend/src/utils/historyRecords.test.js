import { describe, expect, it } from 'vitest'
import {
  extractReportId,
  normalizeAttackRecord,
  normalizeDefenseRecord,
  normalizeHistoryResponse,
} from './historyRecords'

describe('historyRecords', () => {
  it('normalizeAttackRecord maps prompt and report_id from record_meta', () => {
    const record = normalizeAttackRecord({
      id: 1,
      attack_type: 'jailbreak',
      original_prompt: 'hello',
      adversarial_prompt: 'evil hello',
      record_meta: { report_id: 99 },
    })
    expect(record.prompt).toBe('evil hello')
    expect(record.report_id).toBe(99)
  })

  it('normalizeDefenseRecord maps input_text and report_id', () => {
    const record = normalizeDefenseRecord({
      id: 2,
      defense_type: 'input_filter',
      input_text: 'scan me',
      report_id: 7,
    })
    expect(record.input).toBe('scan me')
    expect(extractReportId(record)).toBe(7)
  })

  it('normalizeHistoryResponse reads records array from API payload', () => {
    const items = normalizeHistoryResponse({
      records: [{ id: 3, original_prompt: 'x', attack_type: 'gcg' }],
    }, 'attack')
    expect(items).toHaveLength(1)
    expect(items[0].prompt).toBe('x')
  })
})