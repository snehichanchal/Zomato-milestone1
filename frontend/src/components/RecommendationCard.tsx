import { RecommendationItem } from "@/lib/api";
import styles from "./RecommendationCard.module.css";

interface RecommendationCardProps {
  item: RecommendationItem;
  index: number; // for stagger animation
}

function getRankBadgeClass(rank: number): string {
  switch (rank) {
    case 1: return styles.rankGold;
    case 2: return styles.rankSilver;
    case 3: return styles.rankBronze;
    default: return styles.rankDefault;
  }
}

export default function RecommendationCard({ item, index }: RecommendationCardProps) {
  const cuisines = item.cuisine.split(",").map((c) => c.trim()).filter(Boolean);

  return (
    <article
      className={`${styles.card} animate-slide-up stagger-${Math.min(index + 1, 5)}`}
      style={{ opacity: 0 }} // start invisible for animation
    >
      {/* Rank Badge */}
      <div className={`${styles.rankBadge} ${getRankBadgeClass(item.rank)}`}>
        #{item.rank} Match
      </div>

      {/* Content */}
      <div className={styles.content}>
        <div className={styles.header}>
          <h3 className={styles.name}>{item.name}</h3>
          <div className={styles.ratingBadge}>
            {item.rating.toFixed(1)}
            <span className="material-symbols-outlined" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>
              star
            </span>
          </div>
        </div>

        {/* Cuisine chips + location */}
        <div className={styles.tags}>
          {cuisines.map((c) => (
            <span key={c} className={styles.chip}>{c}</span>
          ))}
        </div>

        {/* Cost */}
        <p className={styles.cost}>₹{item.estimated_cost.toLocaleString("en-IN")} for two</p>

        {/* AI Explanation */}
        <div className={styles.explanation}>
          &ldquo;{item.explanation}&rdquo;
        </div>
      </div>
    </article>
  );
}
