# Faceless AI Video Pipeline

Automatyczny potok do kanalu typu "faceless AI" na TikToka i YouTube Shorts:
scenariusz, lektor po polsku, napisy, montaz i publikacja. Zbudowany pod realny
scenariusz uzycia (kanal stylizacyjny), z mysla o 1-2 filmach dziennie.

Potok dziala od reki w trybie demo (bez platnych kluczy API): realnie renderuje
pionowy plik MP4 1080x1920 z wypalonymi napisami. Klucze API wlaczaja tryb realny.

## Architektura

Kolejne kroki potoku (kazdy to osobny modul w `src/`):

1. `script_gen.py` - scenariusz (hook + 5 scen + CTA). Realnie: OpenAI lub Anthropic/Claude.
   Demo: wbudowany przykladowy scenariusz.
2. `voice.py` - lektor po polsku. Realnie: ElevenLabs. Demo: cichy placeholder audio
   (ffmpeg `anullsrc`) o dlugosci dopasowanej do tekstu, zeby dalsze kroki dzialaly.
3. `captions.py` - deterministyczny podzial tekstu na segmenty czasowe i zapis `.srt`
   (bez API), na podstawie liczby slow i tempa mowy.
4. `assemble.py` - montaz FFmpeg: tlo (kolor lub podane obrazy) + lektor + wypalone
   napisy + placeholder muzyki, wynik to pionowy MP4 1080x1920.
5. `publish.py` - szkielet publikacji na TikToka (Content Posting API) i YouTube Shorts
   (Data API v3) z retry i backoffem. Demo/dry-run: tylko loguje "would upload".

Spinacz: `run.py` uruchamia kroki 1 do 5 (publikacja domyslnie w trybie dry-run).

```
script_gen -> voice -> captions -> assemble -> publish (dry-run)
```

## Wymagania

- Python 3.12 lub nowszy
- FFmpeg w systemie (`ffmpeg` w PATH)
- Zaleznosci Pythona z `requirements.txt` (opcjonalne, tylko dla trybu realnego)

## Jak uruchomic demo

```bash
python run.py
```

Efekt: powstaja pliki `out/video.mp4` (pionowy 1080x1920, z napisami),
`out/captions.srt` i `out/voice.mp3`. Sciezka i rozmiar MP4 pojawiaja sie w podsumowaniu.

Testy:

```bash
pip install -r requirements.txt
pytest -q
```

## Jak podpiac realne klucze

Skopiuj `.env.example` do `.env` i uzupelnij wybrane klucze, potem wyeksportuj do srodowiska
(potok czyta zmienne z `os.environ`, nie parsuje `.env` samodzielnie):

```bash
export $(grep -v '^#' .env | xargs)
```

Zmienne srodowiskowe:

- `OPENAI_API_KEY` lub `ANTHROPIC_API_KEY` - generowanie scenariusza
- `ELEVENLABS_API_KEY` (opcjonalnie `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL`) - lektor
- `TIKTOK_ACCESS_TOKEN`, `YOUTUBE_ACCESS_TOKEN` - publikacja

Realna publikacja (wymaga tokenow):

```bash
python run.py --publish
```

Bez danego klucza dany krok automatycznie schodzi do trybu demo. Zadne sekrety nie sa
trzymane w kodzie ani w repo (patrz `.gitignore`).

## Orkiestracja w n8n

Plik `workflow-n8n.json` to importowalny szkielet workflow (Schedule Trigger 09:00 i 17:00,
czyli 2 razy dziennie, wywolanie `run.py`, galaz sukcesu i galaz alertu). Import w n8n:
menu workflow, "Import from File".

## Struktura repo

```
src/            moduly potoku
tests/          testy pytest
run.py          orkiestrator
requirements.txt
workflow-n8n.json
.github/workflows/ci.yml
```

---

Zbudowane przez FluxLab, https://fluxlab.pl
