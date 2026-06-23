import styles from "./EmptyState.module.css";

export default function EmptyState() {
  return (
    <div className={styles.container}>
      <div className={styles.iconCircle}>
        <span className="material-symbols-outlined" style={{ fontSize: 40, color: "var(--color-on-surface-variant)" }}>
          search_off
        </span>
      </div>
      <h3 className={styles.title}>No exact matches found</h3>
      <p className={styles.subtitle}>
        Your top picks will appear here once you adjust your preferences.
        Try broadening your budget or cuisine choices.
      </p>
    </div>
  );
}
