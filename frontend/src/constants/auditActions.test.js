import { describe, expect, it } from 'vitest'
import { AUDIT_ACTION_LABELS, AUDIT_ACTION_OPTIONS } from './auditActions'

describe('auditActions constants', () => {
  it('includes report lifecycle actions', () => {
    expect(AUDIT_ACTION_LABELS.report_create).toBe('报告创建')
    expect(AUDIT_ACTION_LABELS.report_delete).toBe('报告删除')
  })

  it('keeps all option as first entry', () => {
    expect(AUDIT_ACTION_OPTIONS[0]).toEqual({ value: 'all', label: '全部操作类型' })
  })
})