import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

// Symptoms are grouped on the frontend by id so the list fits one card
// without a long scroll. Any symptom id not listed here lands in "Other".
const CATEGORIES = [
  {
    key: "eyes",
    label: "Eyes & Nose",
    ids: ["sneezing", "nasal_discharge", "eye_discharge", "coughing", "redness_eyes", "squinting"],
  },
  {
    key: "tummy",
    label: "Tummy",
    ids: [
      "vomiting",
      "diarrhea",
      "bloody_diarrhea",
      "loss_of_appetite",
      "increased_appetite",
      "abdominal_pain",
      "bloated_abdomen",
      "worm_segments_in_stool",
    ],
  },
  {
    key: "skin",
    label: "Skin & Ears",
    ids: ["hair_loss", "scaly_skin", "itching", "fleas_present", "poor_coat", "head_shaking", "ear_discharge"],
  },
  {
    key: "bathroom",
    label: "Bathroom",
    ids: [
      "straining_to_urinate",
      "blood_in_urine",
      "frequent_small_urination",
      "urinating_outside_litterbox",
      "increased_thirst",
      "increased_urination",
    ],
  },
  {
    key: "general",
    label: "General",
    ids: ["fever", "lethargy", "weight_loss", "pale_gums", "enlarged_lymph_nodes", "recurring_infections"],
  },
];

const STOP_TEXT = {
  confirmed_early:
    "We stopped early because the match was already strong enough, so the remaining questions weren't needed.",
  ruled_out_early:
    "We stopped early because, even if every remaining answer were 'yes', the match could not reach the level needed.",
  all_answered: "We asked about every sign we look for.",
};

const URGENCY_TEXT = {
  emergency: "This may be an emergency. Contact a vet immediately.",
  urgent: "This should be seen by a vet soon.",
};

const levelFor = (certainty) => (certainty >= 70 ? "high" : certainty >= 40 ? "mid" : "low");
const signed = (n) => `${n > 0 ? "+" : "\u2212"}${Math.abs(n)}`;

// ---------- small SVG pieces ----------

function Paw({ className }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="currentColor" aria-hidden="true">
      <path d="M32 30C22 30 14 40 16 48C18 55 26 54 32 52C38 54 46 55 48 48C50 40 42 30 32 30Z" />
      <ellipse cx="13" cy="29" rx="6" ry="8" transform="rotate(-22 13 29)" />
      <ellipse cx="25" cy="15" rx="6" ry="8.5" transform="rotate(-8 25 15)" />
      <ellipse cx="39" cy="15" rx="6" ry="8.5" transform="rotate(8 39 15)" />
      <ellipse cx="51" cy="29" rx="6" ry="8" transform="rotate(22 51 29)" />
    </svg>
  );
}

function CatPeek({ className }) {
  return (
    <svg className={className} viewBox="0 0 120 90" aria-hidden="true">
      <polygon points="12,52 14,4 50,26" fill="#e9a91f" />
      <polygon points="108,52 106,4 70,26" fill="#e9a91f" />
      <polygon points="19,40 20,15 39,27" fill="#f6b8b0" />
      <polygon points="101,40 100,15 81,27" fill="#f6b8b0" />
      <ellipse cx="60" cy="58" rx="48" ry="36" fill="#e9a91f" />
      <path d="M52 26 L54 36 M60 24 L60 36 M68 26 L66 36" stroke="#c98a10" strokeWidth="3.5" strokeLinecap="round" />
      <ellipse cx="41" cy="52" rx="7" ry="9" fill="#182326" />
      <ellipse cx="79" cy="52" rx="7" ry="9" fill="#182326" />
      <circle cx="43.5" cy="48.5" r="2.6" fill="#fff" />
      <circle cx="81.5" cy="48.5" r="2.6" fill="#fff" />
      <polygon points="55,66 65,66 60,72" fill="#f08a8a" />
      <path d="M60 72 Q54 79 48 74 M60 72 Q66 79 72 74" stroke="#182326" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function CatSitting({ className }) {
  return (
    <svg className={className} viewBox="0 0 120 150" fill="currentColor" aria-hidden="true">
      <path d="M88 138C122 138 124 96 104 92" fill="none" stroke="currentColor" strokeWidth="9" strokeLinecap="round" />
      <path d="M30 142C22 100 34 74 60 74C86 74 98 100 90 142Z" />
      <circle cx="60" cy="52" r="26" />
      <polygon points="38,36 36,8 60,28" />
      <polygon points="82,36 84,8 60,28" />
    </svg>
  );
}

// ---------- background decoration (fixed, positions chosen once) ----------

const BUBBLES = [
  { size: 46, left: "6%", dur: 18, delay: 0 },
  { size: 24, left: "14%", dur: 14, delay: 4 },
  { size: 62, left: "24%", dur: 22, delay: 9 },
  { size: 30, left: "35%", dur: 16, delay: 2 },
  { size: 18, left: "46%", dur: 13, delay: 7 },
  { size: 54, left: "58%", dur: 21, delay: 1 },
  { size: 28, left: "68%", dur: 15, delay: 6 },
  { size: 40, left: "78%", dur: 19, delay: 11 },
  { size: 20, left: "86%", dur: 14, delay: 3 },
  { size: 58, left: "93%", dur: 23, delay: 8 },
];

const PAWS = [
  { top: "6%", left: "4%", size: 64, rot: -20, tone: "yellow" },
  { top: "14%", left: "88%", size: 56, rot: 24, tone: "teal" },
  { top: "38%", left: "2%", size: 44, rot: 12, tone: "teal" },
  { top: "52%", left: "92%", size: 70, rot: -14, tone: "yellow" },
  { top: "74%", left: "8%", size: 58, rot: 30, tone: "yellow" },
  { top: "84%", left: "80%", size: 48, rot: -26, tone: "teal" },
];

function Background() {
  return (
    <div className="bg" aria-hidden="true">
      {PAWS.map((p, i) => (
        <span
          key={`paw-${i}`}
          className={`bg-paw ${p.tone}`}
          style={{
            top: p.top,
            left: p.left,
            width: p.size,
            height: p.size,
            transform: `rotate(${p.rot}deg)`,
          }}
        >
          <Paw />
        </span>
      ))}

      {BUBBLES.map((b, i) => (
        <span
          key={`bubble-${i}`}
          className="bubble"
          style={{
            width: b.size,
            height: b.size,
            left: b.left,
            animationDuration: `${b.dur}s`,
            animationDelay: `-${b.delay}s`,
          }}
        />
      ))}

      <CatSitting className="bg-cat left" />
      <CatSitting className="bg-cat right" />
    </div>
  );
}

// ---------- explanation building blocks ----------

function SourceLinks({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="sources">
      Sources:{" "}
      {sources.map((s, i) => (
        <span key={s.id}>
          {i > 0 && ", "}
          <a href={s.url} target="_blank" rel="noreferrer" title={`${s.title} (${s.publisher})`}>
            {s.id}
          </a>
        </span>
      ))}
    </div>
  );
}

function SourceList({ groups }) {
  const unique = new Map();
  groups.flat().forEach((s) => unique.set(s.id, s));
  const list = [...unique.values()].sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)));
  if (list.length === 0) return null;
  return (
    <div className="source-list">
      <h4>Sources cited</h4>
      <ul>
        {list.map((s) => (
          <li key={s.id}>
            <strong>{s.id}</strong>{" "}
            <a href={s.url} target="_blank" rel="noreferrer">
              {s.title}
            </a>{" "}
            <span>({s.publisher})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Step({ number, title, children }) {
  return (
    <div className="chain-step">
      <div className="chain-marker">{number}</div>
      <div className="chain-body">
        <h4>{title}</h4>
        {children}
      </div>
    </div>
  );
}

function scoreBuild(item) {
  if (item.adjustments.length === 0) return `Match: ${item.certainty}%`;
  const changes = item.adjustments.map((a) => `${signed(a.delta)} (${a.rule_id})`).join(", ");
  return `Started at ${item.base_certainty}%, adjusted ${changes}, final ${item.certainty}%`;
}

// ---------- forward chaining: result + explanation ----------

function ForwardResult({ data }) {
  return (
    <>
      {URGENCY_TEXT[data.overall_urgency] && (
        <div className={`banner ${data.overall_urgency}`}>
          <strong>{URGENCY_TEXT[data.overall_urgency]}</strong>
        </div>
      )}

      {data.ranked.length === 0 ? (
        <div className="result-card">
          <div className="result-info">
            <p>No strong disease match was found.</p>
          </div>
        </div>
      ) : (
        data.ranked.map((item, index) => (
          <div
            className={`result-card ${index === 0 ? "top" : ""}`}
            key={item.disease_id}
            style={{ animationDelay: `${index * 70}ms` }}
          >
            <div className="result-rank">
              <Paw />
            </div>

            <div className="result-info">
              <div className="result-heading">
                <h3>{item.disease_name}</h3>
                {index === 0 && <span className="badge">Most likely</span>}
              </div>

              <div className="match">{item.certainty}% match</div>

              <div className="bar">
                <div className={`bar-fill ${levelFor(item.certainty)}`} style={{ width: `${item.certainty}%` }} />
              </div>
            </div>
          </div>
        ))
      )}

      {data.recommendations.length > 0 && (
        <div className="advice">
          <h4>Good to know</h4>
          <ul>
            {data.recommendations.map((r) => (
              <li key={r.rule_id}>{r.message}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

function ForwardExplanation({ data }) {
  const top3 = data.ranked.slice(0, 3);
  const top = data.ranked[0];
  const allSources = [
    ...top3.map((r) => r.sources),
    ...data.rules_applied.differentiator.map((d) => d.sources),
    ...data.recommendations.map((r) => r.sources),
  ];

  return (
    <div className="chain">
      <Step number="1" title="What you told us">
        <div className="chip-list">
          {data.input.map((s) => (
            <span className="mini-chip" key={s.id}>
              {s.description}
            </span>
          ))}
        </div>
      </Step>

      <Step number="2" title="What we noted">
        <p className="plain">Each symptom you picked was recorded as a known fact about your cat.</p>
        <pre className="facts-code">{data.facts.join("\n")}</pre>
      </Step>

      <Step number="3" title="What we checked">
        {data.rules_applied.diagnostic.map((r) => (
          <div className="rule-row" key={r.rule_id}>
            <span className="rule-id">{r.rule_id}</span>
            <div>
              <strong>{r.disease_name}</strong>
              <div className="rule-detail">
                Matched: {r.matched.map((m) => `${m.id.replace(/_/g, " ")} (+${m.weight})`).join(", ")}
                {" \u2192 "}
                {r.score}% match
              </div>
            </div>
          </div>
        ))}
        {data.rules_applied.differentiator.map((d) => (
          <div className="rule-row" key={d.rule_id}>
            <span className="rule-id diff">{d.rule_id}</span>
            <div>
              <strong>{d.explanation}</strong>
              <div className="rule-detail">
                {d.effects.map((e) => `${e.disease_name} ${signed(e.delta)}`).join(", ")}
              </div>
            </div>
          </div>
        ))}
      </Step>

      <Step number="4" title="How we weighed it">
        {top3.length === 0 && <p className="plain">Nothing matched the selected symptoms.</p>}
        {top3.map((item) => (
          <div className="reason-block" key={item.disease_id}>
            <strong>{item.disease_name}</strong>
            <div className="build">{scoreBuild(item)}</div>
            <p className="plain">{item.reasoning}</p>
            <SourceLinks sources={item.sources} />
          </div>
        ))}
      </Step>

      <Step number="5" title="Our conclusion">
        {top ? (
          <p className="plain">
            Most likely <strong>{top.disease_name}</strong> at a {top.certainty}% match. {top.recommendation}
          </p>
        ) : (
          <p className="plain">Nothing matched, so we can't suggest a cause from these symptoms.</p>
        )}
        {URGENCY_TEXT[data.overall_urgency] && (
          <div className={`banner ${data.overall_urgency}`}>{URGENCY_TEXT[data.overall_urgency]}</div>
        )}
        {data.recommendations.map((r) => (
          <div className="rule-row" key={r.rule_id}>
            <span className="rule-id adv">{r.rule_id}</span>
            <div>
              {r.message}
              {r.design ? <span className="tag-design">general guidance</span> : <SourceLinks sources={r.sources} />}
            </div>
          </div>
        ))}
      </Step>

      <SourceList groups={allSources} />
    </div>
  );
}

// ---------- backward chaining: result + explanation ----------

function BackwardResult({ data }) {
  return (
    <>
      <div className={`result-card ${data.conclusion ? "top" : ""}`}>
        <div className="result-rank">
          <Paw />
        </div>
        <div className="result-info">
          <div className="result-heading">
            <h3>{data.disease_name}</h3>
            <span className={`badge ${data.conclusion ? "" : "badge-muted"}`}>
              {data.conclusion ? "Likely match" : "Not a strong match"}
            </span>
          </div>
          <div className="match">
            {data.certainty}% match (a likely match starts at {data.threshold}%)
          </div>
          <div className="bar">
            <div className={`bar-fill ${levelFor(data.certainty)}`} style={{ width: `${data.certainty}%` }} />
          </div>
        </div>
      </div>

      {data.conclusion ? (
        <div className="banner routine">{data.recommendation}</div>
      ) : (
        <p className="plain">
          Your answers don't strongly match this illness. Try the symptom check, or check another illness.
        </p>
      )}
    </>
  );
}

function BackwardExplanation({ data }) {
  const askedIds = new Set(data.trace.map((t) => t.id));
  const notAsked = data.rule_condition.filter((c) => !askedIds.has(c.id));
  const yes = data.trace.filter((t) => t.answer).map((t) => t.weight);

  return (
    <div className="chain">
      <Step number="1" title="What we set out to check">
        <p className="plain">
          Whether your cat's problem could be <strong>{data.disease_name}</strong>.
        </p>
      </Step>

      <Step number="2" title="What we looked for">
        <div className="rule-row">
          <span className="rule-id">{data.rule_id}</span>
          <div>
            <strong>Signs of this illness, most important first</strong>
            <div className="chip-list">
              {data.rule_condition.map((c) => (
                <span className="mini-chip" key={c.id}>
                  {c.id.replace(/_/g, " ")}
                </span>
              ))}
            </div>
            <div className="rule-detail">It counts as a likely match once the match reaches {data.threshold}%.</div>
          </div>
        </div>
      </Step>

      <Step number="3" title="What you told us">
        {data.trace.map((t) => (
          <div className="rule-row" key={t.id}>
            <span className={`answer-pill ${t.answer ? "yes" : "no"}`}>{t.answer ? "Yes" : "No"}</span>
            <div>
              {t.description}
              <div className="rule-detail">{t.answer ? `+${t.weight} points` : "+0 points"}</div>
            </div>
          </div>
        ))}
        {notAsked.length > 0 && (
          <div className="rule-detail">
            Not needed: {notAsked.map((c) => c.id.replace(/_/g, " ")).join(", ")}
          </div>
        )}
      </Step>

      <Step number="4" title="How we weighed it">
        <div className="build">
          {yes.length ? yes.join(" + ") : "0"} = {data.certainty}% match
        </div>
        <p className="plain">{STOP_TEXT[data.stopped_reason]}</p>
        <p className="plain">{data.reasoning}</p>
        <SourceLinks sources={data.sources} />
      </Step>

      <Step number="5" title="Our conclusion">
        <p className="plain">
          <strong>{data.disease_name}</strong>: {data.conclusion ? "a likely match" : "not a strong match"} at{" "}
          {data.certainty}%. {data.conclusion ? data.recommendation : ""}
        </p>
      </Step>

      <SourceList groups={[data.sources]} />
    </div>
  );
}

// ---------- results popup (cat shaped) ----------

function ResultPopup({ popup, onClose, onRestart }) {
  const [tab, setTab] = useState("result");
  const forward = popup.kind === "forward";
  const data = popup.data;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="cat-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="result-title"
        onClick={(event) => event.stopPropagation()}
      >
        <span className="cat-ear left" />
        <span className="cat-ear right" />

        <div className="whiskers left" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
        <div className="whiskers right" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>

        <button className="modal-close" onClick={onClose} aria-label="Close results">
          &times;
        </button>

        <div className="cat-face" aria-hidden="true">
          <span className="eye" />
          <span className="nose" />
          <span className="eye" />
        </div>

        <h2 id="result-title">{forward ? "Diagnosis Results" : "Illness Check"}</h2>
        <p className="modal-sub">
          {forward
            ? `Based on the ${data.input.length} symptom${data.input.length === 1 ? "" : "s"} you selected`
            : `Checking for: ${data.disease_name}`}
        </p>

        <div className="modal-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={tab === "result"}
            className={`modal-tab ${tab === "result" ? "active" : ""}`}
            onClick={() => setTab("result")}
          >
            Result
          </button>
          <button
            role="tab"
            aria-selected={tab === "why"}
            className={`modal-tab ${tab === "why" ? "active" : ""}`}
            onClick={() => setTab("why")}
          >
            How it was decided
          </button>
        </div>

        <div className="modal-scroll">
          {tab === "result" && (forward ? <ForwardResult data={data} /> : <BackwardResult data={data} />)}
          {tab === "why" && (forward ? <ForwardExplanation data={data} /> : <BackwardExplanation data={data} />)}
        </div>

        <p className="disclaimer">A guide only. Please see a vet for a proper diagnosis.</p>

        <div className="modal-actions">
          <button className="secondary-button" onClick={onClose}>
            {forward ? "Back to symptoms" : "Close"}
          </button>
          <button className="primary-button" onClick={onRestart}>
            <Paw />
            {forward ? "Check another cat" : "Check another illness"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------- app ----------

function App() {
  const [mode, setMode] = useState("forward");

  // shared data from the backend
  const [symptoms, setSymptoms] = useState({});
  const [diseases, setDiseases] = useState([]);
  const [loadError, setLoadError] = useState(false);

  // forward chaining state
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [activeTab, setActiveTab] = useState("eyes");
  const [loading, setLoading] = useState(false);

  // backward chaining state
  const [goal, setGoal] = useState(null);
  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState(null);
  const [stepLoading, setStepLoading] = useState(false);

  // results popup: { kind: "forward" | "backward", data }
  const [popup, setPopup] = useState(null);

  // Get symptoms and diseases from the Python backend
  useEffect(() => {
    fetch(`${API}/symptoms`)
      .then((response) => response.json())
      .then((data) => setSymptoms(data))
      .catch((error) => {
        console.error("Error loading symptoms:", error);
        setLoadError(true);
      });

    fetch(`${API}/diseases`)
      .then((response) => response.json())
      .then((data) => setDiseases(data))
      .catch((error) => {
        console.error("Error loading diseases:", error);
        setLoadError(true);
      });
  }, []);

  // Close the results popup with Escape, and stop the page behind it scrolling
  const popupOpen = popup !== null;
  useEffect(() => {
    if (!popupOpen) return undefined;

    const onKey = (event) => {
      if (event.key === "Escape") setPopup(null);
    };
    window.addEventListener("keydown", onKey);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [popupOpen]);

  // Build the tab list from whatever symptoms the backend returned
  const knownIds = new Set(CATEGORIES.flatMap((category) => category.ids));
  const groups = CATEGORIES.map((category) => ({
    ...category,
    items: category.ids.filter((id) => id in symptoms),
  }));
  const otherIds = Object.keys(symptoms).filter((id) => !knownIds.has(id));
  if (otherIds.length > 0) {
    groups.push({ key: "other", label: "Other", ids: otherIds, items: otherIds });
  }
  const visibleGroups = groups.filter((group) => group.items.length > 0);
  const activeGroup = visibleGroups.find((group) => group.key === activeTab) || visibleGroups[0];

  // Select or unselect a symptom
  const toggleSymptom = (symptomId) => {
    setSelectedSymptoms((previous) => {
      if (previous.includes(symptomId)) {
        return previous.filter((symptom) => symptom !== symptomId);
      }

      return [...previous, symptomId];
    });
  };

  // Forward chaining: send selected symptoms to the Expert System
  const diagnose = async () => {
    if (selectedSymptoms.length === 0) {
      alert("Please select at least one symptom.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API}/diagnose`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedSymptoms),
      });

      if (!response.ok) {
        throw new Error("Diagnosis request failed");
      }

      const data = await response.json();

      setPopup({ kind: "forward", data });
    } catch (error) {
      console.error("Diagnosis error:", error);
      alert("Could not reach the diagnosis service.");
    } finally {
      setLoading(false);
    }
  };

  const startOver = () => {
    setSelectedSymptoms([]);
    setPopup(null);
    setActiveTab("eyes");
  };

  // Backward chaining: ask the server for the next question (or the final answer)
  const fetchStep = async (goalId, currentAnswers) => {
    setStepLoading(true);

    try {
      const response = await fetch(`${API}/backward/next`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal: goalId, answers: currentAnswers }),
      });

      if (!response.ok) {
        throw new Error("Backward chaining request failed");
      }

      const data = await response.json();

      setStep(data);
      if (data.done) {
        setPopup({ kind: "backward", data });
      }
    } catch (error) {
      console.error("Backward chaining error:", error);
      alert("Could not reach the diagnosis service.");
    } finally {
      setStepLoading(false);
    }
  };

  const startBackward = (goalId) => {
    setGoal(goalId);
    setAnswers({});
    setStep(null);
    fetchStep(goalId, {});
  };

  const answerQuestion = (value) => {
    const next = { ...answers, [step.next_symptom]: value };
    setAnswers(next);
    fetchStep(goal, next);
  };

  const resetBackward = () => {
    setGoal(null);
    setAnswers({});
    setStep(null);
    setPopup(null);
  };

  const restartFromPopup = () => {
    if (popup.kind === "forward") {
      startOver();
    } else {
      resetBackward();
    }
  };

  return (
    <div className="app">
      <Background />

      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="logo">
            <img src="/paw.svg" alt="Paw logo" />
          </div>

          <h1>
            <span className="title-yellow">Feline</span>
            <span className="title-teal">Health</span>
          </h1>
          <p className="subtitle">Happy Cat, Happy You</p>
          <p className="intro">
            {mode === "forward"
              ? "Select the symptoms you've noticed in your cat."
              : "Pick an illness you suspect and answer a few questions."}
          </p>
        </header>

        {/* Mode switch */}
        <div className="mode-switch" role="tablist" aria-label="Diagnosis mode">
          <button
            role="tab"
            aria-selected={mode === "forward"}
            className={`mode-button ${mode === "forward" ? "active" : ""}`}
            onClick={() => setMode("forward")}
          >
            <strong>Symptom check</strong>
            <span>Pick what you've noticed and see what it could be</span>
          </button>
          <button
            role="tab"
            aria-selected={mode === "backward"}
            className={`mode-button ${mode === "backward" ? "active" : ""}`}
            onClick={() => setMode("backward")}
          >
            <strong>Check an illness</strong>
            <span>Suspect something? Answer a few questions to check</span>
          </button>
        </div>

        <div className="card-wrap">
          <CatPeek className="cat-peek" />

          {/* Forward chaining card */}
          {mode === "forward" && (
            <div className="symptoms-card">
              <h2>What symptoms have you noticed?</h2>

              {loadError && (
                <p className="notice">
                  Can't reach the diagnosis service. Please start it, then refresh the page.
                </p>
              )}

              {!loadError && visibleGroups.length === 0 && <p className="notice">Loading symptoms...</p>}

              {visibleGroups.length > 0 && (
                <>
                  <div className="tabs" role="tablist" aria-label="Symptom groups">
                    {visibleGroups.map((group) => {
                      const count = group.items.filter((id) => selectedSymptoms.includes(id)).length;
                      return (
                        <button
                          key={group.key}
                          role="tab"
                          aria-selected={activeGroup.key === group.key}
                          className={`tab ${activeGroup.key === group.key ? "active" : ""}`}
                          onClick={() => setActiveTab(group.key)}
                        >
                          {group.label}
                          {count > 0 && <span className="tab-count">{count}</span>}
                        </button>
                      );
                    })}
                  </div>

                  <div className="symptoms-grid">
                    {activeGroup.items.map((id) => (
                      <label
                        key={id}
                        className={`symptom ${selectedSymptoms.includes(id) ? "selected" : ""}`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSymptoms.includes(id)}
                          onChange={() => toggleSymptom(id)}
                        />

                        <Paw className="symptom-paw" />

                        <span>{symptoms[id]}</span>
                      </label>
                    ))}
                  </div>
                </>
              )}

              <div className="selection-bar">
                <span>
                  {selectedSymptoms.length === 0
                    ? "No symptoms selected yet"
                    : `${selectedSymptoms.length} symptom${selectedSymptoms.length === 1 ? "" : "s"} selected`}
                </span>
                {selectedSymptoms.length > 0 && (
                  <button className="link-button" onClick={() => setSelectedSymptoms([])}>
                    Clear all
                  </button>
                )}
              </div>

              {/* Diagnose button */}
              <button
                className={`diagnose-button ${loading ? "is-loading" : ""}`}
                onClick={diagnose}
                disabled={loading}
              >
                <span className="diagnose-paw">
                  <Paw />
                </span>
                <span>{loading ? "Analyzing..." : "Diagnose Cat"}</span>
              </button>
            </div>
          )}

          {/* Backward chaining card */}
          {mode === "backward" && (
            <div className="symptoms-card">
              {/* 1. choose the hypothesis */}
              {!goal && (
                <>
                  <h2>Which illness do you suspect?</h2>

                  {loadError && (
                    <p className="notice">
                      Can't reach the diagnosis service. Please start it, then refresh the page.
                    </p>
                  )}
                  {!loadError && diseases.length === 0 && <p className="notice">Loading illnesses...</p>}

                  <div className="symptoms-grid disease-grid">
                    {diseases.map((d) => (
                      <button
                        key={d.disease_id}
                        className="symptom disease-card"
                        onClick={() => startBackward(d.disease_id)}
                      >
                        <Paw className="symptom-paw" />
                        <div className="disease-text">
                          <strong>{d.disease_name}</strong>
                          <small>{d.category}</small>
                        </div>
                      </button>
                    ))}
                  </div>
                </>
              )}

              {/* 2. answer one question at a time */}
              {goal && step && !step.done && (
                <>
                  <h2>Checking: {step.disease_name}</h2>

                  <div className="rule-preview">
                    <p>To check this, we'll ask about these signs, most important first:</p>
                    <div className="chip-list">
                      {step.rule_condition.map((c) => {
                        const state = c.id in answers ? (answers[c.id] ? "yes" : "no") : "pending";
                        return (
                          <span className={`rule-chip ${state}`} key={c.id}>
                            {c.id.replace(/_/g, " ")}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  <div className="question-card">
                    <p className="question-kicker">Question {step.asked + 1}</p>
                    <p className="question-text">{step.description}?</p>
                    <div className="answer-row">
                      <button className="answer-button yes" disabled={stepLoading} onClick={() => answerQuestion(true)}>
                        Yes
                      </button>
                      <button className="answer-button no" disabled={stepLoading} onClick={() => answerQuestion(false)}>
                        No
                      </button>
                    </div>
                  </div>

                  <div className="meter">
                    <div className="meter-label">
                      <span>Match so far: {step.certainty_so_far}%</span>
                      <span>Likely match at {step.threshold}%</span>
                    </div>
                    <div className="meter-track">
                      <div className="meter-fill" style={{ width: `${step.certainty_so_far}%` }} />
                      <div className="meter-mark" style={{ left: `${step.threshold}%` }} />
                    </div>
                  </div>

                  <div className="selection-bar">
                    <span />
                    <button className="link-button" onClick={resetBackward}>
                      Choose a different illness
                    </button>
                  </div>
                </>
              )}

              {goal && !step && <p className="notice">Thinking...</p>}

              {/* 3. finished */}
              {goal && step && step.done && (
                <>
                  <h2>{step.conclusion ? "Looks like a likely match" : "Not a strong match"}</h2>
                  <p className="notice">
                    {step.disease_name}: {step.certainty}% match after {step.trace.length} question
                    {step.trace.length === 1 ? "" : "s"}.
                  </p>
                  <div className="modal-actions">
                    <button className="secondary-button" onClick={() => setPopup({ kind: "backward", data: step })}>
                      Show the result
                    </button>
                    <button className="primary-button" onClick={resetBackward}>
                      <Paw />
                      Check another illness
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Results popup */}
      {popup && <ResultPopup popup={popup} onClose={() => setPopup(null)} onRestart={restartFromPopup} />}
    </div>
  );
}

export default App;