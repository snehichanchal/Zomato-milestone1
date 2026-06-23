import Link from "next/link";
import styles from "./page.module.css";

const FEATURES = [
  {
    icon: "target",
    title: "Smart Filtering",
    description:
      "Narrow 10,000+ restaurants by location, budget, and cuisine in milliseconds.",
  },
  {
    icon: "auto_awesome",
    title: "AI Recommendations",
    description:
      "Our AI ranks and explains why each restaurant is perfect for you.",
  },
  {
    icon: "bolt",
    title: "Instant Results",
    description:
      "Powered by Groq for lightning-fast, intelligent responses.",
  },
];

const CUISINES = [
  "North Indian", "Chinese", "Italian", "Japanese", "Mexican",
  "Thai", "Continental", "Street Food", "Mughlai", "Biryani",
  "Korean", "Mediterranean", "South Indian", "Cafe", "Desserts",
];

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={`container ${styles.heroContent}`}>
          <h1 className={styles.headline}>
            Find Your <span className={styles.headlineAccent}>Perfect Table.</span>
          </h1>
          <p className={styles.subheadline}>
            AI-powered restaurant recommendations tailored to your taste,
            budget, and location.
          </p>
          <Link href="/discover" className={styles.cta}>
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
              auto_awesome
            </span>
            Discover Restaurants
          </Link>
        </div>
      </section>

      {/* Feature Cards */}
      <section className={`container ${styles.features}`}>
        {FEATURES.map((feature) => (
          <div key={feature.title} className={styles.featureCard}>
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 32, color: "var(--color-primary)" }}
            >
              {feature.icon}
            </span>
            <h3 className={styles.featureTitle}>{feature.title}</h3>
            <p className={styles.featureDesc}>{feature.description}</p>
          </div>
        ))}
      </section>

      {/* Cuisine Ticker */}
      <section className={styles.tickerSection}>
        <div className={styles.tickerTrack}>
          <div className={styles.tickerContent}>
            {[...CUISINES, ...CUISINES].map((cuisine, i) => (
              <span key={`${cuisine}-${i}`} className={styles.tickerChip}>
                {cuisine}
              </span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
