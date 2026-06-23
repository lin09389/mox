import {
  WorkspacePageShell,
  WorkspacePanelIntro,
  WorkspaceConfigPanel,
  WorkspaceReportPanel,
  WorkspaceTypeCard,
  WorkspaceRunButton,
  WorkspaceDemoBanner,
  WorkspaceReportEmpty,
  WorkspaceRiskGauge,
  WorkspaceLabHero,
  WorkspaceCodeBlock,
} from '../workspace'

/** 攻击工作台页面容器 → 统一 ws 主题栈 */
export function AttackPageShell({ children, className = '' }) {
  return (
    <WorkspacePageShell theme="attack" className={className}>
      {children}
    </WorkspacePageShell>
  )
}

export const AttackPanelIntro = WorkspacePanelIntro
export const AttackConfigPanel = WorkspaceConfigPanel
export const AttackReportPanel = WorkspaceReportPanel
export const AttackTypeCard = WorkspaceTypeCard
export const AttackRunButton = WorkspaceRunButton
export const AttackDemoBanner = WorkspaceDemoBanner
export const AttackReportEmpty = WorkspaceReportEmpty
export const AttackRiskGauge = WorkspaceRiskGauge
export const AttackLabHero = WorkspaceLabHero
export const AttackCodeBlock = WorkspaceCodeBlock