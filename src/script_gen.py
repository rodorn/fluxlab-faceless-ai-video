"""Generowanie scenariusza wideo.

Tryb realny: OpenAI (OPENAI_API_KEY) lub Anthropic/Claude (ANTHROPIC_API_KEY).
Tryb demo (brak kluczy): wbudowany przykladowy scenariusz.
"""

from __future__ import annotations

import json
import logging
import os

from .models import Script

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Jestes scenarzysta krotkich pionowych wideo typu faceless (TikTok / YouTube Shorts) "
    "po polsku. Tworzysz dynamiczny scenariusz: mocny hook, 5 krotkich scen narracji "
    "i jedno wyrazne CTA. Zwracasz WYLACZNIE JSON o kluczach: title, hook, scenes (lista 5 "
    "napisow), cta."
)

DEMO_SCRIPT = Script(
    title="3 nawyki, ktore zmieniaja stylizacje w 30 sekund",
    hook="Nosisz drogie ubrania, a i tak wygladasz przecietnie? Oto dlaczego.",
    scenes=[
        "Sekret nie tkwi w cenie ubran, tylko w proporcjach sylwetki.",
        "Zasada numer jeden: gora dopasowana, dol luzniejszy albo odwrotnie, nigdy oba na raz.",
        "Zasada numer dwa: jeden akcent koloru na cala stylizacje, reszta stonowana.",
        "Zasada numer trzy: dodatki robia robote, zegarek albo pasek zmienia wszystko.",
        "Przetestuj to jutro rano i zobacz roznice w lustrze od razu.",
    ],
    cta="Obserwuj TomStyl po wiecej trikow ze stylizacji i zapisz ten filmik na pozniej.",
)


def _from_openai(topic: str, api_key: str) -> Script:
    from openai import OpenAI  # import lokalny, opcjonalna zaleznosc

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Temat wideo: {topic}"},
        ],
        response_format={"type": "json_object"},
    )
    return _parse(resp.choices[0].message.content)


def _from_anthropic(topic: str, api_key: str) -> Script:
    import anthropic  # import lokalny, opcjonalna zaleznosc

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Temat wideo: {topic}. Zwroc sam JSON."}
        ],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return _parse(text)


def _parse(raw: str) -> Script:
    data = json.loads(raw)
    return Script(
        title=data.get("title", "").strip(),
        hook=data.get("hook", "").strip(),
        scenes=[s.strip() for s in data.get("scenes", []) if s.strip()],
        cta=data.get("cta", "").strip(),
    )


def generate_script(
    topic: str = "porady stylizacyjne", provider: str | None = None
) -> Script:
    """Generuje scenariusz. Bez kluczy zwraca DEMO_SCRIPT.

    provider: "openai" | "anthropic" | None (autodetekcja z env).
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if provider == "openai" or (provider is None and openai_key):
        if openai_key:
            log.info("script_gen: uzywam OpenAI")
            return _from_openai(topic, openai_key)
    if provider == "anthropic" or (provider is None and anthropic_key):
        if anthropic_key:
            log.info("script_gen: uzywam Anthropic")
            return _from_anthropic(topic, anthropic_key)

    log.info("script_gen: tryb demo (brak kluczy API), zwracam wbudowany scenariusz")
    return DEMO_SCRIPT
