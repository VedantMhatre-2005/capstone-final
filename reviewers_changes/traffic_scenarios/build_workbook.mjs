import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(here, '../yash_traffic_evaluation');
const data = JSON.parse(await fs.readFile(path.join(out, 'workbook_data.json'), 'utf8'));
const wb = Workbook.create();
const overview = wb.worksheets.add('Summary');
const scenarios = wb.worksheets.add('Scenarios');
const trials = wb.worksheets.add('Trials');
const head = '#243B53';
const body = '#172B4D';
const total = data.summaries.length;
const end = total + 1;

function col(index) {
  let result = '';
  for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) {
    result = String.fromCharCode(65 + (n - 1) % 26) + result;
  }
  return result;
}

function styleTable(sheet, columns, rows, widths, name) {
  const last = col(columns - 1);
  sheet.showGridLines = false;
  sheet.getRange(`A1:${last}${rows}`).format.font = {name: 'Arial', size: 10, color: body};
  sheet.getRange(`A1:${last}${rows}`).format.rowHeight = 18;
  sheet.getRange(`A1:${last}${rows}`).format.verticalAlignment = 'center';
  sheet.getRange(`A1:${last}1`).format = {
    fill: head, font: {name: 'Arial', size: 10, bold: true, color: '#FFFFFF'},
    wrapText: true, rowHeight: 42, horizontalAlignment: 'center', verticalAlignment: 'center',
  };
  widths.forEach((width, i) => { sheet.getRange(`${col(i)}1:${col(i)}${rows}`).format.columnWidth = width; });
  sheet.freezePanes.freezeRows(1);
  const table = sheet.tables.add(`A1:${last}${rows}`, true, name);
  table.style = 'TableStyleLight1';
}

const headers = ['Suite', 'Nodes', 'Scenario ID', 'Traffic family', 'Level', 'Input status',
  'Qubits', 'Requested packets', 'Budget omitted', 'Initial peak (%)', 'QAOA mean peak (%)',
  'QAOA SD (pp)', 'BPSO mean peak (%)', 'BPSO SD (pp)', 'QAOA relief (%)', 'BPSO relief (%)',
  'QAOA relief (pp)', 'BPSO minus QAOA (pp)', 'QAOA outcome', 'BPSO outcome', 'Mean comparison',
  'Exact-J peak (%)', 'Minimum peak (%)', 'QAOA mean J gap', 'Solver seeds'];
const scValues = data.summaries.map(r => [r.suite, r.n_nodes, r.scenario_id, r.family, r.level, r.status,
  r.n_qubits, r.requested_packets, r.budget_omitted_packets, r.initial_peak_pct, r.qaoa_peak_mean_pct,
  r.qaoa_peak_sd_pp, r.bpso_peak_mean_pct, r.bpso_peak_sd_pp, null, null, null, null, null, null, null,
  r.exact_j_peak_pct, r.exact_min_peak_pct, r.qaoa_mean_absolute_j_gap, r.n_solver_seeds]);
scenarios.getRange(`A1:Y${end}`).values = [headers, ...scValues];
for (let row = 2; row <= end; row++) {
  scenarios.getRange(`O${row}:U${row}`).formulas = [[
    `=IF(J${row}=0,"n.a.",100*(J${row}-K${row})/J${row})`,
    `=IF(J${row}=0,"n.a.",100*(J${row}-M${row})/J${row})`,
    `=J${row}-K${row}`, `=M${row}-K${row}`,
    `=IF(J${row}-K${row}>0.00000001,"improved",IF(K${row}-J${row}>0.00000001,"worsened","unchanged"))`,
    `=IF(J${row}-M${row}>0.00000001,"improved",IF(M${row}-J${row}>0.00000001,"worsened","unchanged"))`,
    `=IF(R${row}>0.00000001,"QAOA lower",IF(R${row}< -0.00000001,"BPSO lower","tie"))`,
  ]];
}
styleTable(scenarios, 25, end,
  [15,8,48,28,9,22,8,13,13,15,17,12,17,12,15,15,15,18,15,15,18,16,16,17,12], 'ScenarioMeasurements');
scenarios.getRange(`J2:R${end}`).setNumberFormat('0.00');
scenarios.getRange(`V2:W${end}`).setNumberFormat('0.00');
scenarios.getRange(`X2:X${end}`).setNumberFormat('0.000000');
scenarios.getRange(`Q2:Q${end}`).conditionalFormats.add('cellIs', {
  operator: 'lessThan', formula: 0, format: {fill: '#FCE4E4', font: {color: '#9B1C1C'}},
});

const rawHeaders = ['Scenario ID', 'Method', 'Solver seed', 'Status', 'Qubits',
  'Initial peak (%)', 'Final peak (%)', 'Relative relief (%)', 'Relief (pp)', 'QUBO cost',
  'Minimum J', 'Absolute J gap', 'Solver wrapper (ms)', 'Backend', 'Bitstring'];
const rawValues = data.raw.map(r => [r.scenario_id, r.method, r.solver_seed, r.status, r.n_qubits,
  r.initial_peak_pct, r.final_peak_pct, null, null, r.qubo_cost ?? null, r.exact_min_qubo_cost,
  r.qubo_gap_absolute ?? null, r.solve_ms ?? null, r.backend,
  r.bitstring ? r.bitstring.join('') : null]);
const rawEnd = rawValues.length+1;
trials.getRange(`A1:O${rawEnd}`).values = [rawHeaders, ...rawValues];
trials.getRange('H2:I2').formulas = [['=IF(F2=0,"n.a.",100*(F2-G2)/F2)', '=F2-G2']];
trials.getRange(`H2:I${rawEnd}`).fillDown();
styleTable(trials, 15, rawEnd, [48,15,12,22,8,16,16,17,14,17,17,17,21,55,16], 'SolverTrials');
trials.getRange(`F2:I${rawEnd}`).setNumberFormat('0.00');
trials.getRange(`J2:L${rawEnd}`).setNumberFormat('0.000000');
trials.getRange(`M2:M${rawEnd}`).setNumberFormat('0.00');
trials.getRange(`O2:O${rawEnd}`).setNumberFormat('@');

overview.showGridLines = false;
overview.tabColor = head;
overview.getRange('A1:N27').format.font = {name: 'Arial', size: 10, color: body};
overview.getRange('A1:N27').format.rowHeight = 21;
overview.getRange('A2').values = [['Traffic scenario evaluation']];
overview.getRange('A2').format.font = {name: 'Arial', size: 15, bold: true, color: body};
overview.getRange('A3:N3').format.borders = {bottom: {style: 'thin', color: '#9CAAB5'}};
overview.getRange('A4').values = [['119 synthetic traffic cases; five solver seeds per case; Qiskit statevector simulation.']];
overview.getRange('A4').format.font = {name:'Arial',size:10,italic:true,color:'#526579'};
overview.getRange('A6:N6').values = [[
  'Suite','Nodes','Cases','Q improved','Q unchanged','Q worsened','Q median relief (%)',
  'B improved','B unchanged','B worsened','B median relief (%)','Q lower','Ties','B lower']];
overview.getRange('A6:N6').format = {fill: head, font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},
  wrapText:true,rowHeight:36,horizontalAlignment:'center',verticalAlignment:'center'};
const groups = data.topology.filter(r => r.method === 'QAOA');
groups.forEach((r, index) => {
  const row = index+7;
  const b = data.topology.find(x => x.suite === r.suite && x.n_nodes === r.n_nodes && x.method === 'BPSO');
  overview.getRange(`A${row}:N${row}`).values = [[r.suite, r.n_nodes, null,null,null,null,
    r.median_reduction_relative_pct,null,null,null,b.median_reduction_relative_pct,null,null,null]];
  const criteria = `Scenarios!$A$2:$A$${end},A${row},Scenarios!$B$2:$B$${end},B${row}`;
  overview.getRange(`C${row}:F${row}`).formulas = [[`=COUNTIFS(${criteria})`,
    `=COUNTIFS(${criteria},Scenarios!$S$2:$S$${end},"improved")`,
    `=COUNTIFS(${criteria},Scenarios!$S$2:$S$${end},"unchanged")`,
    `=COUNTIFS(${criteria},Scenarios!$S$2:$S$${end},"worsened")`]];
  overview.getRange(`H${row}:J${row}`).formulas = [[
    `=COUNTIFS(${criteria},Scenarios!$T$2:$T$${end},"improved")`,
    `=COUNTIFS(${criteria},Scenarios!$T$2:$T$${end},"unchanged")`,
    `=COUNTIFS(${criteria},Scenarios!$T$2:$T$${end},"worsened")`]];
  overview.getRange(`L${row}:N${row}`).formulas = [[
    `=COUNTIFS(${criteria},Scenarios!$U$2:$U$${end},"QAOA lower")`,
    `=COUNTIFS(${criteria},Scenarios!$U$2:$U$${end},"tie")`,
    `=COUNTIFS(${criteria},Scenarios!$U$2:$U$${end},"BPSO lower")`]];
});
overview.getRange('A15').values = [['Total cases']];
overview.getRange('C15').formulas = [[`=SUM(C7:C${6+groups.length})`]];
overview.getRange('A15:N15').format.borders = {top:{style:'thin',color:'#9CAAB5'}};
overview.getRange('A15:C15').format.font = {name:'Arial',size:10,bold:true};
overview.getRange('G7:G13').setNumberFormat('0.00');
overview.getRange('K7:K13').setNumberFormat('0.00');
const notes = [
  'Q = QAOA; B = BPSO. Counts compare five-seed mean peaks on fixed traffic inputs.',
  'Negative relief means deterioration. Congestion trigger: load/capacity > 60%.',
  'Median relief values are saved analysis outputs. Formula columns recalculate relief and outcome counts.',
  'This measurement snapshot does not rerun solvers when edited; no statistical-equivalence claim is made.',
  '23 no-action cases bypass the solver. Each allocated packet must choose one of two detours.',
  'Methods, scenario definitions and limitations: REPORT.md. Full inputs and seeds: results/scenario_manifest.json.',
  `Source: ${data.source}`,
];
notes.forEach((note,i)=>{overview.getRange(`A${18+i}`).values=[[note]];});
overview.getRange('A18:A24').format.font={name:'Arial',size:10,color:'#526579'};
[18,8,10,12,12,12,18,12,12,12,18,10,10,10].forEach((w,i)=>{
  overview.getRange(`${col(i)}1:${col(i)}27`).format.columnWidth=w;
});
wb.recalculate();
if (overview.getRange('C15').values[0][0] !== 119) throw new Error('Scenario total does not reconcile');
const savedPeak = scenarios.getRange('K2').values[0][0];
const beforeWorst = overview.getRange('F7').values[0][0];
scenarios.getRange('K2').values = [[scenarios.getRange('J2').values[0][0] + 1]];
wb.recalculate();
if (overview.getRange('F7').values[0][0] !== beforeWorst + 1 ||
    overview.getRange('N7').values[0][0] !== 1) {
  throw new Error('Input-change check did not update scenario relief and summary counts');
}
scenarios.getRange('K2').values = [[savedPeak]];
wb.recalculate();
if (overview.getRange('F7').values[0][0] !== beforeWorst ||
    overview.getRange('N7').values[0][0] !== 0) throw new Error('Input restoration failed');
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',
  options:{useRegex:true,maxResults:20},summary:'final formula error scan'});
await fs.writeFile(path.join(out,'results/workbook_formula_scan.json'),JSON.stringify({
  inspection: errors.ndjson, totalCases:119, formulaRefreshVerified:true, originalInputsRestored:true,
},null,2));
console.log('FORMULA_SCAN', errors.ndjson);
console.log('SUMMARY', (await wb.inspect({kind:'table',range:'Summary!A6:N15',include:'values,formulas',
  tableMaxRows:10,tableMaxCols:14,maxChars:6500})).ndjson);
await fs.mkdir(path.join(out,'previews'),{recursive:true});
for(const [sheetName,range] of [['Summary','A1:N25'],['Scenarios','A1:K10'],['Trials','A1:I10']]){
  const preview=await wb.render({sheetName,range,scale:1.3,format:'png'});
  await fs.writeFile(path.join(out,'previews',`${sheetName.toLowerCase()}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save(path.join(out,'traffic_scenario_results.xlsx'));
console.log('Saved traffic_scenario_results.xlsx');
