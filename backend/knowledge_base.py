"""
knowledge_base.py

Feline Disease Diagnosis Expert System
Knowledge Base: FACTS + RULES + SOURCES

PROVENANCE (read this first)
----------------------------
* Symptom-to-disease associations (which symptoms belong to which disease),
  the differentiating clues between look-alike diseases, and the urgency /
  advice statements are taken from the published veterinary sources listed
  in SOURCES below. Each rule carries a "sources" list of source ids.
* The NUMBERS (certainty weights, boost/penalty amounts, thresholds, the
  50% confirmation threshold and the triage labels) are heuristic design
  parameters chosen by the knowledge engineer. The sources say WHICH
  symptoms matter, not how many "points" each is worth. Rules that are pure
  system-design parameters carry "design": True and no sources.

Prolog-style reading of the structures below:
    symptom(sneezing).                      -> SYMPTOMS
    disease(uri).                           -> DISEASES
    diagnose(Cat, uri, C) :- has(Cat, S)... -> DIAGNOSTIC_RULES (R1..R12)
    differentiate(...)                      -> DIFFERENTIATOR_RULES (D1..D8)
    urgency(Cat, Level) :- ...              -> URGENCY_RULES (U1..U12)

Sources were accessed on 28 September 2026.
"""

# =====================================================================
# SOURCES
# =====================================================================
SOURCES = {
    "S1":  {"title": "Respiratory Infections", "publisher": "Cornell Feline Health Center",
            "url": "https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/respiratory-infections"},
    "S2":  {"title": "Feline Upper Respiratory Infection", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/feline-upper-respiratory-infection"},
    "S3":  {"title": "Feline Panleukopenia", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/feline-panleukopenia"},
    "S4":  {"title": "Panleukopenia (fact sheet, PDF)", "publisher": "Animal Welfare League NSW",
            "url": "https://www.awlnsw.com.au/wp-content/uploads/2023/02/Panleukopenia.pdf"},
    "S5":  {"title": "Feline Panleukopenia: What you should know, and how to protect your cat", "publisher": "Anicira",
            "url": "https://anicira.org/resources/feline-panleukopenia-what-you-should-know-and-how-to-protect-your-cat/"},
    "S6":  {"title": "Feline Leukemia Virus (FeLV)", "publisher": "PetMD",
            "url": "https://www.petmd.com/cat/conditions/infectious-parasitic/c_ct_feline_leukemia"},
    "S7":  {"title": "Feline Leukemia Virus (FeLV) brochure - signs and who should be tested", "publisher": "Merck Animal Health",
            "url": "https://merck-animal-health-usa.com/offload-downloads/feline-leukemia-virus"},
    "S8":  {"title": "What is Feline Leukemia Virus (FeLV)?", "publisher": "catfriendly.com",
            "url": "https://catfriendly.com/?p=2549"},
    "S9":  {"title": "Ringworm in Cats (Dermatophytosis)", "publisher": "UC Davis School of Veterinary Medicine",
            "url": "https://healthtopics.vetmed.ucdavis.edu/node/1641"},
    "S10": {"title": "Ringworm in Cats", "publisher": "PetMD",
            "url": "https://petmd.com/cat/conditions/skin/ringworm-in-cats"},
    "S11": {"title": "Flea Allergy Dermatitis in Cats", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/allergy-flea-allergy-in-cats"},
    "S12": {"title": "Fleas of Cats (Pet Owner Version)", "publisher": "Merck Veterinary Manual",
            "url": "https://merckvetmanual.com/cat-owners/skin-disorders-of-cats/fleas-of-cats"},
    "S13": {"title": "Flea Allergy Dermatitis in Cats and Dogs", "publisher": "Vetstreet",
            "url": "https://www.vetstreet.com/care/flea-allergy-dermatitis-in-cats-and-dogs"},
    "S14": {"title": "Flea Control in Cats", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/flea-control-in-cats"},
    "S15": {"title": "Ear Mites in Cats: Causes, Symptoms & Treatment", "publisher": "Cats.com",
            "url": "https://cats.com/ear-mites-in-cats"},
    "S16": {"title": "What are Ear Mites in Cats: Signs, Causes, Treatment, Prevention and More", "publisher": "Vetic",
            "url": "https://www.vetic.in/blog/pet-health/what-are-ear-mites-in-cats-signs-causes-treatment-prevention-and-more/"},
    "S17": {"title": "Feline lower urinary tract disease (FLUTD)", "publisher": "American Veterinary Medical Association (AVMA)",
            "url": "https://www.avma.org/public/PetCare/Pages/FLUTD.aspx"},
    "S18": {"title": "Feline Lower Urinary Tract Disease (FLUTD)", "publisher": "PetMD",
            "url": "https://www.petmd.com/cat/conditions/urinary/feline-lower-urinary-tract-disease"},
    "S19": {"title": "Chronic Kidney Disease in Cats", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/kidney-failure-chronic-in-cats"},
    "S20": {"title": "Chronic kidney disease (CKD) in cats", "publisher": "International Cat Care",
            "url": "https://icatcare.org/articles/chronic-kidney-disease-ckd-in-cats"},
    "S21": {"title": "Diabetes Mellitus in Cats: Overview", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/diabetes-mellitus-in-cats"},
    "S22": {"title": "Gastrointestinal Parasites of Cats (brochure)", "publisher": "Cornell Feline Health Center",
            "url": "https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/gastrointestinal-parasites-cats-brochure"},
    "S23": {"title": "Gastrointestinal Parasites of Cats (Pet Owner Version)", "publisher": "MSD Veterinary Manual",
            "url": "https://www.msdvetmanual.com/cat-owners/digestive-disorders-of-cats/gastrointestinal-parasites-of-cats"},
    "S24": {"title": "How to Treat Your Cat for Intestinal Parasites", "publisher": "Hartz",
            "url": "https://www.hartz.com/how-to-treat-your-cat-for-intestinal-parasites/"},
    "S25": {"title": "Roundworms in Cats: Vet Answer", "publisher": "Catster",
            "url": "https://www.catster.com/ask-the-vet/roundworms-in-cats-vet-answer"},
    "S26": {"title": "Conjunctivitis in Cats", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/conjunctivitis-in-cats"},
    "S27": {"title": "Conjunctivitis in Cats", "publisher": "Catster (Ask the Vet)",
            "url": "https://catster.com/ask-the-vet/conjunctivitis-in-cats"},
    "S28": {"title": "Gastroenteritis in Cats", "publisher": "VCA Animal Hospitals",
            "url": "https://vcahospitals.com/know-your-pet/gastroenteritis-in-cats"},
    "S29": {"title": "What is gastroenteritis in cats?", "publisher": "Bow Wow Insurance (Australia)",
            "url": "https://bowwowinsurance.com.au/pet-care/diseases-conditions/what-is-gastroenteritis-in-cats/"},
}

# =====================================================================
# FACTS - Type 1: Symptoms
# Prolog equivalent:  symptom(sneezing).  symptom(nasal_discharge).  ...
# =====================================================================
SYMPTOMS = {
    "sneezing":                    "Cat is sneezing repeatedly",
    "nasal_discharge":             "Discharge (clear or cloudy) from the nose",
    "eye_discharge":               "Discharge (clear, cloudy, or bloody) from the eye(s)",
    "coughing":                    "Cat is coughing",
    "fever":                       "Cat's temperature is elevated",
    "lethargy":                    "Cat is unusually tired / low energy",
    "vomiting":                    "Cat is vomiting",
    "diarrhea":                    "Cat has loose/watery stool",
    "bloody_diarrhea":             "Diarrhea contains blood",
    "loss_of_appetite":            "Cat is eating less than usual / refusing food",
    "increased_appetite":          "Cat is eating more than usual",
    "weight_loss":                 "Noticeable, unintentional weight loss",
    "poor_coat":                   "Coat looks dull, dry, or unkempt",
    "pale_gums":                   "Gums appear pale rather than pink",
    "enlarged_lymph_nodes":        "Lymph nodes feel swollen",
    "recurring_infections":        "Cat keeps getting repeat infections/illnesses",
    "hair_loss":                   "Patchy or circular areas of hair loss",
    "scaly_skin":                  "Flaky, crusty, or scaly patches of skin",
    "itching":                     "Cat is scratching/licking/biting at itself often",
    "fleas_present":               "Fleas or flea dirt visible in the coat",
    "head_shaking":                "Cat shakes its head frequently",
    "ear_discharge":               "Dark, coffee-ground-like discharge in the ear",
    "straining_to_urinate":        "Cat strains or cries while trying to urinate",
    "blood_in_urine":              "Blood visible in the urine",
    "frequent_small_urination":    "Cat visits the litter box often but passes only small amounts",
    "urinating_outside_litterbox": "Cat is urinating outside the litter box",
    "abdominal_pain":              "Cat shows tenderness/pain when the belly is touched",
    "increased_thirst":            "Cat is drinking noticeably more water",
    "increased_urination":         "Cat is urinating more frequently / larger volumes",
    "worm_segments_in_stool":      "Rice-like or spaghetti-like worm segments visible in stool/fur",
    "bloated_abdomen":             "Abdomen looks swollen or pot-bellied",
    "redness_eyes":                "Eyes (conjunctiva) look red or swollen",
    "squinting":                   "Cat is squinting or keeping an eye partly closed",
}

# =====================================================================
# FACTS - Type 2: Diseases
# Prolog equivalent:  disease(uri).  disease(panleukopenia).  ...
#
# "urgency" is a triage label assigned by the knowledge engineer from the
# severity wording in the cited sources (for example "potentially fatal",
# "emergency"); it is a design parameter, not a quoted fact.
# "recommendation" is the general advice the sources give for the disease.
# =====================================================================
DISEASES = {
    "uri": {
        "name": "Upper Respiratory Infection (URI)",
        "category": "Respiratory",
        "urgency": "moderate",
        "recommendation": "See a vet for diagnosis and supportive care. URIs are highly contagious, "
                          "so keep the cat away from other cats; difficulty breathing needs prompt attention.",
        "sources": ["S1", "S2"],
    },
    "panleukopenia": {
        "name": "Feline Panleukopenia (Feline Distemper)",
        "category": "Viral / Systemic",
        "urgency": "emergency",
        "recommendation": "Contact a vet immediately. This is a highly contagious and potentially "
                          "fatal viral disease, especially in kittens and unvaccinated cats.",
        "sources": ["S3", "S4", "S5"],
    },
    "felv": {
        "name": "Feline Leukemia Virus (FeLV)",
        "category": "Viral / Immune",
        "urgency": "urgent",
        "recommendation": "See a vet for FeLV testing; it is diagnosed with a simple blood test.",
        "sources": ["S6", "S7"],
    },
    "ringworm": {
        "name": "Ringworm (Dermatophytosis)",
        "category": "Fungal / Skin",
        "urgency": "non_urgent",
        "recommendation": "See a vet to confirm (appearance alone is not reliable) and treat. "
                          "Ringworm is contagious to other animals and to people.",
        "sources": ["S9", "S10"],
    },
    "flea_allergy_dermatitis": {
        "name": "Flea Allergy Dermatitis",
        "category": "Parasitic / Skin",
        "urgency": "non_urgent",
        "recommendation": "Treat the cat and its environment for fleas and see a vet, "
                          "especially if scratching has caused skin sores or infection.",
        "sources": ["S11", "S12", "S14"],
    },
    "ear_mites": {
        "name": "Ear Mites (Otodectes cynotis)",
        "category": "Parasitic",
        "urgency": "non_urgent",
        "recommendation": "See a vet to confirm the mites (bacterial or yeast ear infections look "
                          "similar) and to get the right treatment.",
        "sources": ["S15", "S16"],
    },
    "flutd": {
        "name": "Feline Lower Urinary Tract Disease (FLUTD) / UTI",
        "category": "Urinary",
        "urgency": "urgent",
        "recommendation": "See a vet promptly. A cat that strains but passes little or no urine "
                          "may have a blocked urethra, which is an emergency.",
        "sources": ["S17", "S18"],
    },
    "ckd": {
        "name": "Chronic Kidney Disease (CKD)",
        "category": "Metabolic / Senior",
        "urgency": "urgent",
        "recommendation": "See a vet for blood and urine tests, which are used to diagnose CKD.",
        "sources": ["S19", "S20"],
    },
    "diabetes": {
        "name": "Diabetes Mellitus",
        "category": "Metabolic / Endocrine",
        "urgency": "urgent",
        "recommendation": "See a vet for blood and urine glucose testing to confirm the diagnosis.",
        "sources": ["S21"],
    },
    "intestinal_worms": {
        "name": "Intestinal Worms (Roundworms/Tapeworms)",
        "category": "Parasitic",
        "urgency": "non_urgent",
        "recommendation": "See a vet to confirm (usually by a stool test) and deworm. Flea control "
                          "helps prevent tapeworms, and hygiene matters because some worms can infect people.",
        "sources": ["S22", "S23"],
    },
    "conjunctivitis": {
        "name": "Conjunctivitis (isolated / non-URI)",
        "category": "Ophthalmic",
        "urgency": "moderate",
        "recommendation": "See a vet for an eye exam; the cause (infection, irritant, allergy) "
                          "decides the treatment.",
        "sources": ["S26", "S27"],
    },
    "gastroenteritis": {
        "name": "Gastroenteritis",
        "category": "Digestive",
        "urgency": "moderate",
        "recommendation": "See a vet if vomiting or diarrhea continues for more than 24 hours, "
                          "because dehydration can develop quickly.",
        "sources": ["S28"],
    },
}

# =====================================================================
# RULES - Type 1: Diagnostic rules (one per disease)
# Prolog equivalent:
#   diagnose(Cat, uri, Certainty) :- has_symptom(Cat, sneezing), ...
#
# "condition" = {symptom: weight}. WHICH symptoms are listed comes from the
# rule's sources; the weights (summing to 100 per rule) are heuristic
# design values. Certainty = sum of weights of the symptoms reported.
# =====================================================================
DIAGNOSTIC_RULES = [
    {
        "id": "R1", "disease": "uri",
        "condition": {"sneezing": 25, "nasal_discharge": 25, "eye_discharge": 15,
                      "coughing": 15, "fever": 10, "lethargy": 10},
        "explanation": "Upper respiratory infections cause sneezing, nose and eye discharge, "
                       "coughing, and less specific signs such as fever and lethargy.",
        "sources": ["S1", "S2"],
    },
    {
        "id": "R2", "disease": "panleukopenia",
        "condition": {"vomiting": 20, "bloody_diarrhea": 25, "fever": 20,
                      "lethargy": 20, "loss_of_appetite": 15},
        "explanation": "Panleukopenia typically shows frequent vomiting and diarrhea (which may "
                       "contain blood), fever, lethargy/depression and loss of appetite.",
        "sources": ["S3", "S4"],
    },
    {
        "id": "R3", "disease": "felv",
        "condition": {"weight_loss": 20, "poor_coat": 15, "pale_gums": 15,
                      "enlarged_lymph_nodes": 20, "recurring_infections": 20, "lethargy": 10},
        "explanation": "FeLV weakens the immune system: pale gums (anemia), weight loss, poor coat, "
                       "enlarged lymph nodes, recurring infections and lethargy are reported signs.",
        "sources": ["S6", "S7", "S8"],
    },
    {
        "id": "R4", "disease": "ringworm",
        "condition": {"hair_loss": 35, "scaly_skin": 30, "itching": 20, "poor_coat": 15},
        "explanation": "Ringworm usually causes circular patches of hair loss with scaly or crusty "
                       "skin, dull broken hair and sometimes excessive grooming or scratching.",
        "sources": ["S9", "S10"],
    },
    {
        "id": "R5", "disease": "flea_allergy_dermatitis",
        "condition": {"itching": 35, "fleas_present": 30, "hair_loss": 25, "scaly_skin": 10},
        "explanation": "Flea allergy dermatitis causes itching, hair loss and small scabs/crusts, "
                       "often with fleas or flea dirt visible in the coat.",
        "sources": ["S11", "S12", "S13"],
    },
    {
        "id": "R6", "disease": "ear_mites",
        "condition": {"head_shaking": 40, "ear_discharge": 40, "itching": 20},
        "explanation": "Ear mites cause head shaking, itchy ears and a dark, coffee-ground-like "
                       "discharge in the ear.",
        "sources": ["S15", "S16"],
    },
    {
        "id": "R7", "disease": "flutd",
        "condition": {"straining_to_urinate": 35, "blood_in_urine": 30,
                      "urinating_outside_litterbox": 20, "frequent_small_urination": 15},
        "explanation": "FLUTD major signs: straining to urinate, blood in the urine, urinating outside "
                       "the litter box, and frequent trips passing only small amounts.",
        "sources": ["S17", "S18"],
    },
    {
        "id": "R8", "disease": "ckd",
        "condition": {"increased_thirst": 25, "increased_urination": 25, "weight_loss": 20,
                      "poor_coat": 10, "loss_of_appetite": 10, "lethargy": 10},
        "explanation": "CKD causes increased thirst and urination, weight loss, poor coat, poor "
                       "appetite and lethargy, mainly in older cats.",
        "sources": ["S19", "S20"],
    },
    {
        "id": "R9", "disease": "diabetes",
        "condition": {"increased_thirst": 25, "increased_urination": 25,
                      "weight_loss": 25, "increased_appetite": 25},
        "explanation": "The four main signs of diabetes mellitus are increased thirst, increased "
                       "urination, weight loss and increased appetite.",
        "sources": ["S21"],
    },
    {
        "id": "R10", "disease": "intestinal_worms",
        "condition": {"worm_segments_in_stool": 40, "bloated_abdomen": 25,
                      "diarrhea": 15, "poor_coat": 10, "weight_loss": 10},
        "explanation": "Intestinal worms may be seen as worms or rice-like segments in stool, with a "
                       "pot-bellied look, diarrhea, dull coat and weight loss.",
        "sources": ["S22", "S23", "S24", "S25"],
    },
    {
        "id": "R11", "disease": "conjunctivitis",
        "condition": {"redness_eyes": 40, "eye_discharge": 35, "squinting": 25},
        "explanation": "Conjunctivitis shows red, swollen eye membranes, eye discharge and squinting.",
        "sources": ["S26", "S27"],
    },
    {
        "id": "R12", "disease": "gastroenteritis",
        "condition": {"vomiting": 30, "diarrhea": 30, "abdominal_pain": 20,
                      "loss_of_appetite": 10, "lethargy": 10},
        "explanation": "Gastroenteritis shows vomiting and diarrhea, abdominal tenderness, lethargy "
                       "and decreased appetite.",
        "sources": ["S28"],
    },
]

# =====================================================================
# RULES - Type 2: Differentiator rules
# Resolve overlap between diseases that share symptoms. The IF-part comes
# from comparing what the sources say about each disease (the "derivation"
# field states which sources are compared). The boost/penalty sizes are
# heuristic design values.
# =====================================================================
DIFFERENTIATOR_RULES = [
    {"id": "D1",
     "if_symptoms": ["weight_loss", "increased_appetite"],
     "boost": {"diabetes": 15}, "penalise": {"ckd": 15},
     "explanation": "Weight loss WITH increased appetite favours Diabetes over CKD.",
     "derivation": "S21 lists increased appetite as a main diabetes sign; S19/S20 describe poor "
                   "appetite in CKD.",
     "sources": ["S21", "S19", "S20"]},
    {"id": "D2",
     "if_symptoms": ["weight_loss", "loss_of_appetite"],
     "boost": {"ckd": 15}, "penalise": {"diabetes": 15},
     "explanation": "Weight loss WITH reduced appetite favours CKD over Diabetes.",
     "derivation": "S19/S20 describe poor appetite in CKD; S21 describes increased appetite in diabetes.",
     "sources": ["S19", "S20", "S21"]},
    {"id": "D3",
     "if_symptoms": ["eye_discharge", "sneezing"],
     "boost": {"uri": 15}, "penalise": {"conjunctivitis": 15},
     "explanation": "Eye discharge WITH sneezing points to URI (conjunctivitis is one of its signs).",
     "derivation": "S1/S2 list conjunctivitis and eye discharge as part of a URI together with sneezing.",
     "sources": ["S1", "S2"]},
    {"id": "D4",
     "if_symptoms": ["eye_discharge", "nasal_discharge"],
     "boost": {"uri": 10}, "penalise": {"conjunctivitis": 10},
     "explanation": "Eye discharge WITH nasal discharge points to URI rather than isolated conjunctivitis.",
     "derivation": "S1/S2 list nose and eye discharge together as URI signs.",
     "sources": ["S1", "S2"]},
    {"id": "D5",
     "if_symptoms": ["vomiting", "diarrhea", "bloody_diarrhea", "fever"],
     "boost": {"panleukopenia": 15}, "penalise": {"gastroenteritis": 15},
     "explanation": "Vomiting + bloody diarrhea + fever together favour Panleukopenia over simple Gastroenteritis.",
     "derivation": "S3/S4 list bloody diarrhea and fever for panleukopenia; S28 describes "
                   "gastroenteritis with a low-grade fever and as a diagnosis of exclusion.",
     "sources": ["S3", "S4", "S28"]},
    {"id": "D6",
     "if_symptoms": ["itching", "fleas_present"],
     "boost": {"flea_allergy_dermatitis": 10}, "penalise": {"ringworm": 10},
     "explanation": "Itching WITH visible fleas or flea dirt favours Flea Allergy Dermatitis over Ringworm.",
     "derivation": "S11/S13 list visible fleas/flea dirt as a sign of flea allergy dermatitis; S9 "
                   "describes ringworm as a fungal skin infection.",
     "sources": ["S11", "S13", "S9"]},
    {"id": "D7",
     "if_symptoms": ["hair_loss", "scaly_skin"],
     "boost": {"ringworm": 10}, "penalise": {"flea_allergy_dermatitis": 5},
     "explanation": "Circular hair loss with scaly skin is the classic Ringworm pattern.",
     "derivation": "S9/S10 describe circular hair loss with scaly or crusty skin as the usual ringworm signs.",
     "sources": ["S9", "S10"]},
    {"id": "D8",
     "if_symptoms": ["straining_to_urinate", "blood_in_urine", "urinating_outside_litterbox"],
     "boost": {"flutd": 15}, "penalise": {},
     "explanation": "Straining, blood in urine and urinating outside the litter box are all listed "
                    "as major FLUTD signs, so having them together strengthens the match.",
     "derivation": "S17 and S18 list all three among the main FLUTD signs.",
     "sources": ["S17", "S18"]},
]

# =====================================================================
# RULES - Type 3: Urgency and recommendation rules
# U1, U2 and U6-U12 are grounded in the cited sources.
# U3, U4, U5 are generic system-design rules about certainty levels
# ("design": True, no domain source).
# =====================================================================
URGENCY_RULES = [
    {"id": "U1",
     "if_symptoms": ["straining_to_urinate", "blood_in_urine"],
     "urgency": "emergency",
     "message": "Straining to urinate with blood in the urine can indicate FLUTD. A cat that strains "
                "but passes little or no urine may have a blocked urethra, which is an emergency - "
                "see a vet immediately.",
     "sources": ["S17", "S18"]},
    {"id": "U2",
     "if_symptoms": ["bloody_diarrhea", "fever", "lethargy"],
     "urgency": "emergency",
     "message": "Bloody diarrhea with fever and lethargy is consistent with panleukopenia, a highly "
                "contagious and potentially fatal disease - contact a vet immediately, especially "
                "for kittens.",
     "sources": ["S3", "S4", "S5", "S29"]},
    {"id": "U3", "design": True, "sources": [],
     "min_certainty": 70,
     "message": "High-confidence match - consult a vet to confirm the diagnosis and begin treatment."},
    {"id": "U4", "design": True, "sources": [],
     "max_certainty": 40,
     "message": "No strong match found - monitor the cat and consult a vet if symptoms persist or worsen."},
    {"id": "U5", "design": True, "sources": [],
     "tie_margin": 10,
     "message": "Two or more conditions scored closely - a vet exam and tests are needed to tell them apart."},
    {"id": "U6", "disease": "felv", "sources": ["S7"],
     "message": "Ask the vet about FeLV testing - sick cats should be tested (a simple blood test)."},
    {"id": "U7", "disease": "ckd", "sources": ["S19", "S20"],
     "message": "CKD becomes much more common as cats age - tell your vet the cat's age."},
    {"id": "U8", "disease": "ear_mites", "sources": ["S15", "S16"],
     "message": "Ear mites spread easily between pets - the vet may advise treating every pet in the household."},
    {"id": "U9", "disease": "flea_allergy_dermatitis", "sources": ["S14"],
     "message": "Treat the home as well as the cat (wash bedding, vacuum, treat the household) to stop re-infestation."},
    {"id": "U10", "disease": "ringworm", "sources": ["S9"],
     "message": "Ringworm can spread to people and other animals - wash hands after handling and limit contact."},
    {"id": "U11", "disease": "intestinal_worms", "sources": ["S22", "S24"],
     "message": "Some intestinal parasites can infect people - wash hands after handling the litter box."},
    {"id": "U12", "disease": "panleukopenia", "sources": ["S3", "S5"],
     "message": "Highly contagious - keep the cat away from other cats; the virus survives in the "
                "environment and needs strong disinfectant (for example 2% bleach)."},
]


def source_label(source_id):
    """Short human-readable label, e.g. 'S3 Feline Panleukopenia (VCA Animal Hospitals)'."""
    s = SOURCES[source_id]
    return f"{source_id} {s['title']} ({s['publisher']})"


def knowledge_base_stats():
    return {
        "symptom_facts": len(SYMPTOMS),
        "disease_facts": len(DISEASES),
        "source_facts": len(SOURCES),
        "total_facts": len(SYMPTOMS) + len(DISEASES),
        "diagnostic_rules": len(DIAGNOSTIC_RULES),
        "differentiator_rules": len(DIFFERENTIATOR_RULES),
        "urgency_rules": len(URGENCY_RULES),
        "total_rules": len(DIAGNOSTIC_RULES) + len(DIFFERENTIATOR_RULES) + len(URGENCY_RULES),
    }


def check_integrity():
    """Sanity checks: weights sum to 100, symptoms exist, cited source ids exist."""
    problems = []
    for r in DIAGNOSTIC_RULES:
        if sum(r["condition"].values()) != 100:
            problems.append(f"{r['id']}: weights sum to {sum(r['condition'].values())}, not 100")
        for s in r["condition"]:
            if s not in SYMPTOMS:
                problems.append(f"{r['id']}: unknown symptom {s}")
        if r["disease"] not in DISEASES:
            problems.append(f"{r['id']}: unknown disease {r['disease']}")
    for r in DIFFERENTIATOR_RULES:
        for s in r["if_symptoms"]:
            if s not in SYMPTOMS:
                problems.append(f"{r['id']}: unknown symptom {s}")
    for r in URGENCY_RULES:
        for s in r.get("if_symptoms", []):
            if s not in SYMPTOMS:
                problems.append(f"{r['id']}: unknown symptom {s}")
    for r in DIAGNOSTIC_RULES + DIFFERENTIATOR_RULES + URGENCY_RULES:
        if not r.get("sources") and not r.get("design"):
            problems.append(f"{r['id']}: no source and not marked as design rule")
        for sid in r.get("sources", []):
            if sid not in SOURCES:
                problems.append(f"{r['id']}: unknown source {sid}")
    for did, d in DISEASES.items():
        for sid in d["sources"]:
            if sid not in SOURCES:
                problems.append(f"{did}: unknown source {sid}")
    return problems


if __name__ == "__main__":
    print("Knowledge Base Statistics")
    print("-" * 30)
    for k, v in knowledge_base_stats().items():
        print(f"{k}: {v}")
    issues = check_integrity()
    print("\nIntegrity check:", "OK" if not issues else issues)