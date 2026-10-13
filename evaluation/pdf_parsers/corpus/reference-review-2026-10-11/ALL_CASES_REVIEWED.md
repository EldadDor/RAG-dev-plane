# pdf-001 - 10-common-hibernate-mistakes-that-cripple-your-performance-free.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/10-common-hibernate-mistakes-that-cripple-your-performance-free.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-001.md)

Status: reviewed candidate; human source verification pending.

## pdf-001-q1

Question: What is Mistake 1, and what does the document recommend to fix it?

Answerable: Yes

Required answer facts:

- Mistake 1 is "Use Eager Fetching"
- The recommended fix is to use FetchType.LAZY instead, which delays initialization of the relationship until it's used in business code

Evidence (page numbers are PDF viewer numbers):

- Page 1: PDF viewer page 1 — "Mistake 1: Use Eager Fetching / The FetchType defines when Hibernate initializes an association. You can specify with the fetch attribute of the @OneToMany, @ManyToOne, @ManyToMany and @OneToOne annotation. Hibernate loads eagerly fetched associations when it loads an entity... Better use FetchType.LAZY instead. It delays the initialization of the relationship until you use it in your business code."

Changes / review notes:

- Required facts narrowed to the mistake and recommended fix asked for.

Human verifier: pending. Verification date: pending.

## pdf-001-q2

Question: According to the document, how can you limit the number of records returned by a JPQL query, since JPQL doesn't support OFFSET and LIMIT keywords?

Answerable: Yes

Required answer facts:

- JPQL does not support the OFFSET and LIMIT keywords used in SQL
- To limit records, you set the information on the Query interface rather than in the JPQL statement itself
- The code example shows using .setMaxResults(5) and .setFirstResult(0) on the query

Evidence (page numbers are PDF viewer numbers):

- Page 2: PDF viewer page 2 — "Mistake 4: Select More Records Than You Need / JPQL doesn't support the OFFSET and LIMIT keywords you use in your SQL query... You just need to set this information on the Query interface and not in the JPQL statement." Boxed code: List<Author> authors = em.createQuery("SELECT a FROM Author a ORDER BY a.id ASC", Author.class).setMaxResults(5).setFirstResult(0).getResultList();

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-001-q3

Question: What percentage performance improvement does using bind parameters typically provide compared to not using them?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: The document explains bind-parameter optimization but states no percentage improvement. Human verifier must check all six pages for any numeric bind-parameter benchmark.

Changes / review notes:

- Normalized abstention to empty fact/evidence lists, document scope and an explicit reason; human absence verification remains pending.

Human verifier: pending. Verification date: pending.



---

# pdf-002 - 9rules.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/9rules.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-002.md)

Status: reviewed candidate; human source verification pending.

## pdf-002-q1

Question: מה נמצא בקופסת המשחק, וכמה אסימוני צורות יש?

Answerable: Yes

Required answer facts:

- בקופסה יש 54 קלפים וקופסת קלפים אחת
- יש 9 אסימוני צורות ב-3 צורות ו-3 צבעים
- יש קובייה אחת עבור הגרסה למתחילים
- יש 2 קוביות עבור המשחק הבסיסי

Evidence (page numbers are PDF viewer numbers):

- Page 1: עמוד PDF 1 — "מה בקופסה: 54 קלפים, קופסת קלפים 1... 9 אסימוני צורות ב-3 צורות ב-3 צבעים... קובייה עבור 1 הגרסה למתחילים... קוביות עבור 2 המשחק הבסיסי"

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-002-q2

Question: כיצד בודקים את התשובות הנכונות בסיום כל סבב במשחק הבסיסי?

Answerable: Yes

Required answer facts:

- לאחר שכל המשתתפים בחרו אסימון (או בחרו לא לקחת אסימון), הופכים את הקלף
- התשובות לכל השאלות מופיעות בגב הקלף (בחלק התחתון עבור גרסת המשחק הבסיסי)
- אם השאלות על שתי הקוביות שונות — ייתכנו 2 תשובות נכונות, ואז משתתף אחד מקבל את קלף השאלה והמשתתף השני מקבל קלף חדש מהקופסה
- אם אותה שאלה מופיעה על שתי הקוביות — יש תשובה נכונה אחת בלבד, והמשתתף המחזיק באסימון הנכון מקבל את קלף השאלה

Evidence (page numbers are PDF viewer numbers):

- Page 2: עמוד PDF 2 — "הפכו את הקלף. התשובות לכל השאלות מופיעות בגב הקלף... בדקו מהן התשובות הנכונות לשאלות של הסבב הזה... אם השאלות המופיעות על הקוביות שונות, יש 2 תשובות נכונות... אם אותה השאלה מופיעה על שתי הקוביות, קיימת תשובה נכונה אחת בלבד"

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-002-q3

Question: מהו משך הזמן המומלץ (בדקות) עבור הטיימר בגרסת "הוראות משחק ליחיד"?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: Solo rules on page 4 allow an optional timer to track personal records without prescribing a duration. The separate duel mode specifies two minutes; do not transfer that duration to solo mode. Human verifier must confirm all four pages.

Changes / review notes:

- Normalized abstention to empty fact/evidence lists, document scope and an explicit reason; human absence verification remains pending.

Human verifier: pending. Verification date: pending.



---

# pdf-003 - Alpha_Casino_LeadMagnet_V28.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Alpha_Casino_LeadMagnet_V28.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-003.md)

Status: reviewed candidate; human source verification pending.

## pdf-003-q1

Question: According to the floor diagram on page 8, what are the labeled areas/systems shown in the "End-to-End Connection" illustration?

Answerable: Yes

Required answer facts:

- Restaurant Menu Boards
- Bar
- Video Walls
- Table Games
- Cashier Cages
- Slot Systems
- Column Wrap
- Audio
- Sports Book
- Large Format Exterior LED
- Porte Cochère
- Valet Queueing/Signage
- Registration Desk
- Touchscreen Wayfinding
- In-Room Television
- Meeting Room
- Theater

Evidence (page numbers are PDF viewer numbers):

- Page 8: End-to-End Connection: visible leader-line labels: Restaurant Menu Boards; Bar; Video Walls; Table Games; Cashier Cages; Slot Systems; Column Wrap; Audio; Sports Book; Large Format Exterior LED; Porte Cochère; Valet Queueing/Signage; Registration Desk; Touchscreen Wayfinding; In-Room Television; Meeting Room; Theater

Changes / review notes:

- Bar and Video Walls are separate visible labels. Audio is a label; the source does not label it a connecting element across the whole diagram.

Human verifier: pending. Verification date: pending.

## pdf-003-q2

Question: What is the stated purpose of this guide, as described in the introduction on page 2?

Answerable: Yes

Required answer facts:

- A connected, end-to-end technology solution is essential to delivering a differentiated casino guest experience that advances strategic objectives
- The guide applies whether a property is building new or upgrading existing infrastructure
- The best way to drive engagement is through careful planning
- The guide provides key questions to consider during the planning process, plus guidance for realizing a casino technology vision

Evidence (page numbers are PDF viewer numbers):

- Page 2: PDF viewer page 2 — "Unifying audio, visual, content, control, and design / A connected, end-to-end technology solution is essential to delivering a truly differentiated casino guest experience that advances your strategic objectives. Whether you're building a new property or upgrading your existing infrastructure, the best way to drive engagement is through careful planning. This guide provides key questions to consider in the planning process, along with guidance for making your casino technology vision possible."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-003-q3

Question: What specific bandwidth or network latency thresholds does page 9 recommend for IP-based audio/video system design in a casino?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: Page 9 gives qualitative design questions, without numeric bandwidth or latency thresholds. Question is expressly scoped to page 9; unrelated networking content is not an answer.

Changes / review notes:

- Normalized abstention to empty fact/evidence lists, document scope and an explicit reason; human absence verification remains pending.

Human verifier: pending. Verification date: pending.



---

# pdf-004 - Catalogue_of_Czech_TOYS-and-GAMES.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Catalogue_of_Czech_TOYS-and-GAMES.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-004.md)

Status: reviewed candidate; human source verification pending.

## pdf-004-q1

Question: What is the ETS Trains company's specialization, and what materials/characteristics define their railway models?

Answerable: Yes

Required answer facts:

- The company focuses on small series production of railway locomotives and wagons, making the models both toys and collector's items
- ETS manufactures electric railway models in "0" gauge (TinPlate Model Railway "0" Gauge), designed according to actual locomotives and wagons
- The models are robust and all-metal, with attention paid to electrical and mechanical parts; a significant part of production is done by hand

Evidence (page numbers are PDF viewer numbers):

- Page 24: Document page 24 — "The producer of the ETS model railway has been operating on the market for over 25 years... The company manufactures electric RAILWAY models in the size of '0'... The ETS railroad models are robust, and all-metal... A significant part of the production is made by hand production."

Changes / review notes:

- Removed company age from required facts because the question asks specialization/materials.

Human verifier: pending. Verification date: pending.

## pdf-004-q2

Question: Who is considered the father of Czech puppetry, and what is significant about his family's legacy?

Answerable: Yes

Required answer facts:

- Matěj Kopecký is considered the father of Czech puppetry
- In the first half of the 19th century, he spread Czech culture through his work in the countryside
- This activity was passed down as a family craft by the Kopecký family, now entering its eighth generation
- In 2009, the family founded the ensemble Cirk La Putyka in Prague, devoted to the new circus genre, blending acrobatics, modern dance, puppet theatre, concert, and sport
- The ensemble has performed internationally, including in China (Shanghai), Australia, Brazil, and France

Evidence (page numbers are PDF viewer numbers):

- Page 33: Document page 33 — "Matěj Kopecký is considered the father of Czech puppetry. In the first half of the 19th century he spread Czech culture through his work in the countryside. This activity was passed down as a family craft by the Kopecký family and today it is entering its eighth generation. In 2009, they founded the ensemble Cirk La Putyka in Prague..."

Changes / review notes:

- Added PDF viewer page 33 to inspection pages. Source is the same 48-page catalog; photographs and page count are confirmed visually.

Human verifier: pending. Verification date: pending.

## pdf-004-q3

Question: What is listed as "Contents" entry #4 in the catalogue's table of contents, and on what page does it begin?

Answerable: Yes

Required answer facts:

- Contents entry 4 is "METAL AND TECHNICAL TOYS"
- It begins on page 21

Evidence (page numbers are PDF viewer numbers):

- Page 3: Document page 3 — "CONTENT / 1. TOYS AND GAMES IN THE CZECH REPUBLIC 8 / 2. WOODEN TOYS 12 / 3. PLUSH AND CLOTH TOYS 18 / 4. METAL AND TECHNICAL TOYS 21 / 5. MODELS AND GAMES 25..."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.



---

# pdf-005 - Full Process for Coding with AI Coding Assistants.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Full Process for Coding with AI Coding Assistants.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-005.md)

Status: reviewed candidate; human source verification pending.

## pdf-005-q1

Question: What Golden Rules does the guide list on PDF viewer page 1 for working with AI coding assistants?

Answerable: Yes

Required answer facts:

- Use markdown files to manage the project: README.md, PLANNING.md, TASK.md
- Keep files under 500 lines; split into modules when needed
- Start fresh conversations often, since long threads degrade response quality
- Don't overload the model — one task per message is ideal
- Test early, test often — every new function should have unit tests
- Be specific in requests; more context and examples help a lot
- Write docs and comments as you go; don't delay documentation
- Implement environment variables yourself; don't trust the LLM with API keys

Evidence (page numbers are PDF viewer numbers):

- Page 1: PDF viewer page 1 — "1. 🔑 Golden Rules / These are the high-level principles that guide how to work with AI tools efficiently and effectively... Use markdown files to manage the project (README.md, PLANNING.md, TASK.md). Keep files under 500 lines... Start fresh conversations often... Don't overload the model... Test early, test often... Be specific in your requests... Write docs and comments as you go... Implement environment variables yourself. Don't trust the LLM with API keys."

Changes / review notes:

- Question broadened to ask the complete Golden Rules list, matching its eight required facts.

Human verifier: pending. Verification date: pending.

## pdf-005-q2

Question: What is the purpose of PLANNING.md, and how should the AI be prompted to use it?

Answerable: Yes

Required answer facts:

- PLANNING.md's purpose is to capture the high-level vision, architecture, constraints, tech stack, and tools
- The suggested prompt to the AI is: "Use the structure and decisions outlined in PLANNING.md."
- The LLM should be instructed to reference this file at the beginning of any new conversation
- The global rules reinforce this by stating: "Always read PLANNING.md at the start of a new conversation to understand the project's architecture, goals, style, and constraints."

Evidence (page numbers are PDF viewer numbers):

- Page 2: PDF viewer page 2 — "PLANNING.md / Purpose: High-level vision, architecture, constraints, tech stack, tools, etc. Prompt to AI: 'Use the structure and decisions outlined in PLANNING.md.' Have the LLM reference this file at the beginning of any new conversation."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-005-q3

Question: What specific MCP servers are listed as "primary" in the guide's MCP configuration section on page 5, and what does each one enable the AI assistant to do?

Answerable: Yes

Required answer facts:

- A server to crawl and leverage external knowledge (library/tool documentation)
- A server to manage Supabase (create databases, make new tables, etc.)
- A server to search the web (described as great for pulling documentation), using Brave
- The document states: "Those three are my primary MCP servers."

Evidence (page numbers are PDF viewer numbers):

- Page 5: PDF viewer page 5 (note: numbered as section "4. 🧰 Configuring MCP" in the body text, physically appearing before the "Initial Prompt" section) — "MCP enables your AI assistant to interact with services to do things like: Crawl and leverage external knowledge (library/tool documentation)... Manage your Supabase (create databases, make new tables, etc.)... Search the web (great for pulling documentation) with Brave... Those three are my primary MCP servers. Here are a couple other useful ones: File system MCP... Git MCP..."

Changes / review notes:

- Removed non-primary servers from required facts; they are not requested.

Human verifier: pending. Verification date: pending.



---

# pdf-006 - gurkan03tableschairs.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/gurkan03tableschairs.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-006.md)

Status: reviewed candidate; human source verification pending.

## pdf-006-q1

Question: On PDF viewer page 2 (printed pages 122/123), what are the back height, seat height, seat width, and seat depth (in mm) of the CHR.02/H95 chair model?

Answerable: Yes

Required answer facts:

- Back height: 950 mm
- Seat height: 620 mm
- Seat width: 380 mm
- Seat depth: 355 mm

Evidence (page numbers are PDF viewer numbers):

- Page 2: PDF viewer page 2 (printed pages 122/123) — "catalogue code CHR.01 CHR.02 CHR.02/H95 ... tube ø 21 ø 21 ø 25 ... using place general general cafe ... back height (mm) 785 780 950 ... seat height (mm) 450 450 620 ... seat width (mm) 385 380 380 ... seat depth (mm) 380 355 355"

Changes / review notes:

- Only the four requested chair dimensions are required; model identity is already in the question.

Human verifier: pending. Verification date: pending.

## pdf-006-q2

Question: On PDF viewer page 6 (printed pages 130/131), what are the width and depth (in mm) of the widest rectangle table in the "600 mm Deep" standard square-leg series?

Answerable: Yes

Required answer facts:

- Width: 2000 mm.
- Depth: 600 mm.

Evidence (page numbers are PDF viewer numbers):

- Page 6: PDF viewer page 6 (printed pages 130/131) — "RECTANGLE TABLES - 600 mm DEEP / catalogue code MTB.R.106 MTB.R.126 MTB.R.146 MTB.R.166 MTB.R.186 MTB.R.206 ... height (mm) 750 750 750 750 750 750 / width (mm) 1000 1200 1400 1600 1800 2000 / depth (mm) 600 600 600 600 600 600"

Changes / review notes:

- Only the requested width/depth are required; height/model code are optional context.

Human verifier: pending. Verification date: pending.

## pdf-006-q3

Question: On PDF viewer page 6, which standard features and packaging are listed for Standard Tables (square leg), and what optional upgrade is available?

Answerable: Yes

Required answer facts:

- Core features: Durable Metal Frame Construction; Electrostatic Powder Coating; Square Tube Legs; Levelling Feet under Tubes; 25 mm Wooden Top; 2 mm Edgebanding; Easy Assembly
- Packaging: Flatpack in Corrugated Carton; Delivery on Pallet
- Optional feature: Chrome-Plated Legs

Evidence (page numbers are PDF viewer numbers):

- Page 6: PDF viewer page 6 (printed pages 130/131) — "FEATURES » Durable Metal Frame Construction » Electrostatic Powder Coating » Square Tube Legs » Levelling Feet under Tubes » 25 mm Wooden Top » 2 mm Edgebanding » Easy Assembly » Packaging: Flatpack in Corrugated Carton » Delivery on Pallet / OPTIONAL » Chrome-Plated Legs"

Changes / review notes:

- Question made explicit about listing standard features and packaging, matching the proposed facts.

Human verifier: pending. Verification date: pending.



---

# pdf-007 - Herbrew_Casino1.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Herbrew_Casino1.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-007.md)

Status: reviewed candidate; human source verification pending.

## pdf-007-q1

Question: מהו הטיעון הכלכלי התומך העוסק בגידול בהכנסות המדינה כתוצאה מהסדרה חוקית של ענף ההימורים?

Answerable: Yes

Required answer facts:

- לגליזציה והסדרה בחוק של הימורים ימנעו גלגול כספים לא מדווחים.
- כיום מתגלגל כסף רב בענף ההימורים הלא חוקיים בארץ, והמדינה מפסידה מסים רבים.

Evidence (page numbers are PDF viewer numbers):

- Page 2: עמוד PDF 2 (עמוד מודפס 1), תחת "2.1 טיעונים כלכליים" — "לגליזציה והסדרה בחוק של הימורים ימנעו גלגול כספים לא מדווחים... מכיוון שכבר כיום מתגלגל כסף רב בענף ההימורים הלא חוקיים בארץ, המדינה מפסידה מסים רבים."

Changes / review notes:

- Corrected illegal money to unreported money; narrowed grading to the state-tax argument actually asked for.

Human verifier: pending. Verification date: pending.

## pdf-007-q2

Question: מהו הטיעון החברתי המתנגד העוסק בהתמכרות להימורים והשלכותיה על המהמר ומשפחתו?

Answerable: Yes

Required answer facts:

- מחקרים מראים כי ניתן להתמכר להימורים, והדבר יוצר שורה של בעיות הן עבור המהמר המכור והן עבור סביבתו הקרובה והרחוקה
- מהמר כפייתי פוגע בתפקודו המשפחתי ובהכנסתה הכלכלית של המשפחה
- לעיתים הוא עלול להיגרר לתגובות רגשיות קיצוניות עקב מצוקה כלכלית או רגשית הנגרמת מההימורים הכפייתיים
- אנשים כאלו מתקשים לשמור על עבודה סדירה, ועלותם לחברה גבוהה בשל הצורך בשיקום, גמילה ושיטור
- מחקר אמריקאי מצא כי אחוז פושטי הרגל היה גבוה ב-18 אחוזים במחוזות עם מוסד הימורים אחד, וגבוה ב-35 אחוזים במקומות עם למעלה מחמישה מוסדות הימורים, לעומת הממוצע הארצי

Evidence (page numbers are PDF viewer numbers):

- Page 5: 3.2 טיעונים חברתיים: התמכרות והתנהגות חברתית בעייתית. מהמר כפייתי פוגע בתפקודו המשפחתי, בהכנסתה הכלכלית של המשפחה; עלול להיגרר לתגובות רגשיות קיצוניות; מתקשה לשמור על עבודה סדירה; צורכי שיקום וגמילה ושיטור. הערת שוליים 8: אחוז פושטי הרגל גבוה ב-18 אחוזים מהממוצע הארצי במחוז עם מוסד הימורים אחד וב-35 אחוזים במקומות עם מעל חמישה מוסדות.

Changes / review notes:

- Social-arguments paragraph and footnote are on PDF viewer page 5 (printed page 4), not viewer page 4.

Human verifier: pending. Verification date: pending.

## pdf-007-q3

Question: מהו המקור המצוטט לטענה כי אחוז פושטי הרגל גבוה יותר במחוזות עם נוכחות מוסדות הימורים, ומהו מספר העמוד המצוין במקור?

Answerable: Yes

Required answer facts:

- John J Egan, State-sanctioned gambling is a bad bet, U.S. Catholic, Nov 1997, p. 25.
- המקור מופיע בהערת שוליים 8, בעמוד PDF 5 (מודפס 4).

Evidence (page numbers are PDF viewer numbers):

- Page 5: הערת שוליים 8: John J Egan State-sanctioned gambling is a bad bet U.S. Catholic; Nov 1997 p 25.

Changes / review notes:

- Fully answerable from footnote 8 on PDF viewer page 5. Removed unrelated duplicate-citation requirement.

Human verifier: pending. Verification date: pending.



---

# pdf-008 - imc_telemetry-solutions_EN-201810_WEB.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/imc_telemetry-solutions_EN-201810_WEB.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-008.md)

Status: reviewed candidate; human source verification pending.

## pdf-008-q1

Question: What is the maximum free-field transmission distance of the CTP high-speed radio telemetry system, and what supply voltage does it need?

Answerable: Yes

Required answer facts:

- Distances of up to 2000 m in free field are possible.
- The power supply is external, 10 to 30 VDC.

Evidence (page numbers are PDF viewer numbers):

- Page 10: CTP: distances of up to 2000 m in free field are possible. The power supply is external with 10 to 30 VDC.

Changes / review notes:

- CTP uses external 10–30 VDC on viewer page 10. The battery box is on page 11 for CTP-Rotate, a different variant; the submitted conflict warning was mistaken.

Human verifier: pending. Verification date: pending.

## pdf-008-q2

Question: Which output interfaces does the Dx telemetry receiver unit offer, and how can it be configured?

Answerable: Yes

Required answer facts:

- The receiver offers an Ethernet output.
- The receiver offers a CAN interface.
- The receiver offers analog outputs.
- Configuration is done via Ethernet and a standard web browser.

Evidence (page numbers are PDF viewer numbers):

- Page 12: Receiver unit: As outputs, the receiver offers an Ethernet and a CAN interface as well as analog outputs. The configuration can be done easily via Ethernet and a standard web-browser.

Changes / review notes:

- Confirmed receiver outputs and configuration on viewer page 12; unrelated diagram labels removed.

Human verifier: pending. Verification date: pending.

## pdf-008-q3

Question: What is the list price of the CTP-Rotate telemetry system, and which Wi-Fi standard does its receiver use?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: No list price or Wi-Fi standard is stated for CTP-Rotate in the submitted evidence. Radio frequency is not an IEEE 802.11 standard. Human verifier must check all 20 pages, including figures, for the absence of both requested items.

Changes / review notes:

- Normalized abstention to empty fact/evidence lists, document scope and an explicit reason; human absence verification remains pending.

Human verifier: pending. Verification date: pending.



---

# pdf-009 - Maven, IntelliJ Build & Run Guide-2.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Maven, IntelliJ Build & Run Guide-2.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-009.md)

Status: reviewed candidate; human source verification pending.

## pdf-009-q1

Question: Before building or running a project in IntelliJ, what should you do first, and which Maven commands does the guide say to start with?

Answerable: Yes

Required answer facts:

- Always start with either MVI (mvn install) or MVC (mvn clean install).
- Only after a successful compilation on the command line should you build or run the project in IntelliJ.

Evidence (page numbers are PDF viewer numbers):

- Page 1: Heading "1. Starting with Maven": "Always start with either MVI (mvn install) or MVC (mvn clean install)."
Heading "2. Building in IntelliJ": "Only after a successful compilation in the command line should you attempt to build/run the project in IntelliJ."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-009-q2

Question: Where in IntelliJ do you check the compiler memory, and what is the minimum it should be?

Answerable: Yes

Required answer facts:

- The compiler memory should be at least 1024m.
- The setting is at Settings -> Compiler -> Build Process -> Memory/Heap.

Evidence (page numbers are PDF viewer numbers):

- Page 1: Heading "2.1 Build in IntelliJ: Potential Problems", sub-heading "Solutions", item 2: "Ensure that the memory allocated for the compiler is at least 1024m. Check this in: Settings -> Compiler -> Build Process -> Memory/Heap."
Related item for the Maven side, under "1. Starting with Maven" > "Solutions", item 3: MAVEN_OPTS should be at least 1024m. Avoid confusing the two in grading.

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-009-q3

Question: What is the difference between the memory the CRM server needs and what JIDI needs when running, and where do you set it?

Answerable: Yes

Required answer facts:

- The CRM server requires at least 1536m.
- JIDI is fine with 1024m.
- You adjust the values with -Xmx in the running configuration of each server.

Evidence (page numbers are PDF viewer numbers):

- Page 1: Heading "2.2 Running Problems", item 1: "Running fails with memory issues after the server starts: The CRM server requires at least 1536m, while JIDI is fine with1024m. Adjust the values in the running configuration for each server using -Xmx." The missing space in "with1024m" is in the original text.

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.



---

# pdf-010 - phillippine_weather_PAGASA.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/phillippine_weather_PAGASA.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-010.md)

Status: reviewed candidate; human source verification pending.

## pdf-010-q1

Question: What is the forecast weather condition for Metro Manila in the PAGASA 24-hour public weather forecast issued at 4:00 PM on October 10, 2026 (valid until 4:00 PM October 11, 2026)?

Answerable: Yes

Required answer facts:

- Weather condition: Cloudy skies with scattered rains and thunderstorms
- Cause: the Low Pressure Area (LPA)
- Impact/hazard: possible flash floods or landslides due to moderate to at times heavy rains

Evidence (page numbers are PDF viewer numbers):

- Page 1: PDF viewer page 1, "FORECAST WEATHER CONDITION" table — "Metro Manila, Visayas, CALABARZON, Bicol Region, Marinduque, Romblon, Occidental Mindoro, and Oriental Mindoro | Cloudy skies with scattered rains and thunderstorms | LPA | Possible flash floods or landslides due to moderate to at times heavy rains"

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-010-q2

Question: According to the forecast wind and coastal water condition table, what is the wind intensity, direction, and coastal wave height range for Northern Luzon and the eastern section of Central Luzon?

Answerable: Yes

Required answer facts:

- Winds intensity: Moderate to Strong
- Winds direction: Northeast to East
- Coastal waters: Moderate to Rough, 1.5 to 2.8 meters

Evidence (page numbers are PDF viewer numbers):

- Page 1: PDF viewer page 1, "FORECAST WIND AND COASTAL WATER CONDITION" table — "Northern Luzon and the eastern section of Central Luzon | Moderate to Strong | Northeast to East | Moderate to Rough (1.5 to 2.8 meters)"

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-010-q3

Question: What is the predicted low-tide time and height for Manila Bay "Today" (October 10, 2026)?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: The Today column for Manila Bay tide predictions on page 1 contains dashes for low-tide time/height. Tomorrow values must not be substituted. No explanation for the dashes is given; removed the speculative reason about publication time.

Changes / review notes:

- Normalized abstention to empty fact/evidence lists, document scope and an explicit reason; human absence verification remains pending.

Human verifier: pending. Verification date: pending.



---

# pdf-011 - Print-Ready-file-for-Know-the-Odds-4pg-brochure__165223_GAMING_V01.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Print-Ready-file-for-Know-the-Odds-4pg-brochure__165223_GAMING_V01.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-011.md)

Status: reviewed candidate; human source verification pending.

## pdf-011-q1

Question: In the brochure's table of typical U.S. casino house advantages, what is the house advantage for Double Zero roulette, and how much can a player expect to lose per $100 bet?

Answerable: Yes

Required answer facts:

- The house advantage for Double Zero roulette is 5.3%.
- A player can lose $5.30 for every $100 bet.

Evidence (page numbers are PDF viewer numbers):

- Page 2: Table heading: "If you are a player with average skills, playing under standard rules, typical house advantages in U.S. casinos might be:"
Row under the ROULETTE group: "Double Zero | 5.3% | $5.30". The columns are headed "HOUSE ADVANTAGE" and "EVERY $100 BET, A PLAYER CAN LOSE".

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-011-q2

Question: What assumptions does the brochure make about player strategy for games with decisions like blackjack, and about rule or pay variations in games like slot machines, when stating house advantages?

Answerable: Yes

Required answer facts:

- For games with player decisions (for example blackjack and video poker), an "average player" strategy is assumed.
- For games with rule or pay variations (for example slot machines), a typical offering is assumed.
- An operator may, subject to governmental requirements, provide a greater or lower house advantage, and actual house advantages and hold percentages may vary.

Evidence (page numbers are PDF viewer numbers):

- Page 1: Note: For games with strategic decisions (e.g., blackjack, video poker), an “average player” strategy is assumed. For games in which rule/pay variations exist (e.g., slot machines), a typical offering is assumed although an operator may, subject to governmental requirements, provide for a greater or lower house advantage. Actual house advantages and hold percentages may vary.

Changes / review notes:

- Completed the note from the visible source; panel break is not a missing sentence.

Human verifier: pending. Verification date: pending.

## pdf-011-q3

Question: What does the asterisk on “EVERY $100 BET, A PLAYER CAN LOSE*” mean, and does the table figure guarantee what an individual will lose?

Answerable: Yes

Required answer facts:

- The figures show the percentage nature of the house advantage.
- They represent what the hypothetical, average player can expect to lose for each $100 wagered over a reasonable period of time.
- They are not a guarantee: an average individual may lose more or less than the average house advantage.
- Other factors also influence the loss: length of time playing, speed of play, skill and amount wagered.

Evidence (page numbers are PDF viewer numbers):

- Page 2: The footnote reads, "These figures illustrate the percentage nature of the house advantage, and they represent the amount of money that the hypothetical, average player can expect to lose, for each $100 wagered, over a reasonable period of time. There are other factors, such as length of time spent playing, speed of play, skill and amount wagered that can also influence the amount of money a player loses. … An average individual may lose more or less than the average house advantage."

Changes / review notes:

- Preserved the literal asterisk in the table-header question.

Human verifier: pending. Verification date: pending.



---

# pdf-012 - Qwopus3-5-27b-Colab_complete_guide_to_llm_finetuning.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Qwopus3-5-27b-Colab_complete_guide_to_llm_finetuning.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-012.md)

Status: reviewed candidate; human source verification pending.

## pdf-012-q1

Question: In the guide's opening fine-tuning diagram, what are the stages of the flow, and what does the LoRA / PEFT step do?

Answerable: Yes

Required answer facts:

- The flow runs from the Base LLM (pretrained) and the Training Data (domain / task) into Fine-tuning, which produces the Adapted Model.
- The LoRA / PEFT step trains a small adapter.
- The adapted model is the base plus the adapter, which is better on your tasks.

Evidence (page numbers are PDF viewer numbers):

- Page 1: Diagram labels: "Base LLM (pretrained)", "Training Data (domain / task)", "Fine-tuning", "LoRA / PEFT: train a small adapter", "Adapted Model", "base + adapter (better on your tasks)", with "+" joining the first two boxes.
Caption: "LLM Fine-tuning: adapt a pretrained LLM to your domain with task-specific data (often by training a small LoRA adapter)."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-012-q2

Question: According to the guide's description of Unsloth, what training speedup and VRAM savings does it report, and which training methods and tooling does it remain compatible with?

Answerable: Yes

Required answer facts:

- It reports around 2× training speedups.
- It reports VRAM savings commonly near 70%, with RL workflows often claiming 50–90%.
- It remains compatible with Hugging Face/TRL workflows including SFT, GRPO, GSPO and DPO.

Evidence (page numbers are PDF viewer numbers):

- Page 2: Heading "1 Prerequisites and Platform Overview", then "1.1 What is Unsloth?"
Callout "Unsloth: quick summary": "…around 2× training speedups and large VRAM savings (commonly reported near 70%, with RL workflows often claiming 50–90%)… it still provides 250+ notebooks and broad support across 500+ models."
Body text: "…remaining compatible with Hugging Face/TRL workflows including SFT, GRPO, GSPO, and DPO."

Changes / review notes:

- Removed notebook/model counts from mandatory grading because the question asks speed/VRAM/method compatibility.

Human verifier: pending. Verification date: pending.

## pdf-012-q3

Question: In the guide's dataset configuration code, what are MAX_CONTEXT_WINDOW and the sample count for each of the three datasets?

Answerable: Yes

Required answer facts:

- MAX_CONTEXT_WINDOW = 8192.
- ds1 is 3900 samples, from nohurry/Opus-4.6-Reasoning-3000x-filtered.
- ds2 is 700 samples, from Jackrong/Qwen3.5-reasoning-700x.
- ds3 is 9633 samples, from Roman1111111/claude-opus-4.6-10000x.

Evidence (page numbers are PDF viewer numbers):

- Page 13: Code: Configuration and dataset loading, lines 9, 11–15: MAX_CONTEXT_WINDOW = 8192; num_samples_dict = {"ds1": 3900, # nohurry/Opus-4.6-Reasoning-3000x-filtered; "ds2": 700, # Jackrong/Qwen3.5-reasoning-700x; "ds3": 9633, # Roman1111111/claude-opus-4.6-10000x}.

Changes / review notes:

- Configuration values are visually present on viewer page 13; code starts and continues on later pages but these values do not cross the boundary.

Human verifier: pending. Verification date: pending.



---

# pdf-013 - t4.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/t4.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-013.md)

Status: reviewed candidate; human source verification pending.

## pdf-013-q1

Question: מה הן הדוגמאות לסמלים (צורה וצבע) המופיעות בחוברת ההוראות, וכמה דוגמאות סמלים כאלה מוצגות בסך הכל?

Answerable: Yes

Required answer facts:

- מוצגות שבע דוגמאות סמלים.
- אחת כחול; שתיים אדום; שלוש כתום; משולש צהוב; עיגול ירוק; ריבוע סגול; מלבן אדום.

Evidence (page numbers are PDF viewer numbers):

- Page 4: דוגמאות סמלים: אחת כחול; שתיים אדום; שלוש כתום; משולש צהוב; עיגול ירוק; ריבוע סגול; מלבן אדום.

Changes / review notes:

- Examples are on viewer page 4, not 2. There are seven examples, not six. Removed the unsupported three-properties assertion.

Human verifier: pending. Verification date: pending.

## pdf-013-q2

Question: כיצד מתנהל מיני-המשחק "טיול על המסלול" (גרסת סולו), ומה קורה לאחר שמוצאים את הסמל המשותף?

Answerable: Yes

Required answer facts:

- זהו משחק סולו (ליחיד)
- השחקן מניח קלפים לצדו כך שיצרו מסלול
- ניתן לבחור כמה קלפים להשתמש בהם, בהתאם לגיל, להיכרות עם המשחק ולזמן הפנוי
- צריך לחפש את הסמל המשותף לקלף העליון בערימה ולקלף הראשון במסלול
- כאשר מוצאים את הסמל, מכסים את הקלף הראשון במסלול בקלף מהערימה, מניחים אותו הפוך (עם הגב כלפי מעלה), ועוברים לקלף השני במסלול
- ממשיכים באותו אופן עד שכל המסלול מכוסה בקלפים

Evidence (page numbers are PDF viewer numbers):

- Page 5: טיול על המסלול (משחק סולו): ניתן לבחור את מספר הקלפים בהתאם לגיל, להיכרות עם המשחק ולזמן הפנוי.
- Page 6: חפשו את הסמל שמשותף לקלף העליון בערימה שלצדכם ולקלף הראשון במסלול. מצאתם? כסו את הקלף הראשון במסלול עם הקלף שלכם. הניחו אותו הפוך (עם הגב כלפי מעלה) ועברו לקלף השני במסלול. המשיכו באותו האופן עד שתכסו את כל המסלול בקלפים!

Changes / review notes:

- Setup is on viewer page 5 and play/end instructions on page 6.

Human verifier: pending. Verification date: pending.

## pdf-013-q3

Question: איזה ניקוד ניצחון מספרי, במונחי נקודות, מצוין בחוברת עבור מיני-המשחק "מחבואים"?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: החוברת מתארת בעמודים 13–14 זכייה כאשר לשחקן לא נותרו קלפים גלויים, אך אינה מציינת ניקוד ניצחון מספרי במונחי נקודות עבור מחבואים. נדרשת בדיקה אנושית של כל החוברת לפני הקפאה.

Changes / review notes:

- Rewrote the mixed question to ask only the missing numerical score. Hide-and-seek is on viewer pages 13–14; page 8 is a different mini-game.

Human verifier: pending. Verification date: pending.



---

# pdf-014 - Technion_AI_change_cse.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Technion_AI_change_cse.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-014.md)

Status: reviewed candidate; human source verification pending.

## pdf-014-q1

Question: לפי טבלה 1 (תהליך שינוי ארגוני לפי קוטר), מה בוצע ביישום שלב 5 ("הסרת מכשולים ואיפשור פעולה") בהוראת מדעי המחשב?

Answerable: Yes

Required answer facts:

- פתרונות טכנולוגיים קודמו במהירות, ובמקרים של אי הצלחה, נלמדו המקרים והופקו מסקנות
- לאחר שבוט ראשוני נכשל בפיילוט, שולב בוט חדש בשם Stacks, שהוטמע תוך ימים ספורים
- כ-100 מורים הוכשרו להוראה באמצעות הבוט Stacks עד יוני 2025
- נמצא כי חלופת למידה עמוקה בהנדסת תוכנה נלמדת בפועל על ידי כ-500 תלמידים בלבד, ותכניה מציבים קושי מהותי
- גובשה חשיבה מחודשת לשילוב מודלי שפה (LLM) בחלופות נוספות: אפליקציות משולבות נתונים, יישומי טלפונים חכמים, והגנת סייבר

Evidence (page numbers are PDF viewer numbers):

- Page 2: טבלה 1, שלב 5: פתרונות טכנולוגיים קודמו במהירות; לאחר שבוט ראשוני נכשל בפיילוט שולב Stacks תוך ימים ספורים ו-100 מורים הוכשרו ביוני 2025. חלופת למידה עמוקה נלמדת על ידי כ-500 תלמידים; שילוב LLM באפליקציות משולבות נתונים, טלפונים חכמים והגנת סייבר.

Changes / review notes:

- Stage 5 table row is on viewer page 2 (printed 6), not viewer page 1. The question stays scoped to Table 1; later prose uses a different training-date wording.

Human verifier: pending. Verification date: pending.

## pdf-014-q2

Question: לפי איור 1 (ציר הזמן של הפעילויות), אילו שני אירועים התרחשו בחודש פברואר 2025, ומה הקשר התוכני ביניהם?

Answerable: Yes

Required answer facts:

- ב-9.2.25 התקיימה פתיחת השתלמות בסיסית למורי חט"ב – מבוא לפייתון ו-AI
- ב-11.2.25 התקיימה פתיחת השתלמות מתקדמת למורי התיכון בנושא שילוב מודלי שפה (LLM)
- שני האירועים שייכים לשלב 3 (פיתוח חזון ואסטרטגיה) במודל קוטר, כחלק ממרכיב "פיתוח מקצועי למורים"
- ההשתלמות הבסיסית לחט"ב וההשתלמות המתקדמת לתיכון מתוארות כשני מסלולים מקבילים בהיקפים שונים — האחת הכשרה בסיסית, השנייה הכשרה מתקדמת

Evidence (page numbers are PDF viewer numbers):

- Page 4: איור 1: 9.2.25 פתיחת השתלמות בסיסית למורי חט״ב – מבוא לפייתון ו-AI; 11.2.25 פתיחת השתלמות מתקדמת למורי התיכון בנושא שילוב מודלי שפה (LLM).
- Page 5: שלב 3: פיתוח חזון ואסטרטגיה. פיתוח מקצועי למורים: הכשרות בסיסיות לפייתון עם AI ועד השתלמויות מתקדמות לשילוב LLM; השתלמות בסיסית לחטיבת הביניים (9.2.25).
- Page 6: המשך: השתלמות מתקדמת לתיכון (11.2.25).

Changes / review notes:

- Timeline is on viewer page 4 (printed 8); stage-3 prose supporting the connection spans viewer pages 5–6, not 1–2.

Human verifier: pending. Verification date: pending.

## pdf-014-q3

Question: באיזה כלי או שיטת איסוף משוב ספציפית נאסף הנתון שלפיו 85% מהמורים מתכוונים ליישם את הכלים, בהקשר לכנס 4 במאי 2025?

Answerable: No

Required answer facts:

- None (unanswerable).

Evidence (page numbers are PDF viewer numbers):

- None.

Reason / absence check: עמודים 4–5 מציינים ממצאי משוב ו-85% אך לא כלי איסוף מסוים (כגון שאלון או ריאיון). נדרשת בדיקה אנושית של תשעת העמודים כדי לוודא שהשיטה אינה מופיעה במקום אחר.

Changes / review notes:

- Rewrote to ask only the missing feedback method. The 85% value is answerable on pages 4–5 and must not be scored as an abstention.

Human verifier: pending. Verification date: pending.



---

# pdf-015 - Technion_programing_casino.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/Technion_programing_casino.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-015.md)

Status: reviewed candidate; human source verification pending.

## pdf-015-q1

Question: לפי תיאור סוגי הקזינו בשלב ב', מהו כלל הניקוד של "קזינו 3" (7 בום), וכמה נקודות מקבלים כאשר הכלל מתקיים?

Answerable: Yes

Required answer facts:

- קזינו מסוג 3 נקרא "7 בום"
- הכלל: אם סכום 3 המספרים שהוגרלו מתחלק ב-7, או מכיל את הספרה 7, זכינו ב-40 נקודות נוספות

Evidence (page numbers are PDF viewer numbers):

- Page 7: עמוד PDF 7 (בתוך "שלב ב': קבלת פרמטרים", תחת "סוגי הקזינו") — "1. כפי שהגדרנו בשלב הקודם. 2. כמו סוג 1 וגם – אם שלושת המספרים זוגיים אז זכינו ב-2+ נקודות. 3. 7 בום – כלומר אם סכום 3 המספרים שהוגרלו מתחלק ב-7 או מכיל 7 אז זכינו ב-40+ נקודות"

Changes / review notes:

- Removed other casino variants from mandatory facts; they are not requested.

Human verifier: pending. Verification date: pending.

## pdf-015-q2

Question: מהו נתיב התפריט/הפעולות ב-Visual Studio ליצירת אתר האינטרנט החדש עבור משימת הקזינו?

Answerable: Yes

Required answer facts:

- פותחים את Visual Studio ובוחרים File -> New -> Website
- בוחרים בסוג האתר ASP.NET Empty Web Site
- כפתור "Browse" מאפשר למקם את האתר כרצוננו (למשל, ב-Desktop) ולתת לו שם (למשל, MyWebSite)
- בחלונית Solution Explorer, בצד ימין, עומדים על שם האתר, לוחצים ימני עם העכבר ובוחרים Add New Item
- בחלון שנפתח בוחרים Web Form ונותנים לו שם (למשל, Default.aspx)

Evidence (page numbers are PDF viewer numbers):

- Page 2: עמוד PDF 2, "יצירת אתר 'קזינו' בסביבת VisualStudio" — "נפתח את ה-VisualStudio ונבחר file->new->website... ושם נבחר ASP.NET Empty Web Site. כפתור Browse מאפשר לנו למקם את האתר כרצוננו... בצד ימין, בחלון SolutionExplorer, נעמוד על שם האתר, ימני עם העכבר ונבחר: Add New Item. בחלון שנקבל נבחר Web Form"

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-015-q3

Question: בשלב ג׳, מהי פקודת המעבר לדף "כל הכבוד", באיזה דף יש לאפס את ה-Session, ובאיזו פעולה?

Answerable: Yes

Required answer facts:

- פקודת המעבר בצד שרת היא Response.Redirect("win.aspx");.
- יש לאפס את ה-Session בדף הטופס.
- הפעולה היא Session.Abandon().

Evidence (page numbers are PDF viewer numbers):

- Page 9: שלב ג׳: מעברים בין דפים באתר. הפקודה המוצגת: Response.Redirect("win.aspx");. באיזה דף נכון לאפס את הנקודות? ג. מה שנותר – דף הטופס. איפוס כל ה-Session יתבצע ע״י נטישת ה-session, הפעולה Session.Abandon().

Changes / review notes:

- Stage C is on viewer page 9, not 7. Actual redirect target is win.aspx. The printed threshold is ±100, so no unambiguous >=100 reference is inferred; question revised to the explicit redirect/reset instructions.

Human verifier: pending. Verification date: pending.



---

# pdf-016 - חוברת חקלאות מוגבר-חגית חלד.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/חוברת חקלאות מוגבר-חגית חלד.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-016.md)

Status: reviewed candidate; human source verification pending.

## pdf-016-q1

Question: According to the disease-agent comparison table (טבלה מס' 4), how does reproduction differ among viruses, bacteria and fungi?

Answerable: Yes

Required answer facts:

- Viruses reproduce asexually (התרבות אל-מינית).
- Bacteria reproduce asexually (אל-מינית).
- Fungi reproduce both sexually and asexually, through spores (מינית ואל-מינית על ידי נבגים).

Evidence (page numbers are PDF viewer numbers):

- Page 57: Table title: "טבלה מס' 4 – השוואה גורמי מחלה". The columns are "וירוס – נגיף", "חיידק – בקטריה" and "פטרייה". The first row, "גודל ומבנה", gives virus size as nanometer-scale and fungi as nucleated cells.
Reproduction row: "התרבות | אל-מינית | אל-מינית | מינית ואל-מינית על ידי נבגים".

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-016-q2

Question: In the plant hormones summary table (טבלה מס' 7), what does gibberellin (ג'יברלין) promote, and what does it suppress?

Answerable: Yes

Required answer facts:

- Gibberellin promotes stem elongation through cell division.
- It promotes seed germination.
- It promotes development of stamens and fruits.
- It affects flower sex.
- It promotes starch breakdown in seeds.
- It suppresses seed dormancy (תרדמת זרעים).

Evidence (page numbers are PDF viewer numbers):

- Page 88: Column headers: "הורמון | מעודד | מדכא | מבנה כימי".
Row "ג'יברלין": "התארכות הגבעול על ידי חלוקת תאים נביטת זרעים התפתחות אבקנים ופירות השפעה על זוויג הפרח פירוק עמילן בזרעים", and the suppress cell "תרדמת זרעים".

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-016-q3

Question: According to the book's preface, what does Chapter B cover, and when was the preface written?

Answerable: Yes

Required answer facts:

- Chapter B covers the specialization branch for potted plants, including growing potted plants indoors and outdoors.
- It specifically mentions growing bonsai and Venus flytrap (ונוס צמחים).
- The preface is signed Jerusalem, Nisan 5768 (תשס"ח), March 2008.

Evidence (page numbers are PDF viewer numbers):

- Page 2: פרק ב׳ כולל את ענף ההתמחות מיוחד לצמחי עציץ שמחייב התמצאות בגידולים של עציצים בבית ובחוץ ובמיוחד גידול צמח הבונסאי וונוס צמחים. ירושלים, ניסן תשס״ח, מרס 2008.

Changes / review notes:

- Chapter B also explicitly mentions Venus flytrap; added it to the chapter-scope answer.

Human verifier: pending. Verification date: pending.



---

# pdf-017 - שם-קוד.pdf

[Original PDF](<E:/Workspace/AI_Stuff/Pdf_Examples/PDFs/שם-קוד.pdf>) | [Submitted worksheet](../../worksheets-done/pdf-017.md)

Status: reviewed candidate; human source verification pending.

## pdf-017-q1

Question: לפי תיאור הרכיבים בעמוד 2 (PDF), מהו תפקידו של סמן "הסוכן הכפול," וכיצד יש להציב אותו בהכנת המשחק?

Answerable: Yes

Required answer facts:

- סמן הסוכן הכפול הוא מרגל דו-צדדי ששייך לצוות המתחיל
- יש להפוך אותו כך שהצד בצבע המתאים (צבע הצוות המתחיל) יהיה למעלה
- לאחר מכן יש להוסיף אותו לערימת סמני המרגלים המתאימה (בהתאם לצוות המתחיל)

Evidence (page numbers are PDF viewer numbers):

- Page 2: PDF עמוד 2, "סמני מרגלים" — "סמן הסוכן הכפול הוא מרגל דו צדדי ששייך לצוות המתחיל. הפכו אותו כך שהצד בצבע המתאים יהיה למעלה והוסיפו אותו לערימת סמני המרגלים המתאימה." ורשימת הרכיבים: "סמן סוכן כפול 1"

Changes / review notes:

- Removed component-count requirement because the question asks role and setup.

Human verifier: pending. Verification date: pending.

## pdf-017-q2

Question: לפי PDF עמוד 3 (מספור מודפס "2"), כיצד קלף ההצפנה קשור לפריסת הקלפים על השולחן, ומה מייצג כל צבע ריבוע?

Answerable: Yes

Required answer facts:

- קלף ההצפנה מתאים לריבוע של הקלפים שעל השולחן
- ריבועים כחולים מייצגים את המילים שהצוות הכחול צריך לנחש (מרגלים כחולים)
- ריבועים אדומים מייצגים את המילים שהצוות האדום צריך לנחש (מרגלים אדומים)
- ריבועים בהירים מייצגים עוברי אורח תמימים
- הריבוע השחור מייצג את המתנקש שאסור ליצור איתו קשר
- בהכנת המשחק שולפים 25 קלפים באקראי ומניחים אותם בריבוע של 5 על 5

Evidence (page numbers are PDF viewer numbers):

- Page 3: PDF עמוד 3 (מספור מודפס "2"), "מפעילים" — "קלף ההצפנה מתאים לריבוע של הקלפים שעל השולחן. ריבועים כחולים מייצגים את המילים שהצוות הכחול צריך לנחש... ריבועים בהירים מייצגים עוברי אורח תמימים והריבוע השחור מייצג את המתנקש שאסור ליצור איתו קשר!" וכן, "הכנת המשחק" — "שלפו 25 קלפים באקראי והניחו אותם בריבוע של 5 על 5."

Changes / review notes:

- Schema/format normalization only; confirm facts and evidence against the original.

Human verifier: pending. Verification date: pending.

## pdf-017-q3

Question: לפי עמוד PDF 4, מה קורה כשאף אחד לא שם לב שרמז אינו חוקי, ומהו העונש אם המפעיל נותן רמז שאינו חוקי והדבר מזוהה?

Answerable: Yes

Required answer facts:

- אם אף אחד לא שם לב שהרמז אינו חוקי, הוא נחשב חוקי.
- אם המפעיל נותן רמז שאינו חוקי, התור עובר לצוות השני.
- המפעיל של הצוות השני רשאי לכסות אחד מקלפי צוותו בסמן מרגל בצבע שלו לפני מתן הרמז הבא.

Evidence (page numbers are PDF viewer numbers):

- Page 4: עונש על רמז בלתי חוקי: אם המפעיל נותן רמז שאינו חוקי, התור עובר לצוות השני. בנוסף המפעיל של הצוות השני רשאי לכסות אחד מהקלפים של הצוות שלו בסמן מרגל בצבע שלו לפני שהוא נותן את הרמז הבא. אם אף אחד לא שם לב שהרמז אינו חוקי, הוא נחשב חוקי.

Changes / review notes:

- Converted the mixed question into an answerable rule comparison. No unsupported numeric penalty is required.

Human verifier: pending. Verification date: pending.

