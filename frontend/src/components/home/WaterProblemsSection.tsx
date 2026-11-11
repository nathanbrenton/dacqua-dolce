import { CONFIGURATION_FAMILIES } from "../catalog/productConfigurations";

type WaterProblemsSectionProps = {
  onNavigate: (path: string) => void;
  onTalkToExpert: () => void;
};

type WaterProblem = {
  family: string;
  title: string;
  /** What the customer notices at home, in their words. */
  symptom: string;
  /** The kind of system that addresses it. */
  need: string;
  /** What the D'Acqua Dolce system does; restates approved catalog copy only. */
  answer: string;
};

/**
 * Problem-first entry to the catalog. Each answer repeats a statement the
 * catalog already makes for that family; no new performance claim is added.
 */
const WATER_PROBLEMS: readonly WaterProblem[] = [
  {
    family: "Refine",
    title: "Scale, spots and stubborn cleaning",
    symptom:
      "White crust on taps and showerheads, spotted glasses and soap that is hard to rinse are signs of hard water. The same minerals build up inside pipes and water heaters.",
    need: "You need a water softener.",
    answer:
      "Refine is designed to address the hardness minerals behind scale and spotting.",
  },
  {
    family: "Essence",
    title: "Water that tastes or smells off",
    symptom:
      "A chlorine taste in the glass, or an odor at the tap and in the shower.",
    need: "You need whole-home carbon filtration.",
    answer:
      "Essence is intended to help address unwanted tastes and odors at every tap.",
  },
  {
    family: "Essence",
    title: "Laundry that smells after a wash",
    symptom:
      "Clothes and towels come out of the machine with an odor, even when they are clean.",
    need: "You need a carbon filter.",
    // Owner direction, 2026-11-10: carbon captures chemicals and sulfides.
    answer:
      "Essence carbon filtration is intended to capture the chemicals and sulfides that can leave an odor in your water and your wash.",
  },
  {
    family: "Harmony",
    title: "Scale, but you would rather not add salt",
    symptom:
      "You want to deal with scale without a brine tank and bags of salt to carry.",
    need: "You need salt-free conditioning.",
    answer:
      "Harmony with CLEAR Technology conditions hardness minerals so they are less likely to adhere as scale.",
  },
  {
    family: "Origin",
    title: "Tap water you would rather not drink",
    symptom:
      "You buy bottled water, or you want better water for drinking, coffee and cooking.",
    need: "You need reverse osmosis where you drink.",
    answer:
      "Origin filters drinking and cooking water at the point of use.",
  },
];

function familyPath(familyName: string): string | null {
  const family = CONFIGURATION_FAMILIES.find(
    (entry) => entry.name === familyName,
  );

  return family === undefined
    ? null
    : `/systems/${family.defaultSku.toLowerCase()}`;
}

export function WaterProblemsSection({
  onNavigate,
  onTalkToExpert,
}: WaterProblemsSectionProps) {
  return (
    <section
      id="water-problems"
      className="problems-section"
      aria-labelledby="water-problems-heading"
    >
      <div className="section-heading">
        <p className="eyebrow">Start with the problem</p>

        <h2 id="water-problems-heading">
          What would you like to fix about your water?
        </h2>

        <p>
          Most people come to us with one of these. Find yours and see what
          solves it.
        </p>
      </div>

      <div className="problem-grid">
        {WATER_PROBLEMS.map((problem) => {
          const path = familyPath(problem.family);

          return (
            <article className="problem-card" key={problem.title}>
              <h3>{problem.title}</h3>
              <p>{problem.symptom}</p>

              <div className="problem-answer">
                <p className="problem-need">{problem.need}</p>
                <p>{problem.answer}</p>
              </div>

              {path !== null ? (
                <a
                  className="problem-link"
                  href={path}
                  onClick={(event) => {
                    event.preventDefault();
                    onNavigate(path);
                  }}
                >
                  See {problem.family}
                  <span aria-hidden="true"> →</span>
                </a>
              ) : null}
            </article>
          );
        })}

        <article className="problem-card problem-card-help">
          <h3>Something else, or not sure what you have?</h3>
          <p>
            Staining, cloudy water, or water you simply do not trust: tell us
            what you are seeing and we will help you work out what is going
            on.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={onTalkToExpert}
          >
            We&apos;re here to help
          </button>
        </article>
      </div>
    </section>
  );
}
