import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  evaluateRecommendation,
  type RecommendationContext,
  type RecommendationDecision,
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


const recommendationPaths = [
  {
    title: "Scale and spots, and you want soft water",
    cue: "Start with whole-home carbon filtration paired with a water softener.",
    description:
      "This path also includes reverse osmosis for drinking water. It needs an electrical outlet and a drain near where the system goes.",
  },
  {
    title: "Scale, but no salt",
    cue: "Start with whole-home carbon filtration paired with Harmony conditioning.",
    description:
      "Harmony featuring CLEAR Technology conditions without a brine tank. This path needs an electrical outlet and a drain near where the system goes.",
  },
  {
    title: "No outlet or drain near your water line",
    cue: "Start with Harmony conditioning paired with cartridge filtration.",
    description:
      "Some systems rinse themselves, so they need an electrical outlet and a drain nearby. If either one is missing, this is where to start.",
  },
] as const;

/**
 * Customer wording for each recommendation outcome. The API's own title and
 * description are written for staff and stored with the decision record, so
 * they stay unchanged; these replace them on the public page only.
 */
const CUSTOMER_RESULT_COPY: Record<
  RecommendationDecision["code"],
  { title: string; description: string }
> = {
  well_testing_required: {
    title: "A water test comes first.",
    description:
      "For well water, we need third-party laboratory results and a review by our team before we recommend a system.",
  },
  source_water_review: {
    title: "First, where does your water come from?",
    description:
      "Let us know whether your home is on city water or a private well, and we can suggest a starting point.",
  },
  limited_utilities: {
    title: "Harmony with cartridge filtration",
    description:
      "Without an electrical outlet or a drain near where the system would go, Harmony conditioning with cartridge filtration is the place to start. Our team confirms the fit with you before you buy.",
  },
  installation_review: {
    title: "Two details about your installation",
    description:
      "Is there an electrical outlet and a drain near where the system would go? Some systems rinse themselves and need both, so this decides which ones fit.",
  },
  salt_free: {
    title: "Whole-home carbon filtration + Harmony",
    description:
      "For city water with an outlet and a drain nearby, this is the starting point when you want carbon filtration and salt-free scale conditioning. Our team confirms the fit with you before you buy.",
  },
  softened_with_ro: {
    title: "Whole-home carbon filtration + water softener + reverse osmosis",
    description:
      "For city water with an outlet and a drain nearby, this is the starting point when you want softened water. Reverse osmosis is included in this path. Our team confirms the fit with you before you buy.",
  },
  treatment_preference_review: {
    title: "One more choice to make",
    description:
      "The starting point depends on whether you prefer salt-free conditioning or conventionally softened water. Not sure? Continue with an expert and we will talk it through.",
  },
};

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
  const [servicePostalCode, setServicePostalCode] =
    useState("");
  const [hardWaterSigns, setHardWaterSigns] =
    useState<TriState>("unsure");
  const [waterHardness, setWaterHardness] =
    useState("");
  const [bathrooms, setBathrooms] =
    useState<BathroomCount>("unsure");
  const [occupants, setOccupants] =
    useState("");
  const [waterServicePipeSize, setWaterServicePipeSize] =
    useState("");
  const [qualityReportRead, setQualityReportRead] =
    useState<TriState>("unsure");
  const [chlorineSigns, setChlorineSigns] =
    useState<TriState>("unsure");
  const [chlorineDetails, setChlorineDetails] =
    useState("");
  const [ironManganeseConcern, setIronManganeseConcern] =
    useState<TriState>("unsure");
  const [ironManganeseDetails, setIronManganeseDetails] =
    useState("");
  const [ph, setPh] =
    useState("");
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
  const [networkExperienceDetails, setNetworkExperienceDetails] =
    useState("");
  const [treatmentPreference, setTreatmentPreference] =
    useState<TreatmentPreference>("unsure");

  const recommendationContext = useMemo<RecommendationContext>(
    () => ({
      source_water: sourceWater,
      service_postal_code: servicePostalCode.trim() || null,
      hard_water_signs: hardWaterSigns,
      water_hardness: waterHardness.trim() || null,
      bathrooms,
      occupants: occupants === "" ? null : Number.parseInt(occupants, 10),
      water_service_pipe_size: waterServicePipeSize.trim() || null,
      water_quality_report_read: qualityReportRead,
      chlorine_chloramine_signs: chlorineSigns,
      chlorine_chloramine_details: chlorineDetails.trim() || null,
      iron_manganese_concerns: ironManganeseConcern,
      iron_manganese_details: ironManganeseDetails.trim() || null,
      ph: ph === "" ? null : Number.parseFloat(ph),
      existing_equipment: existingEquipment.trim() || null,
      drain_available: drainAvailable,
      electrical_available: electricalAvailable,
      irrigation_hose_bib: irrigationHoseBib,
      pool_autofill: poolAutofill,
      drinking_water_ro: drinkingWaterRo,
      water_test_results: waterTestResults,
      water_filtration_network: networkExperience,
      water_filtration_network_details:
        networkExperienceDetails.trim() || null,
      treatment_preference: treatmentPreference,
    }),
    [
      sourceWater,
      servicePostalCode,
      hardWaterSigns,
      waterHardness,
      bathrooms,
      occupants,
      waterServicePipeSize,
      qualityReportRead,
      chlorineSigns,
      chlorineDetails,
      ironManganeseConcern,
      ironManganeseDetails,
      ph,
      existingEquipment,
      drainAvailable,
      electricalAvailable,
      irrigationHoseBib,
      poolAutofill,
      drinkingWaterRo,
      waterTestResults,
      networkExperience,
      networkExperienceDetails,
      treatmentPreference,
    ],
  );

  const [recommendationResult, setRecommendationResult] =
    useState<RecommendationDecision | null>(null);
  const [recommendationError, setRecommendationError] =
    useState<string | null>(null);

  useEffect(() => {
    if (!showGuidedRecommendation) {
      return;
    }

    const controller = new AbortController();
    setRecommendationResult(null);
    setRecommendationError(null);

    const timer = window.setTimeout(() => {
      void evaluateRecommendation(
        recommendationContext,
        controller.signal,
      )
        .then((result) => {
          setRecommendationResult(result);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }

          setRecommendationResult(null);
          setRecommendationError(
            error instanceof Error
              ? error.message
              : "Recommendation review is temporarily unavailable.",
          );
        });
    }, 250);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [
    showGuidedRecommendation,
    recommendationContext,
  ]);

  return (
    <section
      id="recommend-system"
      className="recommendation-section"
      aria-labelledby="recommend-system-heading"
    >
      <div className="section-heading">
        <p className="eyebrow">Let us help you choose a system</p>
        <h2 id="recommend-system-heading">
          Start with the problem you want solved.
        </h2>
        <p>
          Three common situations, and where we would start. The right system also depends on your source water, your installation and how much water your home uses, so we confirm the details with you before anything is final.
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
            Where practical, irrigation, hose-bib and pool-fill lines should bypass treatment equipment. Filling a pool through the system can shorten the life of the filtration media. The final routing depends on your property and installation.
          </p>
        </aside>

        <aside className="recommendation-guidance-card" aria-labelledby="softener-ownership-heading">
          <p className="eyebrow">Softener ownership</p>
          <h3 id="softener-ownership-heading">Plan for simple routine checks.</h3>
          <p>
            With a conventional softener, check the brine-tank salt about once a month and top it up as needed. After a power outage, check the time of day on the control valve of a softener or self-rinsing carbon filter, where applicable. Always follow the instructions for your equipment.
          </p>
        </aside>

        <aside className="recommendation-guidance-card" aria-labelledby="cartridge-ownership-heading">
          <p className="eyebrow">Cartridge filtration</p>
          <h3 id="cartridge-ownership-heading">Plan for routine cartridge replacement.</h3>
          <p>
            If your system uses replaceable cartridges, plan to replace them at least every six months where applicable. Actual service life varies with your source water, the cartridge's micron rating, your usage and system conditions.
          </p>
        </aside>
      </div>

      <div className="recommendation-action recommendation-guided-entry">
        <div>
          <p className="eyebrow">Guided assistance</p>
          <p>
            Want a more specific starting point? Answer a few questions and we'll narrow it down.
          </p>
        </div>
        <button
          type="button"
          className="primary-button"
          aria-expanded={showGuidedRecommendation}
          aria-controls="guided-recommendation"
          onClick={() => {
            setShowGuidedRecommendation((current) => !current);
          }}
        >
          {showGuidedRecommendation
            ? "Hide guided questions"
            : "Help Me Choose"}
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
            Measurements help if you have them, but you don't need them to begin. Your answers help our team confirm the right system with you before you buy.
          </p>
        </div>

        <div className="recommendation-form-grid">
          <SelectField
            label="Where does your water come from?"
            value={sourceWater}
            onChange={(value) => setSourceWater(value as SourceWater)}
            options={[
              { value: "unsure", label: "Not sure" },
              { value: "municipal", label: "City (municipal) water" },
              { value: "well", label: "Private well" },
            ]}
          />

          <label className="recommendation-field">
            <span>Service ZIP code</span>
            <input
              type="text"
              inputMode="numeric"
              autoComplete="postal-code"
              maxLength={20}
              value={servicePostalCode}
              placeholder="If known"
              onChange={(event) => {
                setServicePostalCode(event.target.value);
              }}
            />
          </label>

          <SelectField
            label="Seeing scale, spots or other signs of hard water?"
            value={hardWaterSigns}
            onChange={(value) => setHardWaterSigns(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <label className="recommendation-field">
            <span>Known water hardness</span>
            <input
              type="text"
              maxLength={120}
              value={waterHardness}
              placeholder="Optional — include units if known"
              onChange={(event) => {
                setWaterHardness(event.target.value);
              }}
            />
          </label>

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

          <label className="recommendation-field">
            <span>Number of occupants</span>
            <input
              type="number"
              min="1"
              inputMode="numeric"
              value={occupants}
              placeholder="If known"
              onChange={(event) => {
                setOccupants(event.target.value);
              }}
            />
          </label>

          <label className="recommendation-field">
            <span>Water service pipe size</span>
            <input
              type="text"
              maxLength={120}
              value={waterServicePipeSize}
              placeholder="If known"
              onChange={(event) => {
                setWaterServicePipeSize(event.target.value);
              }}
            />
          </label>

          <SelectField
            label="Have you read the water-quality report from your water provider?"
            value={qualityReportRead}
            onChange={(value) => setQualityReportRead(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Noticed a chlorine taste or smell?"
            value={chlorineSigns}
            onChange={(value) => setChlorineSigns(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Rust-colored or dark staining? (iron or manganese)"
            value={ironManganeseConcern}
            onChange={(value) => setIronManganeseConcern(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <label className="recommendation-field">
            <span>Known chlorine / chloramine details</span>
            <input
              type="text"
              maxLength={240}
              value={chlorineDetails}
              placeholder="Optional — measurement, report note, or concern"
              onChange={(event) => {
                setChlorineDetails(event.target.value);
              }}
            />
          </label>

          <label className="recommendation-field">
            <span>Known iron / manganese details</span>
            <input
              type="text"
              maxLength={240}
              value={ironManganeseDetails}
              placeholder="Optional — measurement or report note"
              onChange={(event) => {
                setIronManganeseDetails(event.target.value);
              }}
            />
          </label>

          <label className="recommendation-field">
            <span>Known pH</span>
            <input
              type="number"
              min="0"
              max="14"
              step="0.1"
              inputMode="decimal"
              value={ph}
              placeholder="If known"
              onChange={(event) => {
                setPh(event.target.value);
              }}
            />
          </label>

          <SelectField
            label="Is there an electrical outlet near where the system would go?"
            value={electricalAvailable}
            onChange={(value) => setElectricalAvailable(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Is there a drain nearby? Some systems rinse themselves and need one."
            value={drainAvailable}
            onChange={(value) => setDrainAvailable(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Outdoor taps or irrigation on the same water line?"
            value={irrigationHoseBib}
            onChange={(value) => setIrrigationHoseBib(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="A pool or automatic pool fill?"
            value={poolAutofill}
            onChange={(value) => setPoolAutofill(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Interested in reverse osmosis for drinking water?"
            value={drinkingWaterRo}
            onChange={(value) => setDrinkingWaterRo(value as TriState)}
            options={yesNoUnsureOptions}
          />

          <SelectField
            label="Do you have water test results?"
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

          <label className="recommendation-field recommendation-field-wide">
            <span>What have you heard or noticed about their filtration?</span>
            <textarea
              rows={2}
              maxLength={1000}
              value={networkExperienceDetails}
              placeholder="Optional — what they use and why they chose filtration"
              onChange={(event) => {
                setNetworkExperienceDetails(event.target.value);
              }}
            />
          </label>

          <SelectField
            label="Which would you prefer?"
            value={treatmentPreference}
            onChange={(value) => setTreatmentPreference(value as TreatmentPreference)}
            options={[
              { value: "unsure", label: "Not sure yet" },
              { value: "salt_free", label: "Scale conditioning without salt" },
              { value: "softened", label: "Softened water (uses salt)" },
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
            + (recommendationResult?.human_review ? " is-review" : "")
          }
          aria-live="polite"
        >
          <p className="eyebrow">
            {recommendationResult?.human_review
              ? "Our team will review this"
              : "Starting recommendation"}
          </p>
          {recommendationResult ? (
            <>
              <h3>{CUSTOMER_RESULT_COPY[recommendationResult.code]?.title ?? recommendationResult.title}</h3>
              <p>{CUSTOMER_RESULT_COPY[recommendationResult.code]?.description ?? recommendationResult.description}</p>
            </>
          ) : recommendationError ? (
            <>
              <h3>Expert review recommended.</h3>
              <p>{recommendationError}</p>
            </>
          ) : (
            <>
              <h3>Working out your starting point…</h3>
              <p>This updates as you answer.</p>
            </>
          )}
          {recommendationResult?.requires_third_party_lab ? (
            <p className="recommendation-result-note">
              For well water, we need third-party laboratory results and a review by our team before we make a final recommendation.
            </p>
          ) : null}
          {recommendationResult?.sizing ? (
            <p className="recommendation-result-note">
              {recommendationResult.sizing.status === "inputs_complete"
                ? "We have what we need to size your system. Our team confirms the capacity with you."
                : "Sizing also depends on your bathrooms, household size and water-service pipe size. Add what you know and we'll confirm the rest with you."}
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
