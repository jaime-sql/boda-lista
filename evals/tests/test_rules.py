import json

from evals.rules import extract_rsvp, extract_song, predict_item


def test_rsvp_yes_party_vegetarian_and_one_child():
    parsed = extract_rsvp("vamos 3, mi hijo es vegetariano", "es")
    assert parsed["attending"] == "yes"
    assert parsed["party_size"] == 3
    assert parsed["meal_restrictions"] == ["vegetarian"]
    assert parsed["kids_count"] == 1
    assert parsed["needs_ride"] is None
    assert parsed["ambiguous"] is False
    assert parsed["confidence"] == 0.90


def test_rsvp_decline_without_a_count():
    parsed = extract_rsvp("mi primo no puede ir", "es")
    assert parsed["attending"] == "no"
    assert parsed["party_size"] is None
    assert parsed["ambiguous"] is False
    assert parsed["confidence"] == 0.75


def test_rsvp_number_words_allergy_vegan_and_ride():
    parsed = extract_rsvp("tal vez somos dos, mi hija es vegana y alérgica a la nuez", "es")
    assert parsed["attending"] == "maybe"
    assert parsed["party_size"] == 2
    assert parsed["meal_restrictions"] == ["allergy:nuez", "vegan"]
    assert parsed["kids_count"] == 1

    confirmed = extract_rsvp(
        "Confirmado, seremos cinco, sin gluten, ocupamos ride y vienen 2 niños",
        "es",
    )
    assert confirmed["attending"] == "yes"
    assert confirmed["party_size"] == 5
    assert confirmed["meal_restrictions"] == ["gluten_free"]
    assert confirmed["kids_count"] == 2
    assert confirmed["needs_ride"] is True
    assert confirmed["confidence"] == 0.90


def test_rsvp_english_party_kids_and_no_kids():
    coming = extract_rsvp(
        "yes we'll be there, party of 4, two kids, gluten free, we need a ride",
        "en",
    )
    assert coming["attending"] == "yes"
    assert coming["party_size"] == 4
    assert coming["kids_count"] == 2
    assert coming["meal_restrictions"] == ["gluten_free"]
    assert coming["needs_ride"] is True

    declined = extract_rsvp("Sorry we can't make it, no kids", "en")
    assert declined["attending"] == "no"
    assert declined["kids_count"] == 0
    assert declined["party_size"] is None
    assert declined["confidence"] == 0.80


def test_rsvp_unresolved_and_contradiction():
    thanks = extract_rsvp("gracias", "es")
    assert thanks["ambiguous"] is True
    assert thanks["attending"] == "maybe"
    assert thanks["needs_ride"] is None
    assert thanks["confidence"] == 0.55

    conflict = extract_rsvp("vamos pero no podemos", "es")
    assert conflict["ambiguous"] is True
    assert conflict["attending"] == "maybe"

    partial = extract_rsvp("vamos 3, pero no te lo firme todavía", "es")
    assert partial["attending"] == "yes"
    assert partial["party_size"] == 3
    assert partial["ambiguous"] is True
    assert partial["needs_ride"] is None


def test_negated_vamos_is_a_decline():
    parsed = extract_rsvp("no vamos", "es")
    assert parsed["attending"] == "no"
    assert parsed["ambiguous"] is False


def test_rules_ignore_gold_fields():
    prediction = predict_item(
        {
            "id": "x",
            "task": "rsvp",
            "split": "dev",
            "lang": "es",
            "text": "vamos 2",
            "attending": "no",
            "party_size": 9,
            "meal_restrictions": ["vegan"],
            "kids_count": 4,
            "needs_ride": True,
            "ambiguous": True,
        }
    )
    output = json.loads(prediction["raw"])
    assert output["attending"] == "yes"
    assert output["party_size"] == 2
    assert output["ambiguous"] is False


def test_song_title_de_artist_and_artist_dash_title():
    parsed = extract_song("Vivir mi vida de Marc Anthony", "es")
    assert parsed["ambiguous"] is False
    assert parsed["title"] == "Vivir mi vida"
    assert parsed["artist"] == "Marc Anthony"
    assert parsed["confidence"] == 0.92

    dashed = extract_song("Marc Anthony - Vivir Mi Vida", "en")
    assert dashed["title"] == "Vivir Mi Vida"
    assert dashed["artist"] == "Marc Anthony"
    assert dashed["ambiguous"] is False

    english = extract_song("Dancing Queen by ABBA", "en")
    assert english["title"] == "Dancing Queen"
    assert english["artist"] == "ABBA"
    assert english["ambiguous"] is False


def test_vague_song_is_not_guessed():
    vague = extract_song("la de Marc Anthony que siempre ponen", "es")
    assert vague["ambiguous"] is True
    assert vague["title"] is None
    assert vague["artist"] == "Marc Anthony"
    assert vague["confidence"] == 0.80
    assert "vivir" not in json.dumps(vague).lower()

    upbeat = extract_song("something upbeat please", "en")
    assert upbeat["ambiguous"] is True
    assert upbeat["title"] is None
    assert upbeat["artist"] is None
    assert upbeat["energy"] == "dance"

    ballad = extract_song("una balada romántica", "es")
    assert ballad["ambiguous"] is True
    assert ballad["title"] is None
    assert ballad["energy"] == "slow"


def test_song_title_may_start_with_an_article():
    parsed = extract_song("El Cantante de Hector Lavoe", "es")
    assert parsed["ambiguous"] is False
    assert parsed["title"] == "El Cantante"
    assert parsed["artist"] == "Hector Lavoe"
