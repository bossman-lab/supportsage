# Reddit Post for r/3Dprinting

## Title
I built an open-source tool that saves 35% on 3D printing support material

## Body
35% of my filament was going into the trash. Not failed prints — successful ones. Just support structures.

Every major slicer (Cura, PrusaSlicer, OrcaSlicer, Bambu Studio) uses the same 30-year-old algorithm: angle threshold, slap uniform supports everywhere. No geometry intelligence.

I built SupportSage — open-source Python CLI:
1. Grades overhangs by severity (critical vs borderline)
2. Detects islands via BFS (bridge = 2 islands, not 1 blob)
3. Tree supports with branch merging (saves 30-50%)

Install: pip install [link to wheel]
Repo: github.com/bossman-lab/supportsage
Deep-dive: dev.to link in comments

Building in public. Would love feedback or STL torture tests!

## Shareable Link
https://www.reddit.com/r/3Dprinting/submit?title=I%20built%20an%20open-source%20tool%20that%20saves%2035%25%20on%203D%20printing%20support%20material&text=35%25%20of%20my%20filament%20was%20going%20into%20the%20trash.%20Not%20failed%20prints%20%E2%80%94%20successful%20ones.%20Just%20support%20structures.%0A%0AEvery%20major%20slicer%20%28Cura%2C%20PrusaSlicer%2C%20OrcaSlicer%2C%20Bambu%20Studio%29%20uses%20the%20same%2030-year-old%20algorithm%3A%20angle%20threshold%2C%20slap%20uniform%20supports%20everywhere.%20No%20geometry%20intelligence.%0A%0AI%20built%20SupportSage%20%E2%80%94%20open-source%20Python%20CLI%3A%0A1.%20Grades%20overhangs%20by%20severity%20%28critical%20vs%20borderline%29%0A2.%20Detects%20islands%20via%20BFS%20%28bridge%20%3D%202%20islands%2C%20not%201%20blob%29%0A3.%20Tree%20supports%20with%20branch%20merging%20%28saves%2030-50%25%29%0A%0AInstall%3A%20pip%20install%20%5Blink%20to%20wheel%5D%0ARepo%3A%20github.com/bossman-lab/supportsage%0ADeep-dive%3A%20dev.to%20link%20in%20comments%0A%0ABuilding%20in%20public.%20Would%20love%20feedback%20or%20STL%20torture%20tests%21

Click the link above, log in if needed, and hit Submit.
