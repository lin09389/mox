/** 与后端 mox/routes/audit.py _ACTION_LABELS 对齐 */
export const AUDIT_ACTION_OPTIONS = [
  { value: 'all', label: '全部操作类型' },
  { value: 'attack_run', label: '攻击测试' },
  { value: 'defense_detect', label: '防御检测' },
  { value: 'benchmark_run', label: '基准评测' },
  { value: 'report_query', label: '报告查询' },
  { value: 'report_download', label: '报告下载' },
  { value: 'report_create', label: '报告创建' },
  { value: 'report_delete', label: '报告删除' },
  { value: 'dataset_query', label: '数据集查询' },
  { value: 'dataset_upload', label: '数据集上传' },
  { value: 'dataset_delete', label: '数据集删除' },
  { value: 'template_query', label: '模板查询' },
  { value: 'template_create', label: '模板创建' },
  { value: 'template_update', label: '模板更新' },
  { value: 'template_delete', label: '模板删除' },
  { value: 'login', label: '用户登录' },
  { value: 'logout', label: '用户登出' },
  { value: 'register', label: '用户注册' },
  { value: 'audit_query', label: '审计查询' },
]

export const AUDIT_ACTION_LABELS = Object.fromEntries(
  AUDIT_ACTION_OPTIONS.filter((item) => item.value !== 'all').map((item) => [item.value, item.label])
)