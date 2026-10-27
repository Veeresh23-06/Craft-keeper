# Craft Keeper: 3-Minute Hackathon Presentation Script

Structured around the 7 Hackathon Judging Criteria:
1. Problem and Impact
2. Working Demo
3. Use of Open Source
4. Responsible AI and Honesty
5. Creativity and UX
6. Theme Alignment (Audiovisual Heritage)
7. Presentation and Clarity

---

## 0:00 - 0:30 | 1. Problem, Impact & Theme Alignment (Audiovisual Heritage)
> "Judges, across the world, thousands of traditional culinary recipes, weaving styles, and artisan crafts exist only in spoken words and the hands of our elders. They are recorded on family phones or social media, but they are not written down in cookbooks or instruction manuals. When oral knowledge remains unstructured in video files, it is impossible to search, translate, or preserve faithfully.
> 
> We built **Craft Keeper** to turn short video recordings of people demonstrating traditional crafts into structured, editable how-to guides—capturing living heritage while keeping the maker's authentic voice, measurements, and spoken tips intact."

---

## 0:30 - 1:15 | 2. Working Demo & UX
> *"Let's see it work in real time."*
> *(Click "Load Sample Result (Demo Mode)" on `http://127.0.0.1:7860`)*
> 
> "Notice how quickly this loads. We specifically built an offline **Demo Mode** so judges and fieldworkers can test the full pipeline with zero model latency and zero internet dependency.
> 
> Look at the structure:
> 1. At the top: an explicit **Credit line** attributing the knowledge to the artisan, their community, and geographic place.
> 2. Below that: the **'How This Was Made'** provenance box, showing exactly which model pipeline ran and how many visual frames were analyzed.
> 3. An editable **Ingredients Table** and **Numbered Steps Table** with approximate timestamps and authentic spoken tips.
> 4. And critically: this highlighted **'Please Check These'** box. The model flagged that cardamom addition and flour roasting levels were ambiguous. Instead of hallucinating, it explicitly asked for human review."
> *(Click '⬇️ Download Markdown' to show the clean export)*

---

## 1:15 - 2:00 | 3. Use of Open Source & Technical Engineering
> "Every component of Craft Keeper is 100% open source under permissive licenses:
> - **Gemma 4**: The open-weights foundation model released under the Apache 2.0 license.
> - **Faster-Whisper**: For local, CPU-efficient speech-to-text.
> - **FFmpeg**: Handled through a dual-resolution strategy—it checks system PATH first, and seamlessly falls back to a bundled `imageio-ffmpeg` binary so it runs out-of-the-box on Windows, Linux, and macOS without installing system packages.
> - **Pydantic v2**: Enforces strict schema validation with an automated one-shot error-correction retry loop if JSON parsing fails.
> 
> On this 8 GB RAM laptop with an integrated Intel GPU, we benchmarked real memory use: Whisper `base` ran on CPU in 33 seconds for a 1-minute clip, using only 151 MB of peak RAM, and was immediately freed from memory before Gemma was invoked."

---

## 2:00 - 2:40 | 4. Responsible AI & Honesty
> "In traditional heritage archiving, ethical stewardship is paramount:
> 1. **Gated Consent**: The 'Generate' button remains disabled until the user explicitly confirms permission from the recorded person.
> 2. **Right to Anonymity**: Elders who do not wish to have their names published can check 'Keep knowledge holder anonymous', which replaces their personal name with 'Anonymous' across all exports.
> 3. **Honest Limitations**: We do not claim this works magically on every language. As tested on regional Indian terminology, small speech models can phonetically misspell words (like *'kadai'* transcribed as *'cadet'*). We document this limitation openly and insist on human review.
> 4. **Honest Model Labeling**: If hosted Gemma is used, it is labeled `whisper+gemma-hosted`. If direct audio is sent to Gemini, it is labeled `gemini-fallback`. We never claim Gemini output is Gemma."

---

## 2:40 - 3:00 | 5. Conclusion & Presentation Clarity
> "Craft Keeper is available today on GitHub under the Apache 2.0 license, with a complete 20-test automated suite, documentation, and a ready-to-run mock mode that requires no API keys or setup.
> 
> It bridges the gap between spoken tradition and digital preservation. Thank you, and we welcome your questions!"
