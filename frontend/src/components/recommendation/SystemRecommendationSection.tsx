import {
  useMemo,
  useState,
} from "react";

import {
  type RecommendationContext,
} from "../../api/quotes";

type SystemRecommendationSectionProps = {
  onRequestConsultation: (
    context: RecommendationContext,
  ) => void;
};

type TriState = "yes" | "no" | "unsure";
type SourceWater = "municipal" | "well" | "unsure";
type TreatmentPreference =
  | "salt_free"
  | "softened"
  | "unsure";
type BathroomCount = RecommendationContext["bathrooms"];

type RecommendationResult = {
  title: string;
  description: string;
  humanReview: boolean;
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
      "When power and drain access are available, consider backwashing carbon filtration with Harmony conditioning as the starting point.",
  },
  {
    title: "Softened water",
    cue: "Start here when conventionally softened water is the specific goal.",
    description:
      "When power and drain access are available, consider backwashing carbon filtration with a water softener. Reverse osmosis is also included in this recommendation path.",
  },
] as const;

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{
    value: string;
    label: string;
  }>;
}) {
  return (
    <label className="recommendation-field">
      <span>{label}</span>
      <select
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

const yesNoUnsureOptions = [
  { value: "unsure", label: "Not sure" },
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
];

export function SystemRecommendationSection({
  onRequestConsultation,
}: SystemRecommendationSectionProps) {
  const [showGuidedRecommendation, setShowGuidedRecommendation] =
    useState(false);
  const [sourceWater, setSourceWater] =
    useState<SourceWater>("unsure");
  const [hardWaterSigns, setHardWaterSigns] =
    useState<TriState>("unsure");
  const [bathrooms, setBathrooms] =
    useState<BathroomCount>("unsure");
  const [qualityReportRead, setQualityReportRead] =
    useState<TriState>("unsure");
  const [chlorineSigns, setChlorineSigns] =
    useState<TriState>("unsure");
  const [ironManganeseConcern, setIronManganeseConcern] =
    useState<TriState>("unsure");
  const [existingEquipment, setExistingEquipment] =
    useState("");
  const [drainAvailable, setDrainAvailable] =
    useState<TriState>("unsure");
  const [electricalAvailable, setElectricalAvailable] =
    useState<TriState>("unsure");
  const [irrigationHoseBib, setIrrigationHoseBib] =
    useState<TriState>("unsure");
  const [poolAutofill, setPoolAutofill] =
    useState<TriState>("unsure");
  const [drinkingWaterRo, setDrinkingWaterRo] =
    useState<TriState>("unsure");
  const [waterTestResults, setWaterTestResults] =
    useState<TriState>("unsure");
  const [networkExperience, setNetworkExperience] =
    useState<TriState>("unsure");
  const [treatmentPreference, setTreatmentPreference] =
    useState<TreatmentPreference>("unsure");

  const recommendationContext = useMemo<RecommendationContext>(
    () => ({
      source_water: sourceWater,
      hard_water_signs: hardWaterSigns,
      bathrooms,
      water_quality_report_read: qualityReportRead,
      chlorine_chloramine_signs: chlorineSigns,
      iron_manganese_concerns: ironManganeseConcern,
      existing_equipment: existingEquipment.trim() || null,
      drain_available: drainAvailable,
      electrical_available: electricalAvailable,
      irrigation_hose_bib: irrigationHoseBib,
      pool_autofill: poolAutofill,
      drinking_water_ro: drinkingWaterRo,
      water_test_results: waterTestResults,
      water_filtration_network: networkExperience,
      treatment_preference: treatmentPreference,
    }),
    [
      sourceWater,
      hardWaterSigns,
      bathrooms,
      qualityReportRead,
      chlorineSigns,
      ironManganeseConcern,
      existingEquipment,
      drainAvailable,
      electricalAvailable,
      irrigationHoseBib,
      poolAutofill,
      drinkingWaterRo,
      waterTestResults,
      networkExperience,
      treatmentPreference,
    ],
  );

  const recommendationResult = useMemo<RecommendationResult>(() => {
    if (sourceWater === "well") {
      return {
        title: "Third-party water testing comes first.",
        description:
          "Well-water systems require third-party laboratory testing and human review before D'Acqua Dolce makes a system recommendation.",
        humanReview: true,
      };
    }

    if (sourceWater !== "municipal") {
      return {
        title: "Source water comes first.",
        description:
          "Confirm whether the property uses municipal or well water before relying on an automatic starting recommendation.",
        humanReview: true,
      };
    }

    if (electricalAvailable === "no" || drainAvailable === "no") {
      return {
        title: "Harmony + cartridge filtration",
        description:
          "With power or a backwash drain unavailable, Harmony conditioning with cartridge filtration is the confirmed starting path.",
        humanReview: false,
      };
    }

    if (
      electricalAvailable !== "yes"
      || drainAvailable !== "yes"
    ) {
      return {
        title: "Installation review recommended.",
        description:
          "Power and drain availability are needed before choosing between the confirmed backwashing treatment paths.",
        humanReview: true,
      };
    }

    if (treatmentPreference === "salt_free") {
      return {
        title: "Backwashing carbon + Harmony",
        description:
          "For municipal water with power and drain access, this is the confirmed starting path when carbon filtration and scale/deposit mitigation without salt are preferred.",
        humanReview: false,
      };
    }

    if (treatmentPreference === "softened") {
      return {
        title: "Backwashing carbon + water softener + reverse osmosis",
        description:
          "For municipal water with power and drain access, this is the confirmed starting path when conventionally softened water is preferred. Reverse osmosis is always included with the softener recommendation.",
        humanReview: false,
      };
    }

    return {
      title: "Expert review recommended.",
      description:
        "The confirmed starting paths depend on whether salt-free conditioning or conventionally softened water is preferred.",
      humanReview: true,
    };
  }, [
    sourceWater,
    electricalAvailable,
    drainAvailable,
    treatmentPreference,
  ]);

  return (
    <section
      id="recommend-system"
      className="recommendation-section"
      aria-labelledby="recommend-system-heading"
    >
      <div className="section-heading">
        <p className="eyebrow">Recommend a System</p>
        <h2 id="recommend-system-heading">
          Start with your water treatment goals.
        </h2>
        <p>
          These starting points help narrow the conversation. Final system selection should account for source-water conditions, installation requirements, water demand, and verified product capabilities.
        </p>
      </div>

      <div className="recommendation-grid">
        {recommendationPaths.map((path) => (
          <article className="recommendation-card" key={path.title}>
            <h3>{path.title}</h3>
            <p className="recommendation-cue">{path.cue}</p>
            <p>{path.description}</p>
          </article>
        ))}
      </div>

      <div
        className="recommendation-guidance-grid"
        aria-label="Installation and ownership guidance"
      >
        <aside className="recommendation-guidance-card" aria-labelledby="exterior-water-heading">
          <p className="eyebrow">Installation planning</p>
          <h3 id="exterior-water-heading">Treat water where treatment adds value.</h3>
          <p>
            Exterior irrigation and hose-bib lines should generally bypass treated-water equipment where appropriate, helping avoid unnecessary treatment of large exterior water demand. Final routing depends on the property and installation.
          </p>
        </aside>

        <aside className="recommendation-guidance-card" aria-labelledby="softener-ownership-heading">
          <p className="eyebrow">Softener ownership</p>
          <h3 id="softener-ownership-heading">Plan for simple routine checks.</h3>
          <p>
            For conventional softeners, inspect brine-tank salt about monthly and replenish it as needed. After a power loss, verify the valve time-of-day where applicable, and follow the instructions for the specific system.
          </p>
        </aside>

        <aside className="recommendation-guidance-card" aria-labelledby="cartridge-ownership-heading">
          <p className="eyebrow">Cartridge filtration</p>
          <h3 id="cartridge-ownership-heading">Plan for routine cartridge replacement.</h3>
          <p>
            For systems that use replaceable cartridges, plan to replace them at least every six months where applicable. Actual service life varies with source-water quality, micron rating, usage, and system conditions.
          </p>
        </aside>
      </div>

      <div className="recommendation-action recommendation-guided-entry">
        <div>
          <p className="eyebrow">Guided assistance</p>
          <p>
            A few additional questions can help narrow the starting point when you would like more guidance.
          </p>
        </div>
        <button
          type="button"
          className="secondary-button"
          aria-expanded={showGuidedRecommendation}
          aria-controls="guided-recommendation"
          onClick={() => {
            setShowGuidedRecommendation((current) => !current);
          }}
        >
          {showGuidedRecommendation
            ? "Hide guided recommendation"
            : "Start guided recommendation"}
        </button>
      </div>

      {showGuidedRecommendation ? (
        <div
          id="guided-recommendation"
          className="recommendation-builder"
          aria-labelledby="recommendation-builder-heading"
        >
        <div className="recommendation-builder-intro">
          <p className="eyebrow">Guided recommendation</p>
          <h3 id="recommendation-builder-heading">
            Build a starting point from what you already know.
          </h3>
          <p>
            Technical measurements are helpful when available, but they are not required to begin. Signs you have noticed and installation details are useful context too.
          </p>
        </div>

        <div className="recommendation-form-grid">
          <SelectField
            label="Source water"
            value={sourceWater}
            onChange={(value) => setSourceWater(value as SourceWater)}
            options={[
              { value: "unsure", label: "Not sure" },
              { value: "municipal", label: "Municipal water" },
              { value: "well", label: "Well water" },
            ]}
          />

          <SelectField
            label="Signs of hard water"
            value={hardWaterSigns}
            onChange={(value) => setHardWaterSigns(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Number of bathrooms"
            value={bathrooms}
            onChange={(value) => {
              setBathrooms(value as BathroomCount);
            }}
            options={[
              { value: "unsure", label: "Not sure" },
              { value: "1", label: "1" },
              { value: "2", label: "2" },
              { value: "3", label: "3" },
              { value: "4", label: "4" },
              { value: "5+", label: "5 or more" },
            ]}
          />

          <SelectField
            label="Read the water-quality report provided with your water bill"
            value={qualityReportRead}
            onChange={(value) => setQualityReportRead(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Noticed signs of chlorine or chloramine"
            value={chlorineSigns}
            onChange={(value) => setChlorineSigns(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Concerns about iron or manganese"
            value={ironManganeseConcern}
            onChange={(value) => setIronManganeseConcern(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Electrical power available near treatment equipment"
            value={electricalAvailable}
            onChange={(value) => setElectricalAvailable(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Drain available near treatment equipment"
            value={drainAvailable}
            onChange={(value) => setDrainAvailable(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Irrigation or hose-bib plumbing to consider"
            value={irrigationHoseBib}
            onChange={(value) => setIrrigationHoseBib(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Pool or autofill plumbing to consider"
            value={poolAutofill}
            onChange={(value) => setPoolAutofill(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Interested in drinking-water reverse osmosis"
            value={drinkingWaterRo}
            onChange={(value) => setDrinkingWaterRo(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Water test results available"
            value={waterTestResults}
            onChange={(value) => setWaterTestResults(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Neighbors, friends, or family use water filtration"
            value={networkExperience}
            onChange={(value) => setNetworkExperience(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Preferred treatment direction"
            value={treatmentPreference}
            onChange={(value) => setTreatmentPreference(value as TreatmentPreference)}
            options={[
              { value: "unsure", label: "Not sure yet" },
              { value: "salt_free", label: "Scale/deposit mitigation without salt" },
              { value: "softened", label: "Conventionally softened water" },
            ]}
          />

          <label className="recommendation-field recommendation-field-wide">
            <span>Existing water-treatment equipment</span>
            <textarea
              rows={3}
              maxLength={1000}
              value={existingEquipment}
              placeholder="Optional"
              onChange={(event) => {
                setExistingEquipment(event.target.value);
              }}
            />
          </label>
        </div>

        <aside
          className={
            "recommendation-result"
            + (recommendationResult.humanReview ? " is-review" : "")
          }
          aria-live="polite"
        >
          <p className="eyebrow">
            {recommendationResult.humanReview
              ? "Review path"
              : "Starting recommendation"}
          </p>
          <h3>{recommendationResult.title}</h3>
          <p>{recommendationResult.description}</p>
          {sourceWater === "well" ? (
            <p className="recommendation-result-note">
              A third-party laboratory test is mandatory before an automatic system recommendation is made for well water.
            </p>
          ) : null}
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              onRequestConsultation(recommendationContext);
            }}
          >
            Continue with an Expert
          </button>
        </aside>
      </div>
      ) : null}
    </section>
  );
}
