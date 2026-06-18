/**
 * Centralized Animation Configuration
 * 统一定义整站的 Framer Motion 动效变量，确保“极简科幻”体验的高度一致。
 */

// 1. 页面级容器，处理子元素的依次出场 (Staggered Children)
export const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
}

// 2. 细腻的卡片/列表项滑入 (Refined Fade & Slide Up)
export const itemVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.98,
    filter: 'blur(8px)',
  },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      type: 'spring',
      stiffness: 260,
      damping: 20,
      mass: 1,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.98,
    filter: 'blur(4px)',
    transition: {
      duration: 0.2,
      ease: 'easeIn',
    },
  },
}

// 3. 页面顶层过渡切换 (Page Transitions for AnimatePresence)
export const pageVariants = {
  initial: {
    opacity: 0,
    y: 15,
    filter: 'blur(8px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1], // 精调的自定义贝塞尔曲线，显得十分高级
    },
  },
  exit: {
    opacity: 0,
    y: -15,
    filter: 'blur(8px)',
    transition: {
      duration: 0.3,
      ease: [0.22, 1, 0.36, 1],
    },
  },
}

// 4. 微交互：悬停状态 (Micro-interaction: Hover Cards)
export const hoverCardVariants = {
  rest: {
    scale: 1,
    y: 0,
    boxShadow: '0 0 0 rgba(0,0,0,0)',
  },
  hover: {
    scale: 1.015,
    y: -4,
    boxShadow: '0 10px 30px -10px rgba(6, 182, 212, 0.15)', // 青色微弱发光
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 25,
    },
  },
}

// 5. 微交互：点击反馈 (Micro-interaction: Tap)
export const tapEffect = {
  scale: 0.98,
}
