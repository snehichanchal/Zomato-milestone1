"use client";

import { useState } from "react";
import styles from "./ErrorBanner.module.css";

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
}

export default function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  function handleDismiss() {
    setVisible(false);
    onDismiss?.();
  }

  return (
    <div className={styles.banner}>
      <div className={styles.content}>
        <span className={`material-symbols-outlined ${styles.icon}`}>error</span>
        <span className={styles.message}>{message}</span>
      </div>
      <button className={styles.close} onClick={handleDismiss} aria-label="Dismiss error">
        <span className="material-symbols-outlined">close</span>
      </button>
    </div>
  );
}
