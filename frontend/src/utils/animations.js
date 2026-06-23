/**
 * Centralized Animation Configuration
 * 统一定义整站的 Framer Motion 动效变量，确保"极简科幻"体验的高度一致。
 */

const EASE_OUT_EXPO = [0.16, 1, 0.3, 1]
const EASE_OUT_QUART = [0.25, 1, 0.5, 1]

// 1. 页面级容器，处理子元素的依次出场 (Staggered Children)
export const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.04,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.04,
      staggerDirection: -1,
    },
  },
}

// 2. 细腻的卡片/列表项滑入 (Refined Fade & Slide Up)
export const itemVariants = {
  hidden: {
    opacity: 0,
    y: 14,
    scale: 0.985,
  },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 340,
      damping: 26,
      mass: 0.75,
    },
  },
  exit: {
    opacity: 0,
    y: -6,
    scale: 0.99,
    transition: {
      duration: 0.16,
      ease: EASE_OUT_QUART,
    },
  },
}

// 3. 页面顶层过渡切换 (Page Transitions for AnimatePresence)
export const pageVariants = {
  initial: {
    opacity: 0,
    y: 12,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.38,
      ease: EASE_OUT_EXPO,
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: {
      duration: 0.22,
      ease: EASE_OUT_EXPO,
    },
  },
}

// 4. Hub 标签页内容切换
export const tabPanelVariants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.32,
      ease: EASE_OUT_EXPO,
    },
  },
  exit: {
    opacity: 0,
    y: -6,
    transition: {
      duration: 0.18,
      ease: EASE_OUT_EXPO,
    },
  },
}

// 5. 页面标题入场
export const headerVariants = {
  hidden: {
    opacity: 0,
    y: 14,
  },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.42,
      ease: EASE_OUT_EXPO,
    },
  },
}

// 6. 微交互：悬停状态 (Micro-interaction: Hover Cards)
export const hoverCardVariants = {
  rest: {
    scale: 1,
    y: 0,
  },
  hover: {
    scale: 1.015,
    y: -4,
    transition: {
      type: 'spring',
      stiffness: 460,
      damping: 26,
      mass: 0.7,
    },
  },
}

// 6b. Workspace 类型卡片悬停
export const wsTypeCardVariants = {
  rest: { scale: 1, y: 0 },
  hover: {
    scale: 1.01,
    y: -2,
    transition: { type: 'spring', stiffness: 500, damping: 28 },
  },
  tap: { scale: 0.985, y: 0 },
}

// 7. 微交互：点击反馈 (Micro-interaction: Tap)
export const tapEffect = {
  scale: 0.98,
}

// 8. 抽屉侧滑弹簧
export const drawerVariants = {
  initial: { x: '100%' },
  animate: {
    x: 0,
    transition: {
      type: 'spring',
      stiffness: 380,
      damping: 32,
    },
  },
  exit: {
    x: '100%',
    transition: {
      duration: 0.28,
      ease: EASE_OUT_EXPO,
    },
  },
}

// 9. 认证页卡片入场
export const authCardVariants = {
  initial: {
    opacity: 0,
    scale: 0.94,
    y: 16,
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 280,
      damping: 24,
      mass: 0.85,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.97,
    y: -6,
    transition: {
      duration: 0.22,
      ease: EASE_OUT_EXPO,
    },
  },
}