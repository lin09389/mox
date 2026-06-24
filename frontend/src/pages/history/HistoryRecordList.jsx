import { motion } from 'framer-motion'
import { History } from 'lucide-react'
import { TableMobileFallback, Skeleton } from '../../components/ui/AppFrame'
import { FOCUSABLE_ROW_CLASS, handleRowKeyDown } from '../../utils/a11y'
import {
  ATTACK_LABELS,
  DEFENSE_LABELS,
  badgeForAttackResult,
  badgeForDefenseResult,
  formatDate,
} from './constants'

export default function HistoryRecordList({
  isAttack,
  loading,
  filtered,
  searchTerm,
  selectedRecord,
  onSelect,
}) {
  return (
    <section className="card overflow-hidden">
      <div className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-5 py-4">
        <h2 className="text-lg font-bold font-display text-[var(--text-main)]">
          {isAttack ? '攻击记录列表' : '防御记录列表'}
        </h2>
        <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">
          {loading ? '正在同步数据...' : `当前共检索到 ${filtered.length} 条记录。`}
        </p>
      </div>

      {!loading && filtered.length > 0 && (
        <TableMobileFallback
          items={filtered}
          onItemActivate={onSelect}
          getCardClassName={(item) =>
            selectedRecord?.id === item.id ? 'border-l-2 border-l-cyan-500 bg-[var(--bg-glass-strong)]' : ''
          }
          renderTitle={(item) =>
            isAttack
              ? ATTACK_LABELS[item.attack_type] || item.attack_type
              : DEFENSE_LABELS[item.defense_type] || item.defense_type
          }
          renderMeta={(item) => (
            <>
              <p>模型: <span className="font-mono">{item.model_name}</span></p>
              <p>时间: <span className="font-mono">{formatDate(item.created_at)}</span></p>
              <p>
                {isAttack
                  ? `漏洞分值: ${Math.round((item.success_score || 0) * 100)}%`
                  : `判定置信度: ${Math.round((item.confidence || 0) * 100)}%`}
              </p>
            </>
          )}
          renderRight={(item) => (
            <span
              className={`badge ${
                isAttack
                  ? badgeForAttackResult(item.result)
                  : badgeForDefenseResult(item.is_malicious)
              }`}
            >
              {isAttack
                ? item.result === 'success'
                  ? '突破成功'
                  : '已拦截'
                : item.is_malicious
                  ? '发现威胁'
                  : '内容合规'}
            </span>
          )}
        />
      )}

      <div className="hidden md:block">
        {loading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex min-h-[300px] flex-col items-center justify-center px-6 text-center text-sm font-bold text-[var(--text-muted)] opacity-60">
            <History className="h-12 w-12 mb-4" />
            {searchTerm ? '没有找到匹配的记录。' : '当前页签还没有数据。'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[var(--text-main)]">
              <thead className="bg-[var(--bg-glass-strong)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-xs border-b border-[var(--border-glass)]">
                <tr>
                  <th className="px-6 py-4">时间戳</th>
                  <th className="px-6 py-4">{isAttack ? '攻击向量' : '防御切面'}</th>
                  <th className="px-6 py-4">目标模型</th>
                  <th className="px-6 py-4">裁决结果</th>
                  <th className="px-6 py-4">{isAttack ? '漏洞分值' : '判定置信度'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-glass)]">
                {filtered.map((item) => {
                  const typeLabel = isAttack
                    ? ATTACK_LABELS[item.attack_type] || item.attack_type
                    : DEFENSE_LABELS[item.defense_type] || item.defense_type
                  const score = isAttack ? item.success_score || 0 : item.confidence || 0
                  const isSelected = selectedRecord?.id === item.id

                  return (
                    <motion.tr
                      key={item.id}
                      tabIndex={0}
                      role="button"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`hover:bg-[var(--bg-glass)] transition-colors cursor-pointer ${FOCUSABLE_ROW_CLASS} ${
                        isSelected ? 'bg-[var(--bg-glass-strong)] border-l-2 border-l-cyan-500' : ''
                      }`}
                      onClick={() => onSelect(item)}
                      onKeyDown={(event) => handleRowKeyDown(event, () => onSelect(item))}
                    >
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-[var(--text-muted)]">
                        {formatDate(item.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">
                          {typeLabel}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-mono font-bold">{item.model_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`badge ${
                            isAttack
                              ? badgeForAttackResult(item.result)
                              : badgeForDefenseResult(item.is_malicious)
                          }`}
                        >
                          {isAttack
                            ? item.result === 'success'
                              ? '突破成功'
                              : '安全防御'
                            : item.is_malicious
                              ? '发现威胁'
                              : '内容合规'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="h-2 w-24 overflow-hidden rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)]">
                            <div
                              className={`h-full rounded-full transition-all duration-700 ease-out ${
                                score >= 0.6 ? 'bg-rose-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${Math.round(score * 100)}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-[var(--text-main)]">
                            {Math.round(score * 100)}%
                          </span>
                        </div>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}