type SystemRecommendationSectionProps = {
  onRequestConsultation: () => void;
};

const recommendationPaths = [
  {
    title: "Limited utilities",
    cue: "Start here when power or a backwash drain is unavailable.",
    description:
      "Harmony water conditioning featuring CLEAR Technology and cartridge filtration provides the starting point for this installation constraint.",
  },
  {
    title: "Salt-free conditioning",
    cue: "Start here when avoiding brine-tank salt is a priority.",
    description:
      "For homes with power and drain access, consider backwashing carbon filtration with Harmony conditioning as the starting point.",
  },
  {
    title: "Softened water",
    cue: "Start here when softened water is the specific goal.",
    description:
      "For homes with power and drain access, consider carbon filtration paired with a water softener as the starting point.",
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
            <p className="recommendation-cue">
              {path.cue}
            </p>
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
