export function extractReportId(record) {
  if (!record) return null
  if (record.report_id != null) return record.report_id
  const meta = record.record_meta
  if (meta && meta.report_id != null) return meta.report_id
  return null
}

export function normalizeAttackRecord(record) {
  if (!record) return record
  const prompt = record.prompt || record.adversarial_prompt || record.original_prompt || ''
  return {
    ...record,
    prompt,
    original_prompt: record.original_prompt || prompt,
    adversarial_prompt: record.adversarial_prompt || null,
    report_id: extractReportId(record),
  }
}

export function normalizeDefenseRecord(record) {
  if (!record) return record
  const input = record.input || record.text || record.input_text || ''
  return {
    ...record,
    input,
    text: input,
    input_text: record.input_text || input,
    report_id: extractReportId(record),
  }
}

export function normalizeHistoryResponse(response, kind = 'attack') {
  const raw = response?.records ?? response?.data ?? (Array.isArray(response) ? response : [])
  const normalize = kind === 'attack' ? normalizeAttackRecord : normalizeDefenseRecord
  return raw.map(normalize)
}