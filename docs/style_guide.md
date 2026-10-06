# Style guide: "light-built" reference

Source: `Quillami_Final.MP4` (supplied), 480×848 (9:16), 25 fps, 12.05 s, stereo AAC.
Method: one frame every 0.5 s (24 frames), plus a 0.2 s strip across the transition; ffmpeg scene detection, a luma curve every 0.25 s, k-means colour clusters per section, a noise measurement on the static hold, and onset, tempo and spectrum analysis of the audio. Every number below was measured unless it is marked *extrapolated*.

This guide describes the reference's **grammar** only. Its content (the speeding car made of light), its logo and its characters are not to be reused; see the shot list for how the grammar is applied to new content.

---

## 1. Structure at a glance

| Time | What happens | Luma (0–255) |
|---|---|---|
| 0.0–0.4 s | Black. One thin cyan streak flicks across. | 16 |
| 0.4–2.0 s | Camera pushes down a tunnel of radial light streaks. The subject approaches from the vanishing point. | 17 → 25 |
| 2.0–4.0 s | The camera orbits about 90°, from front three-quarter to side profile. The streaks rotate from radial to horizontal. | 29 → 49 |
| 4.0–5.6 s | A lateral tracking shot keeps pace with the subject. The streaks race horizontally and the wet floor reflects. | 54 → 68 |
| 5.6–6.5 s | **Whiteout.** Light accumulates until the frame blows out to cyan-white. The subject dissolves into it. | 75 → **217** (peak 6.5 s) |
| 6.5–7.0 s | The brand mark is assembled out of the light inside the whiteout. | 195 → 116 |
| 7.0–8.5 s | The streaks arc over the mark and decelerate. The floor glow drains. | 129 → 45 |
| 8.5–12.0 s | **Static hold.** Mark on a navy gradient, nothing moves. | 38 (flat) |

**Hard cuts: zero.** Scene detection found none above a 0.25 threshold. The piece is one continuous camera move, one luminance transition and one held frame.

---

## 2. Palette (measured hex)

Five-family system: void, navy, steel, ice and whiteout, plus one brand accent. There are no warm colours anywhere.

| Role | Hex | Where it was measured | Share of frame |
|---|---|---|---|
| Void | `#000002` | tunnel, 0.5–3 s | 36% |
| Void, blue-tinted | `#00000E` | tunnel | 29% |
| Deep navy | `#01041D` | tunnel | 22% |
| Night navy | `#02112C` | side pass, 3–5.5 s | 25% |
| Hold background, top | `#00182B` | static hold | gradient |
| Hold background, bottom | `#000E19` | static hold | gradient |
| Steel blue | `#023458` / `#153857` | mid-tones, floor | 3–12% |
| Streak blue | `#17698E` / `#2D6F94` | body of the light streaks | 2–9% |
| Ice | `#62A4C0` / `#96C7DC` | streak cores, reflections | 1–7% |
| Ice white | `#C0E0ED` | brightest streak cores | 6% (side pass) |
| Whiteout | `#F0FAFD` | flash peak | 30% |
| Flash cyan | `#AAE5F9` / `#59D4F3` | flash body | 9–20% |
| Brand turquoise | `#00D1D8` (in the video), `#44E1E5` (with glow) | the mark | 3% |
| Brand edge | `#0C8DAC` | mark rim, glow falloff | 2% |

Brand colours from the client's Instagram profile (sampled from the screenshot): highlight cyan `#54E2FF`, logo mint `#94F2DC`, logo ring blue `#3D9AC7`, profile UI black `#0D1014`.

**Rules**
- About 85% of every frame is void or navy (`#000002`–`#02112C`). Light is rare, and that rarity is the point.
- Highlights clip to pure white `#FEFEFE` only in streak cores and at the flash peak.
- Accent: turquoise or cyan only, used on the brand element and at the peak of the flash. Never on backgrounds.

---

## 3. Type

**The reference contains no live typography.** Its only lettering is the wordmark inside the logo: very wide, heavy, all-caps techno letterforms with rounded corners, a dark outline, and a much smaller second line under it. The rules below are *extrapolated* from that wordmark and from how the mark behaves, so the new video can carry text without breaking the grammar.

| | Display | UI / labels |
|---|---|---|
| Family | **Unbounded** (OFL): wide, geometric, rounded, closest to the wordmark | **JetBrains Mono** (OFL) |
| Weight | 800 for words, 400 for the secondary line | 500 |
| Case | ALL CAPS | ALL CAPS |
| Tracking | +0.04 em for words; +0.25 em for the small secondary line (the wordmark's "CAR WASH" sits very open) | +0.12 em |
| Size (1080×1920) | 150–220 px for one-word hits; 64–90 px for lines | 34–40 px |
| Colour | Ice white `#F0FAFD` with a turquoise glow; key word in turquoise `#00D1D8` | Ice `#96C7DC` |

One display face and one UI face, as the studio rules require. Words sit in the **upper-middle third** (the mark is centred at 38% of frame height, not 50%). The lower third stays free for the floor reflection.

---

## 4. Shot lengths and rhythm

- **One continuous shot for 6.0 s** (50% of the runtime), **one 0.9 s whiteout transition** (7%), **5.1 s of lockup**, of which **3.5 s is a dead-still hold** (29%).
- Energy does not come from cutting. It comes from **streak speed and camera direction**. The luma rises almost linearly (16 → 68) for 5.5 s, so the piece builds by accumulating light.
- Music: about **89 BPM** (beat ≈ 0.67 s), with a dense transient hit roughly every eighth note.
- Moments land on beats: the orbit starts near beat 3 (2.07 s), the whiteout peaks on beat 10 (6.33–6.5 s) and the hold starts near beat 13 (8.57 s).
- *For longer pieces (extrapolated):* keep each continuous segment at **3–6 s**, never shorter than one bar (2.7 s) except inside a build. Reserve the full whiteout for **one** climax.

---

## 5. Transitions

There are only two kinds. Neither is a cut.

1. **Whiteout (luminance transition).** Light builds over about 0.9 s (luma 68 → 217) on an ease-in. It peaks for 1–2 frames, then settles back over about 0.5 s (217 → 116), with the next image already forming inside the light. The outgoing subject does not fade: it **dissolves into its own light**, with streaks lengthening until they merge.
2. **Streak re-orientation (in-shot transition).** A change of view is carried by the streaks rotating. Radial streaks (forward motion) become horizontal streaks (lateral motion) as the camera orbits. *Extrapolated:* a fast streak acceleration, a whip of horizontal light, can bridge two continuous segments the same way.

Never: crossfades through black, slides, pushes, wipes with hard edges, or glitches.

---

## 6. Camera moves

| Move | Timing | Character |
|---|---|---|
| **Dolly forward** through a radial streak tunnel | 0.4–2.0 s | Vanishing point **at the top third**, not the centre. Steady speed with no ease. |
| **Subject approach** from the vanishing point | 0.5–2.0 s | The subject grows from about 8% to 25% of frame width. |
| **Orbit, about 90°**, front three-quarter to profile | 2.0–4.0 s | Ease-in-out. The vanishing point slides out of frame, so the streaks rotate from radial to horizontal. |
| **Lateral tracking**, locked to the subject | 4.0–5.6 s | The subject is static in frame and the world streaks past. The camera is slightly low (horizon at 55–60%). |
| **Lock-off** | 7.0–12.0 s | Fully static. Residual streaks decelerate on an ease-out, then stop. |

No handheld, no shake, no rack focus, no zoom punches. Motion blur is long, roughly a 360° shutter, on everything that moves.

---

## 7. Texture and finish

- **Light streaks** are the main texture: 1–3 px wide, 5–40% of frame length, an ice-white core with blue falloff, and **additive** blending. Density is about 120–200 visible at once in the tunnel and thinner in the hold.
- **Bloom / halation:** strong. Light bleeds 20–60 px around bright cores, and the brand mark carries a turquoise halo.
- **Wet floor reflection:** a mirrored, vertically blurred copy at about 40% intensity under the subject, glowing ice-white at contact.
- **Grain: none.** In the static hold, temporal noise is 0.24 luma levels (no animated grain) and spatial noise is 1.2 (a smooth gradient). It's a clean digital finish with soft banding in the navy gradients.
- **Vignette:** a natural fall-off from the vertical gradient (top 22.7 → centre 151 → bottom 13 luma behind the mark).
- **Background in holds:** a vertical navy gradient `#00182B` → `#000E19` with a soft radial lift behind the subject.

---

## 8. How text and graphic elements enter and exit

The reference's only graphic element is the mark. Its behaviour defines the rule, with text behaviour *extrapolated* from it.

- **Enter: built from light.** The mark is not cut in or scaled up. It **condenses out of the whiteout** (6.4–6.8 s): fragments of streak converge and the shape resolves as the flash recedes. *For text:* letters assemble from horizontal streak fragments that converge on their final positions (about 0.4–0.6 s, ease-out). The glow arrives first, then the shape and the halo settle.
- **Hold: absolutely still.** Once formed, an element does not bob, pulse or drift. Only the streaks behind it move, then even they stop.
- **Exit: smear into speed or into light.** Either the element stretches horizontally into streaks and races off with the motion (for a mid-piece exit), or it dissolves into a whiteout (into the climax). It never fades to black and never scales down.
- **Timing:** elements arrive **on a beat**, and at most one new text element per beat.

---

## 9. Sound (for matching the cut)

- About 89 BPM, loud master (**-10.9 LUFS**), and heavy energy at 40–300 Hz throughout: an engine and rumble bed under dense percussive hits.
- **Riser from about 5.8 s** (a tonal sweep climbing past 8 kHz) into the whiteout, with **tonal pings** at about 1.8 kHz and 4.3 kHz across the flash (6.0–6.9 s). That's the sonic signature of light being built.
- After the mark forms, the hits thin out and the track **fades over 9.5–12 s** under the static hold.
- *For our pipeline:* synthesize an equivalent bed (no samples), master to the studio's -14 LUFS rather than the reference's -10.9.
