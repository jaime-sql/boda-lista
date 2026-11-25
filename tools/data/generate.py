#!/usr/bin/env python3
"""Build the Boda Lista synthetic wedding data pack.

Stdlib only. Fixed seed. All names, contacts and venues are fictional.
The 300 hand-checked RSVP replies are the test set only.

Dev and stress rows are template-generated, not modeled. From the repo root:

  python tools/data/generate_dev.py

That command uses seed 20261124 and does not call Modal. `--generate-modal`
stays a no-op because the Modal token is expired. Generated rows must never
use split=test and must not reuse test ids or texts.

Usage:
  python generate.py
  python validate.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from rsvp_bank import RECORDS as RSVP_RECORDS

SEED = 20261122
ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
UNKNOWN_ANSWER = "No tengo esa información, pregúntale a los novios"

# Blocked surnames (avoid real-family names from the owner's circle / real forms).
BLOCKED_SURNAMES = {"García", "Garcia", "Morán", "Moran", "Ramírez", "Ramirez"}

FIRST_NAMES_F = [
    "Ana", "Sofía", "Camila", "Valeria", "Fernanda", "Daniela", "Isabel", "Paola",
    "Andrea", "Fabiola", "Alejandra", "Karla", "Michelle", "Gabriela", "Patricia",
    "Rosa", "Carmen", "Teresa", "Claudia", "Liliana", "Marisol", "Yesenia",
    "Rebeca", "Lucia", "Elena", "Mónica", "Verónica", "Cecilia", "Natalia",
    "Ximena", "Adriana", "Beatriz", "Carolina", "Diana", "Evelyn", "Gloria",
    "Helena", "Inés", "Jimena", "Katrina", "Lorena", "Marta", "Nadia", "Olga",
    "Pilar", "Renata", "Sandra", "Tania", "Úrsula", "Vanessa", "Wendy", "Yolanda",
]
FIRST_NAMES_M = [
    "José", "Carlos", "Luis", "Diego", "Andrés", "Mateo", "Fernando", "Ricardo",
    "Óscar", "Roberto", "Héctor", "Eduardo", "Javier", "Mario", "Ernesto",
    "Rafael", "Miguel", "Francisco", "Alberto", "Bruno", "César", "Daniel",
    "Emilio", "Felipe", "Gustavo", "Hugo", "Iván", "Julián", "Kevin", "Leonardo",
    "Manuel", "Nicolás", "Omar", "Pablo", "Raúl", "Sergio", "Tomás", "Ulises",
    "Víctor", "William", "Xavier", "Yuri", "Zacarías", "Álvaro", "Enrique",
    "Pedro", "Samuel", "David", "Ignacio", "Rodrigo",
]
LAST_NAMES = [
    "Hernández", "Martínez", "López", "Rodríguez", "Pérez", "Flores", "Cruz",
    "Rivera", "González", "Sánchez", "Vásquez", "Aguilar", "Ortiz", "Mendoza",
    "Solís", "Castro", "Romero", "Alvarado", "Contreras", "Navarrete", "Pineda",
    "Escobar", "Delgado", "Rivas", "Portillo", "Chávez", "Mejía", "Palacios",
    "Argueta", "Deras", "Bolaños", "Quintanilla", "Sorto", "Henríquez", "Iraheta",
    "Orellana", "Velasco", "Salinas", "Villalta", "Barahona", "Ceren", "Arias",
    "Benitez", "Cornejo", "Fuentes", "Guzmán", "Herrera", "Iglesias", "Jovel",
    "Lara", "Meléndez", "Núñez", "Olivares", "Peña", "Quijano", "Reyes",
]


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_wedding_info() -> dict:
    return {
        "synthetic": True,
        "disclaimer": (
            "SYNTHETIC / FICTICIO. All names, places, contacts, dates and details "
            "in this sheet are invented for the Boda Lista demo and evaluation. "
            "They do not describe a real wedding or real people."
        ),
        "couple": {
            "bride": {"first_name": "Lucía", "last_name": "Mendoza"},
            "groom": {"first_name": "Andrés", "last_name": "Solís"},
        },
        "date": "2026-12-12",
        "timezone": "America/El_Salvador",
        "venue": {
            "name": "Hacienda El Sauce",
            "address": "Km 12.5 Carretera a La Libertad",
            "city": "Santa Tecla, La Libertad",
            "country": "El Salvador",
            "ceremony_area": "Jardín Principal",
            "reception_area": "Salón El Encanto",
            "notes": (
                "The property is a 25-minute drive from central Santa Tecla. "
                "A covered backup hall is available if it rains."
            ),
            "notes_es": (
                "La propiedad queda a 25 minutos en carro del centro de Santa Tecla. "
                "Hay un salón cubierto de respaldo si llueve."
            ),
        },
        "schedule": [
            {"time": "15:30", "title": "Llegada de invitados / Guest arrival", "place": "Patio de ceibas", "notes": "Agua y café de bienvenida."},
            {"time": "16:00", "title": "Ceremonia / Ceremony", "place": "Jardín Principal"},
            {"time": "17:30", "title": "Cóctel / Cocktail hour", "place": "Terraza de los Izotes"},
            {"time": "18:30", "title": "Cena y recepción / Dinner and reception", "place": "Salón El Encanto"},
            {"time": "20:00", "title": "Baile de los novios / First dance", "place": "Salón El Encanto"},
            {"time": "21:00", "title": "Pastel y brindis / Cake and toast", "place": "Salón El Encanto"},
            {"time": "01:00", "title": "Cierre / End of celebration", "place": "Salón El Encanto", "notes": "El servicio de shuttle cierra a las 01:15."},
        ],
        "dress_code": {
            "summary": "Formal de cóctel.",
            "details": (
                "Se sugiere vestido de cóctel o traje / guayabera formal. "
                "Por favor no usar blanco, ivory ni crema, colores reservados para la novia. "
                "El jardín tiene césped: se recomiendan zapatos cómodos."
            ),
            "notes": "Cocktail attire. Guayaberas are welcome. Please do not wear white, ivory or cream.",
        },
        "parking": {
            "summary": "Valet gratuito en la entrada de la hacienda y shuttle desde el Centro Comercial El Encuentro.",
            "details": (
                "El valet opera desde las 15:00. Hay un shuttle gratuito desde el parqueo del "
                "Centro Comercial El Encuentro (estacionamiento norte) cada 20 minutos de 15:00 a 19:00, "
                "y de regreso entre 22:00 y 01:15. No estacionar en el hombro de la carretera."
            ),
            "details_en": (
                "Valet operates from 15:00. A free shuttle runs from the north lot of "
                "Centro Comercial El Encuentro (estacionamiento norte) every 20 minutes from 15:00 to 19:00, "
                "and returns between 22:00 and 01:15. Do not park on the highway shoulder."
            ),
            "notes": "Do not park on the highway shoulder. The last shuttle back leaves at 1:15 a.m.",
        },
        "gifts": {
            "summary": "Lluvia de sobres.",
            "details": (
                "Los novios prefieren una lluvia de sobres. No se reciben electrodomésticos. "
                "Si desean contribuir al viaje de novios, pueden hacerlo en el sobre o por transferencia "
                "a la cuenta que indicará la coordinadora el día del evento. No hay mesa de regalos pública."
            ),
            "notes": "Money envelopes are preferred. There is no public gift registry. Please do not bring appliances.",
        },
        "contacts": [
            {
                "name": "Elena Castro",
                "role": "Coordinadora de boda / Wedding coordinator",
                "email": "elena.castro@boda-mendoza-solis.example.com",
                "phone": "5550-0101",
            },
            {
                "name": "Roberto Solís",
                "role": "Contacto de la familia / Family contact",
                "email": "roberto.solis@boda-mendoza-solis.example.com",
                "phone": "5550-0102",
            },
        ],
    }


def build_info_sheet_md(info: dict) -> str:
    bride = info["couple"]["bride"]
    groom = info["couple"]["groom"]
    v = info["venue"]
    lines = [
        "# Boda Mendoza–Solís",
        "",
        "> **SYNTHETIC / FICTICIO.** This information sheet is invented for the Boda Lista demo. It does not describe a real wedding or real people.",
        "",
        f"**{bride['first_name']} {bride['last_name']}** y **{groom['first_name']} {groom['last_name']}**",
        f"Fecha: sábado 12 de diciembre de 2026 (America/El_Salvador)",
        "",
        "## Venue",
        f"- {v['name']}",
        f"- {v['address']}",
        f"- {v['city']}, {v['country']}",
        f"- Ceremonia: {v['ceremony_area']}",
        f"- Recepción: {v['reception_area']}",
    ]
    for key in ("notes_es", "notes"):
        note = (v.get(key) or "").strip()
        if note:
            lines.append(f"- {note}")
    lines += [
        "",
        "## Schedule",
    ]
    for item in info["schedule"]:
        extra = f" — {item['place']}" if item.get("place") else ""
        note = f" ({item['notes']})" if item.get("notes") else ""
        lines.append(f"- {item['time']} {item['title']}{extra}{note}")
    for key, title in (("dress_code", "Dress code"), ("parking", "Parking"), ("gifts", "Gifts")):
        block = info[key]
        lines += ["", f"## {title}", f"- {block['summary']}"]
        if block.get("details"):
            lines.append(f"- {block['details']}")
        if block.get("details_en"):
            lines.append(f"- {block['details_en']}")
        if block.get("notes"):
            lines.append(f"- {block['notes']}")
    lines += ["", "## Contacts"]
    for c in info["contacts"]:
        bits = [c["name"], c["role"]]
        if c.get("email"):
            bits.append(c["email"])
        if c.get("phone"):
            bits.append(c["phone"])
        lines.append("- " + " · ".join(bits))
    lines.append("")
    return "\n".join(lines) + "\n"


def build_guests(rng: random.Random) -> tuple[list[dict], list[dict]]:
    firsts_f = FIRST_NAMES_F[:]
    firsts_m = FIRST_NAMES_M[:]
    lasts = [n for n in LAST_NAMES if n not in BLOCKED_SURNAMES]
    rng.shuffle(firsts_f)
    rng.shuffle(firsts_m)
    rng.shuffle(lasts)

    # 50 singles + 30 couples (60) + 10 of 3 (30) + 2 of 4 (8) + 1 of 2 leftover (2) = 150, 93 households
    # Adjust: 50*1 + 30*2 + 10*3 + 2*4 + 1*2 = 50+60+30+8+2 = 150; households = 50+30+10+2+1 = 93
    plan = [(1, 50), (2, 30), (3, 10), (4, 2), (2, 1)]
    guests: list[dict] = []
    households: list[dict] = []
    used_names: set[tuple[str, str]] = set()
    fi = mi = li = 0

    def next_name(sex: str) -> tuple[str, str]:
        nonlocal fi, mi, li
        for _ in range(500):
            if sex == "f":
                first = firsts_f[fi % len(firsts_f)]
                fi += 1
            else:
                first = firsts_m[mi % len(firsts_m)]
                mi += 1
            last = lasts[li % len(lasts)]
            li += 1
            if last in BLOCKED_SURNAMES:
                continue
            key = (first, last)
            if key not in used_names:
                used_names.add(key)
                return first, last
        raise RuntimeError("name pool exhausted")

    gid = hid = 0
    sides = ["bride", "groom", "friend"]
    for size, n_hh in plan:
        for _ in range(n_hh):
            hid += 1
            household_id = f"hh-{hid:03d}"
            side = rng.choices(sides, weights=[45, 45, 10], k=1)[0]
            last = None
            members = []
            for j in range(size):
                gid += 1
                if j == 0:
                    sex = rng.choice(["f", "m"])
                elif j == 1 and size >= 2:
                    sex = "m" if members[0]["sex"] == "f" else "f"
                else:
                    sex = rng.choice(["f", "m"])
                first, last_name = next_name(sex)
                if j == 0:
                    last = last_name
                else:
                    # family share a surname
                    last_name = last
                    # keep unique full names: if clash, tweak first already unique per (first,last) — may clash
                    if (first, last_name) in used_names and j > 0:
                        first, _ = next_name(sex)
                    used_names.add((first, last_name))
                age_group = "child" if (j >= 2 and rng.random() < 0.7) or (size >= 3 and j == size - 1 and rng.random() < 0.8) else "adult"
                if j < 2:
                    age_group = "adult"
                guest = {
                    "guest_id": f"guest-{gid:03d}",
                    "household_id": household_id,
                    "first_name": first,
                    "last_name": last_name,
                    "side": side,
                    "age_group": age_group,
                    "synthetic": True,
                    "sex": sex,  # stripped later? keep out of public file maybe
                }
                members.append(guest)
            display = f"Familia {last}" if size > 1 else f"{members[0]['first_name']} {members[0]['last_name']}"
            households.append({
                "household_id": household_id,
                "display_name": display,
                "size": size,
                "side": side,
                "synthetic": True,
            })
            guests.extend(members)

    assert len(guests) == 150, len(guests)
    # strip internal-only sex if we want a cleaner file — keep it? schema doesn't cover guests. I'll drop sex from output.
    public = []
    for g in guests:
        public.append({k: v for k, v in g.items() if k != "sex"})
    return public, households


def build_vendors() -> list[dict]:
    rows = [
        {"id": "vendor-01", "vendor_type": "venue", "vendor_name": "Hacienda El Sauce", "description": "Renta de jardín, salón y mobiliario base, 12 dic 2026.", "amount_usd": 4200, "status": "deposit_paid", "currency": "USD", "synthetic": True},
        {"id": "vendor-02", "vendor_type": "catering", "vendor_name": "Catering La Cosecha", "description": "Cena de 150 platos, cóctel y barra de café. Menú infantil incluido.", "amount_usd": 3750, "status": "quoted", "currency": "USD", "synthetic": True},
        {"id": "vendor-03", "vendor_type": "music", "vendor_name": "DJ Río Viejo", "description": "Sonido, iluminación y 6 horas de música, incluye ceremonia.", "amount_usd": 900, "status": "quoted", "currency": "USD", "synthetic": True},
        {"id": "vendor-04", "vendor_type": "photo_video", "vendor_name": "Luz de Tarde Studio", "description": "Foto y video, 10 horas, álbum digital.", "amount_usd": 1600, "status": "deposit_paid", "currency": "USD", "synthetic": True},
        {"id": "vendor-05", "vendor_type": "flowers", "vendor_name": "Izotes y Cera", "description": "Arreglos de ceremonia, centros de mesa y ramo.", "amount_usd": 850, "status": "quoted", "currency": "USD", "synthetic": True},
        {"id": "vendor-06", "vendor_type": "cake", "vendor_name": "Pastelería Nube de Coco", "description": "Pastel de tres pisos, vainilla y tres leches, 150 porciones.", "amount_usd": 280, "status": "quoted", "currency": "USD", "synthetic": True},
        {"id": "vendor-07", "vendor_type": "beauty", "vendor_name": "Studio Barro y Rosa", "description": "Maquillaje y peinado de novia más 3 madrinas.", "amount_usd": 320, "status": "quoted", "currency": "USD", "synthetic": True},
        {"id": "vendor-08", "vendor_type": "transport", "vendor_name": "Shuttle El Encuentro", "description": "Dos micros, ruta centro comercial–hacienda, 15:00–01:15.", "amount_usd": 450, "status": "quoted", "currency": "USD", "synthetic": True},
    ]
    return rows


def build_guest_questions() -> list[dict]:
    """Hand-checked guest Q&A. Out-of-scope gold is the locked phrase."""
    in_scope = [
        ("es", "¿A qué hora es la ceremonia?", "La ceremonia es a las 16:00 en el Jardín Principal de Hacienda El Sauce."),
        ("es", "¿Dónde es la boda?", "La boda es en Hacienda El Sauce, Km 12.5 Carretera a La Libertad, Santa Tecla, La Libertad, El Salvador."),
        ("es", "¿Cuál es el código de vestimenta?", "El código de vestimenta es formal de cóctel. Se sugiere vestido de cóctel o traje / guayabera formal. Por favor no usar blanco, ivory ni crema."),
        ("es", "¿Puedo usar guayabera?", "Sí. Las guayaberas formales son bienvenidas."),
        ("es", "¿Se puede ir de blanco?", "No. El blanco, ivory y crema están reservados para la novia."),
        ("es", "¿Hay parqueo?", "Sí. Hay valet gratuito en la entrada de la hacienda desde las 15:00, y un shuttle gratuito desde el parqueo norte del Centro Comercial El Encuentro."),
        ("es", "¿Cada cuánto sale el shuttle?", "El shuttle sale cada 20 minutos de 15:00 a 19:00, y de regreso entre 22:00 y 01:15."),
        ("es", "¿A qué hora sale el último shuttle de regreso?", "El último shuttle de regreso sale a la 01:15."),
        ("es", "¿Puedo estacionarme en la carretera?", "No. No se debe estacionar en el hombro de la carretera."),
        ("es", "¿Qué les regalo a los novios?", "Los novios prefieren una lluvia de sobres. No se reciben electrodomésticos y no hay mesa de regalos pública."),
        ("es", "¿Hay mesa de regalos?", "No hay mesa de regalos pública. Los novios prefieren una lluvia de sobres."),
        ("es", "¿A qué hora empieza el cóctel?", "El cóctel es a las 17:30 en la Terraza de los Izotes."),
        ("es", "¿A qué hora es la cena?", "La cena y recepción son a las 18:30 en el Salón El Encanto."),
        ("es", "¿Hasta qué hora es la fiesta?", "La celebración cierra a la 01:00. El shuttle de regreso cierra a la 01:15."),
        ("es", "¿La ceremonia es al aire libre?", "Sí, la ceremonia es en el Jardín Principal. Hay un salón cubierto de respaldo si llueve."),
        ("es", "¿Qué hago si llueve?", "La hacienda tiene un salón cubierto de respaldo si llueve."),
        ("es", "¿A qué hora hay que llegar?", "La llegada de invitados es a las 15:30 en el Patio de ceibas."),
        ("es", "¿Quién es la coordinadora y cómo le marco?", "La coordinadora es Elena Castro, elena.castro@boda-mendoza-solis.example.com, 5550-0101."),
        ("es", "¿Me pueden dar un teléfono de contacto de la familia?", "Roberto Solís es el contacto de la familia: roberto.solis@boda-mendoza-solis.example.com, 5550-0102."),
        ("es", "¿Cuánto tiempo hay del centro de Santa Tecla a la hacienda?", "La propiedad queda a unos 25 minutos del centro de Santa Tecla."),
        ("es", "¿A qué hora es el baile de los novios?", "El baile de los novios es a las 20:00 en el Salón El Encanto."),
        ("es", "¿Cuándo cortan el pastel?", "El pastel y el brindis son a las 21:00 en el Salón El Encanto."),
        ("es", "¿Puedo usar zapatos de tacón fino en el jardín?", "El jardín tiene césped; se recomiendan zapatos cómodos."),
        ("en", "What time is the ceremony?", "The ceremony is at 4:00 p.m. in the Jardín Principal at Hacienda El Sauce."),
        ("en", "Where is the wedding?", "The wedding is at Hacienda El Sauce, Km 12.5 Carretera a La Libertad, Santa Tecla, La Libertad, El Salvador."),
        ("en", "What is the dress code?", "The dress code is cocktail attire. A cocktail dress or a suit / formal guayabera is suggested. Please do not wear white, ivory or cream."),
        ("en", "Is there parking?", "Yes. Free valet is available at the hacienda gate from 3:00 p.m., plus a free shuttle from the north parking lot of Centro Comercial El Encuentro."),
        ("en", "When is the last shuttle back?", "The last shuttle back leaves at 1:15 a.m."),
        ("en", "What should we gift the couple?", "The couple prefers a money envelope (lluvia de sobres). Please do not bring appliances. There is no public gift registry."),
        ("en", "Is there a gift registry?", "There is no public gift registry. The couple prefers money envelopes."),
        ("en", "Who is the wedding coordinator?", "The coordinator is Elena Castro, elena.castro@boda-mendoza-solis.example.com, 5550-0101."),
        ("en", "What time should guests arrive?", "Guest arrival is at 3:30 p.m. at the Patio de ceibas."),
    ]
    out_of_scope = [
        ("es", "¿Hay tarifa especial en un hotel para invitados?"),
        ("es", "¿Va a ir el exnovio de Lucía?"),
        ("es", "¿Qué marcas van a servir en la barra libre?"),
        ("es", "¿Puedo llevar a mi perro?"),
        ("es", "¿Van a transmitir la ceremonia en vivo?"),
        ("es", "¿Me puedo llevar un plus one que no está en la lista?"),
        ("en", "Do you have a block of hotel rooms and the group rate?"),
        ("en", "Can I bring my dog to the reception?"),
        ("en", "Will there be a livestream link?"),
        ("en", "Is so-and-so invited? I want to check a name that isn't on my invite."),
    ]
    rows = []
    n = 0
    for lang, text, answer in in_scope:
        n += 1
        rows.append({
            "id": f"qa-{n:04d}",
            "split": "test",
            "task": "guest_question",
            "text": text,
            "lang": lang,
            "answer": answer,
            "out_of_scope": False,
        })
    for lang, text in out_of_scope:
        n += 1
        rows.append({
            "id": f"qa-{n:04d}",
            "split": "test",
            "task": "guest_question",
            "text": text,
            "lang": lang,
            "answer": UNKNOWN_ANSWER,
            "out_of_scope": True,
        })
    return rows


def song_records() -> list[dict]:
    """60 hand-checked song requests: 45 clear (real title+artist) and 15 vague."""
    clear = [
        ("es", "Pueden poner Vivir Mi Vida de Marc Anthony? esa nos encanta", "Vivir Mi Vida", "Marc Anthony", "dance"),
        ("es", "Para el vals pedimos Perfect de Ed Sheeran", "Perfect", "Ed Sheeran", "slow"),
        ("es", "Suavemente de Elvis Crespo, pa' que baile la familia", "Suavemente", "Elvis Crespo", "dance"),
        ("es", "Una bachata: Propuesta Indecente de Romeo Santos", "Propuesta Indecente", "Romeo Santos", "medium"),
        ("es", "La Bilirrubina de Juan Luis Guerra, merengue clásico", "La Bilirrubina", "Juan Luis Guerra", "dance"),
        ("es", "Pongan Obsesión de Aventura porfa", "Obsesión", "Aventura", "medium"),
        ("es", "Gasolina de Daddy Yankee cuando ya esté animado el salón", "Gasolina", "Daddy Yankee", "dance"),
        ("es", "Como La Flor de Selena, no puede faltar", "Como La Flor", "Selena", "medium"),
        ("es", "A Puro Dolor de Son by Four para una lenta", "A Puro Dolor", "Son by Four", "slow"),
        ("es", "El Niágara en Bicicleta de Juan Luis Guerra", "El Niágara en Bicicleta", "Juan Luis Guerra", "dance"),
        ("es", "La Vida Es Un Carnaval de Celia Cruz, esa es obligatoria", "La Vida Es Un Carnaval", "Celia Cruz", "dance"),
        ("es", "Darte un Beso de Prince Royce", "Darte un Beso", "Prince Royce", "medium"),
        ("es", "Valió la Pena de Marc Anthony, salsa", "Valió la Pena", "Marc Anthony", "dance"),
        ("es", "Nada Se Compara Contigo de Álvaro Torres, lenta", "Nada Se Compara Contigo", "Álvaro Torres", "slow"),
        ("es", "Cumbia Sobre el Río de Celso Piña", "Cumbia Sobre el Río", "Celso Piña", "dance"),
        ("es", "La Incondicional de Luis Miguel para una romantica", "La Incondicional", "Luis Miguel", "slow"),
        ("es", "Tusa de Karol G, pa' las primas", "Tusa", "Karol G", "dance"),
        ("es", "Rayando el Sol de Maná", "Rayando el Sol", "Maná", "medium"),
        ("es", "Tu Sonrisa de Elvis Crespo", "Tu Sonrisa", "Elvis Crespo", "dance"),
        ("es", "Un Beso de Aventura", "Un Beso", "Aventura", "medium"),
        ("es", "Que Nadie Sepa Mi Sufrir de La Sonora Dinamita", "Que Nadie Sepa Mi Sufrir", "La Sonora Dinamita", "dance"),
        ("es", "Ojalá Que Llueva Café de Juan Luis Guerra", "Ojalá Que Llueva Café", "Juan Luis Guerra", "dance"),
        ("es", "Héroe de Enrique Iglesias, lenta", "Héroe", "Enrique Iglesias", "slow"),
        ("es", "Mi Gente de J Balvin cuando pida el DJ cumbia-reggaeton", "Mi Gente", "J Balvin", "dance"),
        ("es", "Por Debajo de la Mesa de Luis Miguel", "Por Debajo de la Mesa", "Luis Miguel", "slow"),
        ("es", "Bachata Rosa de Juan Luis Guerra", "Bachata Rosa", "Juan Luis Guerra", "medium"),
        ("es", "Livin' la Vida Loca de Ricky Martin", "Livin' la Vida Loca", "Ricky Martin", "dance"),
        ("es", "Color Esperanza de Diego Torres", "Color Esperanza", "Diego Torres", "medium"),
        ("es", "Las Pamplonas de Los Hermanos Flores, cumbia salvadoreña", "Las Pamplonas", "Los Hermanos Flores", "dance"),
        ("es", "Procura de Chichi Peralta", "Procura", "Chichi Peralta", "dance"),
        ("es", "Despacito de Luis Fonsi, aunque ya la conozcan todos", "Despacito", "Luis Fonsi", "dance"),
        ("es", "Tiempo de Vals de Chayanne para cuando bailen los novios", "Tiempo de Vals", "Chayanne", "slow"),
        ("es", "Quimbara de Celia Cruz", "Quimbara", "Celia Cruz", "dance"),
        ("es", "Hawái de Maluma", "Hawái", "Maluma", "dance"),
        ("es", "Historia de Taxi de Ricardo Arjona", "Historia de Taxi", "Ricardo Arjona", "medium"),
        ("es", "Pepas de Farruko, pa' tarde en la noche", "Pepas", "Farruko", "dance"),
        ("en", "Please play All of Me by John Legend for a slow dance", "All of Me", "John Legend", "slow"),
        ("en", "Can the DJ play Thinking Out Loud by Ed Sheeran?", "Thinking Out Loud", "Ed Sheeran", "slow"),
        ("en", "A Thousand Years by Christina Perri, if possible", "A Thousand Years", "Christina Perri", "slow"),
        ("en", "Stand by Me, the Prince Royce bachata version", "Stand by Me", "Prince Royce", "medium"),
        ("en", "Hips Don't Lie by Shakira would be fun", "Hips Don't Lie", "Shakira", "dance"),
        ("en", "Play Felices los 4 by Maluma later in the night", "Felices los 4", "Maluma", "dance"),
        ("en", "La Copa de la Vida by Ricky Martin, classic wedding energy", "La Copa de la Vida", "Ricky Martin", "dance"),
        ("en", "Bidi Bidi Bom Bom by Selena please", "Bidi Bidi Bom Bom", "Selena", "dance"),
        ("en", "Odio by Romeo Santos, a bachata is fine", "Odio", "Romeo Santos", "medium"),
    ]
    vague = [
        ("es", "la de Marc Anthony que siempre ponen", "Marc Anthony", None),
        ("es", "algo de Juan Luis Guerra para bailar", "Juan Luis Guerra", "dance"),
        ("es", "una bachata lenta", None, "slow"),
        ("es", "poné música alegre", None, "dance"),
        ("es", "el clásico de Romeo", "Romeo Santos", None),
        ("es", "una de Shakira", "Shakira", None),
        ("es", "la que pusieron en la boda de mi prima", None, None),
        ("es", "merengue de los 90", None, "dance"),
        ("es", "cumbia salvadoreña", None, "dance"),
        ("es", "la de Luis Miguel del piano", "Luis Miguel", "slow"),
        ("es", "la del vals", None, "slow"),
        ("es", "algo para bailar salsa", None, "dance"),
        ("en", "something slow for the newlyweds", None, "slow"),
        ("en", "a daddy yankee track", "Daddy Yankee", "dance"),
        ("en", "any good merengue is fine", None, "dance"),
    ]
    assert len(clear) == 45 and len(vague) == 15
    rows = []
    n = 0
    for lang, text, title, artist, energy in clear:
        n += 1
        rows.append({
            "id": f"song-{n:04d}",
            "split": "test",
            "task": "song",
            "text": text,
            "lang": lang,
            "title": title,
            "artist": artist,
            "energy": energy,
            "ambiguous": False,
        })
    for lang, text, artist, energy in vague:
        n += 1
        rows.append({
            "id": f"song-{n:04d}",
            "split": "test",
            "task": "song",
            "text": text,
            "lang": lang,
            "title": None,
            "artist": artist,
            "energy": energy,
            "ambiguous": True,
        })
    return rows


def assign_households(rng: random.Random, rows: list[dict], households: list[dict], field: str = "household_id") -> None:
    ids = [h["household_id"] for h in households]
    for row in rows:
        if field not in row or not row[field]:
            row[field] = rng.choice(ids)


def build_rsvps(households: list[dict], rng: random.Random) -> list[dict]:
    if len(RSVP_RECORDS) != 300:
        raise SystemExit(f"rsvp_bank.RECORDS must have 300 items, got {len(RSVP_RECORDS)}")
    texts = [r["text"] for r in RSVP_RECORDS]
    if len(set(texts)) != 300:
        raise SystemExit("rsvp_bank.RECORDS texts are not unique")
    ids = [h["household_id"] for h in households]
    # Prefer a stable assignment: walk households in a cycle so most appear in the test set.
    rows = []
    for i, rec in enumerate(RSVP_RECORDS, 1):
        row = {
            "id": f"rsvp-{i:04d}",
            "split": "test",
            "task": "rsvp",
            "text": rec["text"],
            "lang": rec["lang"],
            "attending": rec["attending"],
            "party_size": rec["party_size"],
            "meal_restrictions": list(rec["meal_restrictions"]),
            "kids_count": rec["kids_count"],
            "needs_ride": rec["needs_ride"],
            "ambiguous": rec["ambiguous"],
            "household_id": rec.get("household_id") or ids[(i - 1) % len(ids)],
        }
        rows.append(row)
    return rows


def generate_modal_sets(_args: argparse.Namespace) -> int:
    print(
        "Modal generation is not wired in this revision (token expired). "
        "Dev and stress files come from tools/data/generate_dev.py "
        "(deterministic templates, seed 20261124), not from Modal. "
        "Those files must never use split=test and must not reuse test ids "
        "or texts. See docs/data.md.",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Boda Lista synthetic data pack.")
    parser.add_argument(
        "--generate-modal",
        action="store_true",
        help="No-op. Dev and stress rows are written by generate_dev.py. The Modal token is expired.",
    )
    args = parser.parse_args(argv)
    rng = random.Random(SEED)
    DATA.mkdir(parents=True, exist_ok=True)

    info = build_wedding_info()
    dump_json(DATA / "wedding_info.json", info)
    (DATA / "info_sheet.md").write_text(build_info_sheet_md(info), encoding="utf-8")

    guests, households = build_guests(rng)
    dump_jsonl(DATA / "guests.jsonl", guests)
    dump_jsonl(DATA / "households.jsonl", households)

    rsvps = build_rsvps(households, rng)
    dump_jsonl(DATA / "rsvp_replies.jsonl", rsvps)

    songs = song_records()
    assign_households(rng, songs, households)
    dump_jsonl(DATA / "song_requests.jsonl", songs)

    questions = build_guest_questions()
    dump_jsonl(DATA / "guest_questions.jsonl", questions)

    vendors = build_vendors()
    dump_jsonl(DATA / "vendor_quotes.jsonl", vendors)

    print(f"Wrote pack under {DATA}")
    print(f"  guests.jsonl: {len(guests)}")
    print(f"  households.jsonl: {len(households)}")
    print(f"  rsvp_replies.jsonl: {len(rsvps)} (all split=test)")
    print(f"  song_requests.jsonl: {len(songs)}")
    print(f"  guest_questions.jsonl: {len(questions)}")
    print(f"  vendor_quotes.jsonl: {len(vendors)}")
    print("  wedding_info.json + info_sheet.md")
    print("  schema.json is a source file (not overwritten)")

    if args.generate_modal:
        return generate_modal_sets(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
