import { useState, useEffect } from 'react';

// 简单的A/B测试Hook
// 确保同一用户在同一测试下始终看到相同的变体
export function useABTest(testName, variants = ['A', 'B']) {
  const [variant, setVariant] = useState(null);

  useEffect(() => {
    // 从 localStorage 获取已分配的变体
    const storageKey = `ab_test_${testName}`;
    let assignedVariant = localStorage.getItem(storageKey);

    if (!assignedVariant || !variants.includes(assignedVariant)) {
      // 随机分配一个变体
      const randomIndex = Math.floor(Math.random() * variants.length);
      assignedVariant = variants[randomIndex];
      localStorage.setItem(storageKey, assignedVariant);
      
      // 模拟发送数据到分析服务
      console.log(`[A/B Test] User assigned to ${assignedVariant} for test: ${testName}`);
    }

    const t = setTimeout(() => setVariant(assignedVariant), 0)
    return () => clearTimeout(t)
  }, [testName, variants]);

  // 记录转化事件
  const trackConversion = (eventName) => {
    if (variant) {
      console.log(`[A/B Test Conversion] Test: ${testName}, Variant: ${variant}, Event: ${eventName}`);
      // 这里可以接入实际的埋点系统，如 Mixpanel, Google Analytics 等
    }
  };

  return { variant, trackConversion };
}
