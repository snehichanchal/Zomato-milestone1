import styles from "./LoadingState.module.css";

export default function LoadingState() {
  return (
    <div className={styles.container}>
      {/* Spinner + message */}
      <div className={styles.spinnerRow}>
        <span className={`material-symbols-outlined animate-spin ${styles.spinIcon}`}>
          sync
        </span>
        <span className={styles.message}>AI is ranking restaurants for you...</span>
      </div>

      {/* Skeleton cards */}
      {[1, 2, 3].map((i) => (
        <div key={i} className={styles.skeletonCard}>
          <div className={styles.skeletonContent}>
            <div className={styles.skeletonRow}>
              <div className={`skeleton ${styles.skeletonTitle}`} />
              <div className={`skeleton ${styles.skeletonBadge}`} />
            </div>
            <div className={styles.skeletonRow}>
              <div className={`skeleton ${styles.skeletonChip}`} />
              <div className={`skeleton ${styles.skeletonChip}`} />
            </div>
            <div className={`skeleton ${styles.skeletonCost}`} />
            <div className={`skeleton ${styles.skeletonExplanation}`} />
          </div>
        </div>
      ))}
    </div>
  );
}
