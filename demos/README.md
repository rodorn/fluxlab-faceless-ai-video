# Demos

Przykładowe skrypty produkcyjne pokazujące pełny potok faceless video.

## build_demo_elevenlabs.py

Klip z lektorem ElevenLabs (multilingual_v2, polski głos). Per-zdanie TTS,
realne czasy, synchronizowane napisy, montaż premium, muzyka.

```
ELEVENLABS_API_KEY=... python3 demos/build_demo_elevenlabs.py
```

Produkuje `out/voice_11.wav`, `out/captions_11.srt` i `out/sample_tomstyl_11.mp4`.

## build_demo_broll.py

Wariant z tłem wideo (Ken Burns na zdjęciach). Reużywa lektora i napisów
z `build_demo_elevenlabs.py`, podmienia gradientowe tło na kadry ze zdjęć w
`demos/assets/`. Gładki, wyśrodkowany zoom (bez trzęsienia), crossfade,
grading, limiter zamiast dynamicznego loudnorm.

```
python3 demos/build_demo_broll.py            # tempo lektora 1.0
SPEED=1.07 python3 demos/build_demo_broll.py # lektor +7%
```

### Zdjęcia tła (assets)

Do `demos/assets/*.jpg` wrzuć zdjęcia na wolnej licencji dopuszczającej użytek
komercyjny (np. Wikimedia Commons CC BY-SA / CC0). Materiały prasowe producentów
zwykle są tylko do użytku redakcyjnego, nie do treści komercyjnych, więc nie
nadają się do tego potoku. Przy licencjach z atrybucją (CC BY / CC BY-SA)
podaj autora i licencję w opisie publikowanego materiału; CC BY-SA wymaga też
udostępnienia utworu zależnego na tej samej licencji (ShareAlike).
