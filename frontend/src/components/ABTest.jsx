import React from 'react';
import { useABTest } from '../hooks/useABTest';

export function ABTest({ name, variants, children }) {
  const variantKeys = Object.keys(variants);
  const { variant, trackConversion } = useABTest(name, variantKeys);

  if (!variant) {
    return null; // 或者返回一个骨架屏/Loading状态
  }

  const SelectedVariant = variants[variant];
  
  if (typeof SelectedVariant === 'function') {
    return <SelectedVariant trackConversion={trackConversion} />;
  }

  // 如果传递的是React元素，使用 cloneElement 注入 trackConversion 属性
  if (React.isValidElement(SelectedVariant)) {
    return React.cloneElement(SelectedVariant, { trackConversion });
  }

  return SelectedVariant;
}
