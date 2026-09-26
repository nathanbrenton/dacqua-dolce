type SystemRecommendationSectionProps = {
  onRequestConsultation: () => void;
};

const recommendationPaths = [
  {
    title: "Limited utilities",
    description:
      "For installations where electrical power or a backwash drain is unavailable, start with Harmony water conditioning and cartridge filtration.",
  },
  {
    title: "Salt-free conditioning",
    description:
      "For homes with power and drain access that prioritize carbon filtration and deposit mitigation without brine-tank salt, consider backwashing carbon filtration with Harmony conditioning.",
  },
  {
    title: "Softened water",
    description:
      "For homes with power and drain access that specifically want softened water, consider carbon filtration paired with a water softener.",
  },
] as const;

export function SystemRecommendationSection({
  onRequestConsultation,
}: SystemRecommendationSectionProps) {
  return (
    <section
      id="recommend-system"
      className="recommendation-section"
      aria-labelledby="recommend-system-heading"
    >
      <div className="section-heading">
        <p className="eyebrow">
          Recommend a System
        </p>

        <h2 id="recommend-system-heading">
          Start with the way your home uses water.
        </h2>

        <p>
          These starting points help narrow the conversation.
          Final system selection should account for source-water
          conditions, installation requirements, household demand,
          and verified product capabilities.
        </p>
      </div>

      <div className="recommendation-grid">
        {recommendationPaths.map((path) => (
          <article
            className="recommendation-card"
            key={path.title}
          >
            <h3>{path.title}</h3>
            <p>{path.description}</p>
          </article>
        ))}
      </div>

      <div className="recommendation-action">
        <p>
          Not sure which starting point fits your home?
        </p>
        <button
          type="button"
          className="primary-button"
          onClick={onRequestConsultation}
        >
          Help Me Choose
        </button>
      </div>
    </section>
  );
}
