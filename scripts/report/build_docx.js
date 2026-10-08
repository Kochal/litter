// Builds outputs/report/fly_tipping_story.docx from docs/story.md and the chart images in outputs/report
// (captured from the story page) plus outputs/fig_drive_time_map.png.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, Footer, PageNumber, BorderStyle, LineRuleType,
} = require("docx");

const REPO = path.resolve(__dirname, "../..");
const REP = path.join(REPO, "outputs/report");
// Usage: python scripts/report/story_md_to_blocks.py docs/story.md /tmp/blocks.json && node scripts/report/build_docx.js /tmp/blocks.json
const blocks = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const FONT = "Arial", ACCENT = "1D5B4C", INK2 = "52514E";
const CONTENT_DXA = 11906 - 2 * 1300;

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
const runsOf = (rs, base = {}) => rs.map(r => new TextRun({
  text: r.t, bold: r.b || base.bold, italics: r.i, font: r.code ? "Consolas" : FONT, size: base.size,
}));

const FIGS = {
  trend: { file: "fig_trend.png", width: 620, cap: "Figure 1. Recorded fly-tipping per person by size of load, England (2012/13 = 100). Lines by size of load are for the 223 councils whose numbers changed only gradually; the dashed line is all 296 councils. The dotted line marks 2019/20, when Defra asked councils to also count incidents their own crews find. Data: workbook sheet 1 Trend." },
  map: { file: "../fig_drive_time_map.png", width: 620, cap: "Figure 2. Change in drive time to the nearest recycling centre, 2012 to 2024, for 35,664 neighbourhoods; 973 are at least 3 minutes further away. Crosses mark the 83 verified closures. Wales is shown with its current centres only. Data: drive_time_change_lsoa.parquet and recycling_centres.parquet." },
  access: { file: "fig_access.png", width: 620, cap: "Figure 3. Every test of access to recycling centres: change in fly-tipping per resident, with its likely range (95% confidence interval). The number of observations is under each test. Data: workbook sheet 2 Access tests." },
  drivers: { file: "fig_drivers.png", width: 620, cap: "Figure 4. Change in fly-tipping per 10 percentage points more households renting privately (blue) or without a car or van (orange), by kind of fly-tipping. Comparing councils with similar deprivation, density and access: 950 council-years from 317 councils, 2022/23 to 2024/25. Faded values: the likely range includes no change. Data: workbook sheet 3 Renting and no car." },
  land: { file: "fig_land.png", width: 380, cap: "Figure 5. Type of land where fly-tipping was recorded, official council counts, England and Wales, 2022/23 to 2024/25 (3,624,424 incidents). Street-type land in green. Data: workbook sheet 4a Type of land." },
  setting: { file: "fig_setting.png", width: 380, cap: "Figure 6. FixMyStreet reports whose text says where the waste was (308,043 reports): a doorstep, pavement or street, or an out-of-the-way place such as a layby, field or verge. Data: workbook sheet 4b Street or out of way." },
  pred: { file: "fig_pred.png", width: 430, cap: "Figure 7. Change in recorded fly-tipping per person in England between 2012/13 to 2014/15 and 2022/23 to 2024/25 (296 councils), against the change predicted from the Census shifts in renting and car ownership. Data: workbook sheet 5a Predicted vs actual." },
  minis: { file: "fig_minis.png", width: 620, cap: "Figure 8. Other things that changed over the same years, England, 296 councils: residents moving into or out of their council area, street-cleaning spending per person (from 2017/18), prosecutions and fixed penalty notices per 1,000 incidents. Data: workbook sheet 5c Other factors by year." },
  within: { file: "fig_within.png", width: 620, cap: "Figure 9. Each council compared with itself over time: change in fly-tipping when its moving rate rises by 5 in every 100 residents, or its street-cleaning spending per person is halved, after allowing for changes common to all councils each year. Councils with no sudden jump in recording; the number of councils and council-years is under each row. Data: workbook sheet 5d Same council over time." },
};
function figure(key) {
  const f = FIGS[key], file = path.join(REP, f.file), s = pngSize(file);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80, line: 240, lineRule: LineRuleType.AUTO }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
        transformation: { width: f.width, height: Math.round(f.width * s.h / s.w) },
        altText: { title: f.cap.split(".")[0], description: f.cap, name: key } })] }),
    new Paragraph({ style: "Caption", children: [new TextRun({ text: f.cap.split(". ")[0] + ". ", bold: true }),
      new TextRun(f.cap.slice(f.cap.indexOf(". ") + 2))] }),
  ];
}

function table(rows) {
  const n = rows[0].length;
  const len = rows[0].map((_, j) => Math.max(...rows.map(r => r[j].map(x => x.t).join("").length)));
  const weights = len.map(l => Math.min(Math.max(l, 13), 60));
  const tot = weights.reduce((a, b) => a + b, 0);
  const widths = weights.map(w => Math.floor(w / tot * CONTENT_DXA));
  widths[n - 1] += CONTENT_DXA - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "C9CFCB" };
  return new Table({
    width: { size: CONTENT_DXA, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true,
      children: r.map((c, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA },
        borders: { top: border, bottom: border, left: border, right: border },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        shading: i === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: "E2EEE9" } : undefined,
        children: [new Paragraph({ spacing: { after: 0 }, children: runsOf(c, { bold: i === 0, size: 18 }) })],
      })) })),
  });
}

// Figure placement: after a block index, or replacing it
const AFTER = { 6: ["trend"], 10: ["map"], 23: ["land", "setting"], 31: ["minis"], 32: ["within"] };
const REPLACE = { 12: ["access"], 17: ["drivers"], 18: [], 30: ["pred"] };

const body = [];
body.push(new Paragraph({ style: "Title", children: [new TextRun("What drives fly-tipping in England and Wales")] }));
body.push(new Paragraph({ style: "Subtitle", children: [new TextRun("Findings from official council counts, FixMyStreet reports and councils' own incident records, 2012/13 to 2024/25")] }));
body.push(new Paragraph({ style: "Meta", children: [new TextRun("October 2026. Data behind every chart: fly_tipping_story_data.xlsx. Code and full results: github.com/kochal/litter.")] }));
body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("In brief")] }));
const brief = [
  "Recorded fly-tipping per person in England rose 62% between 2012/13 and 2024/25. In the 223 councils with no sudden change in how they record, it rose 43%, and the bigger the load, the faster it grew: lorry-sized dumps rose 149%.",
  "Closing recycling centres did not measurably raise fly-tipping. Nine different tests found no clear effect, although a small effect where a closure adds 3 minutes or more to the drive cannot be ruled out.",
  "Who lives nearby matters more. Areas with more private renting have more dumped household waste such as black bags and bulky items; areas with more households without a car have more builders' waste and lorry-sized dumps.",
  "Most fly-tipping is at the kerb: 83% of recorded incidents are on highways, footpaths, council land and back alleys, and 0.3% on farmland.",
  "Changes in renting and car ownership do not explain why fly-tipping rose. More people moving home explains roughly a quarter to a third of the rise; most of it points to causes that changed for the whole country at once.",
];
brief.forEach(t => body.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun(t)] })));
body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Contents")] }));
blocks.filter(b => b.type === "h" && b.level === 2).forEach(b => body.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun(b.text)] })));

blocks.forEach((b, k) => {
  if (k === 0 || k === 1) return;                       // title and repository note handled above
  if (k in REPLACE) { REPLACE[k].forEach(f => body.push(...figure(f))); return; }
  if (b.type === "h") {
    body.push(new Paragraph({ heading: b.level <= 2 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
      pageBreakBefore: b.level <= 2, children: [new TextRun(b.text)] }));
  } else if (b.type === "p") {
    body.push(new Paragraph({ children: runsOf(b.runs) }));
  } else if (b.type === "bullets" || b.type === "numbered") {
    const ref = b.type === "bullets" ? "bullets" : `num${k}`;
    b.items.forEach(it => body.push(new Paragraph({ numbering: { reference: ref, level: 0 }, children: runsOf(it) })));
  } else if (b.type === "table") {
    body.push(table(b.rows));
    body.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
  }
  (AFTER[k] || []).forEach(f => body.push(...figure(f)));
});
body.push(new Paragraph({ style: "Meta", spacing: { before: 400 }, children: [new TextRun("Contains Environment Agency information © Environment Agency and/or database right. Contains OS data © Crown copyright and database right. Contains public sector information licensed under the Open Government Licence v3.0 (Defra, Welsh Government, ONS, Natural Resources Wales, MHCLG). FixMyStreet reports from mySociety's public Open311 service. Only aggregate results are shown.")] }));

const numbered = blocks.map((b, k) => b.type === "numbered" ? {
  reference: `num${k}`, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] } : null).filter(Boolean);

const doc = new Document({
  creator: "kochal/litter", title: "What drives fly-tipping in England and Wales",
  description: "Findings on the trend, access to recycling centres, residents, where fly-tipping happens and why it has risen.",
  styles: {
    default: { document: { run: { font: FONT, size: 21, color: "1B1F1D" }, paragraph: { spacing: { after: 140, line: 288, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 44, bold: true, color: "0B0B0B" }, paragraph: { spacing: { after: 120 } } },
      { id: "Subtitle", name: "Subtitle", basedOn: "Normal", run: { font: FONT, size: 26, color: INK2 }, paragraph: { spacing: { after: 160 } } },
      { id: "Meta", name: "Meta", basedOn: "Normal", run: { font: FONT, size: 17, color: INK2 } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: ACCENT }, paragraph: { spacing: { before: 120, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: "0B0B0B" }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", run: { font: FONT, size: 17, color: INK2 }, paragraph: { spacing: { after: 240 } } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
    ...numbered,
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1300, right: 1300 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "What drives fly-tipping in England and Wales    ", size: 16, color: INK2 }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: INK2 })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(path.join(REP, "fly_tipping_story.docx"), buf); console.log("written", buf.length); });
