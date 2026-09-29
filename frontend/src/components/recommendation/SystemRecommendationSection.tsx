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
            Exterior irrigation, hose-bib, and pool-fill lines should generally bypass treated-water equipment when practical. Large pool-fill volumes can prematurely shorten filtration-media service life. Final routing still depends on the property and installation.
          </p>
        </aside>

        <aside className="recommendation-guidance-card" aria-labelledby="softener-ownership-heading">
          <p className="eyebrow">Softener ownership</p>
          <h3 id="softener-ownership-heading">Plan for simple routine checks.</h3>
          <p>
            For conventional softeners, inspect brine-tank salt about monthly and replenish it as needed. After a power interruption, verify valve time-of-day on conventional softeners and backwashing carbon filters where applicable. Follow the instructions for the specific equipment.
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
            Technical measurements are helpful when available, but they are not required to begin. These details help a D'Acqua Dolce employee confirm the right system before an early assisted sale.
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
            label="Signs of hard water"
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
            + (recommendationResult?.human_review ? " is-review" : "")
          }
          aria-live="polite"
        >
          <p className="eyebrow">
            {recommendationResult?.human_review
              ? "Staff review required"
              : "Starting recommendation"}
          </p>
          {recommendationResult ? (
            <>
              <h3>{recommendationResult.title}</h3>
              <p>{recommendationResult.description}</p>
            </>
          ) : recommendationError ? (
            <>
              <h3>Expert review recommended.</h3>
              <p>{recommendationError}</p>
            </>
          ) : (
            <>
              <h3>Reviewing your starting point…</h3>
              <p>Applying the current D'Acqua Dolce recommendation rules.</p>
            </>
          )}
          {recommendationResult?.requires_third_party_lab ? (
            <p className="recommendation-result-note">
              A third-party laboratory test and employee review are required before D'Acqua Dolce makes a final system recommendation for well water.
            </p>
          ) : null}
          {recommendationResult?.sizing ? (
            <p className="recommendation-result-note">
              {recommendationResult.sizing.status === "inputs_complete"
                ? "Sizing inputs are complete. Capacity selection will remain pending until verified sizing rules are available."
                : "Capacity sizing will also consider bathrooms, occupants, and water-service pipe size. Add any known sizing details to strengthen the consultation."}
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
