import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <span className={styles.brand}>Zomato AI</span>
        <span className={styles.copyright}>
          © {new Date().getFullYear()} Zomato AI Recommendations. All rights reserved.
        </span>
        <div className={styles.links}>
          <a href="#" className={styles.link}>Privacy Policy</a>
          <a href="#" className={styles.link}>Terms of Service</a>
          <a href="#" className={styles.link}>Contact Support</a>
        </div>
      </div>
    </footer>
  );
}
