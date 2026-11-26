"use strict";

const pool = JSON.parse(document.querySelector("#review-pool").textContent);
const status = document.querySelector("#review-status");
const reviewer = document.querySelector("#reviewer");
const cards = [...document.querySelectorAll("[data-judgment]")].map((field) => ({
  caseIndex: Number(field.dataset.case),
  judgmentIndex: Number(field.dataset.judgment),
  grade: field.querySelector("[data-grade]"),
  basis: field.querySelector("[data-basis]"),
}));

function assessment(card, dataset) {
  return dataset.cases[card.caseIndex].judgments[card.judgmentIndex];
}

function poolIdentity(dataset) {
  return JSON.stringify(dataset.cases.map((entry) => [
    entry.id, entry.query, entry.ipc ?? null,
    entry.judgments.map((row) => [row.stage, row.number, row.content_scope, row.document_sha256, row.parser_version]),
  ]));
}

function exportReview(complete) {
  const output = structuredClone(pool);
  output.reviewer = reviewer.value.trim();
  let completed = 0;
  for (const card of cards) {
    const row = assessment(card, output);
    row.grade = card.grade.value === "" ? null : Number(card.grade.value);
    row.basis = card.basis.value.trim();
    if (row.grade !== null && row.basis) completed += 1;
  }
  if (complete && (!output.reviewer || completed !== cards.length)) {
    status.textContent = `已完成 ${completed} / ${cards.length}。請填寫複核者與每份文件的分數、判定依據。`;
    return;
  }
  output.label_status = complete ? "human_reviewed" : "pending_human_review";
  const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2) + "\n"], {type: "application/json"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = complete ? "patentscope-review.json" : "patentscope-review-draft.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status.textContent = `已準備下載。完成 ${completed} / ${cards.length}。`;
}

document.querySelector("#save-draft").addEventListener("click", () => exportReview(false));
document.querySelector("#finish-review").addEventListener("click", () => exportReview(true));
document.querySelector("#review-import").addEventListener("change", async (event) => {
  const input = event.currentTarget;
  const file = input.files[0];
  if (!file) return;
  try {
    const draft = JSON.parse(await file.text());
    if (poolIdentity(draft) !== poolIdentity(pool) || typeof draft.reviewer !== "string") throw new Error();
    const rows = cards.map((card) => assessment(card, draft));
    if (rows.some((row) => ![null, 0, 1, 2].includes(row.grade) || typeof row.basis !== "string")) throw new Error();
    reviewer.value = draft.reviewer;
    cards.forEach((card, index) => {
      card.grade.value = rows[index].grade === null ? "" : String(rows[index].grade);
      card.basis.value = rows[index].basis;
    });
    status.textContent = "已載入同一候選池的複核檔。";
  } catch {
    status.textContent = "無法載入。請選擇同一候選池匯出的複核檔。";
  } finally {
    input.value = "";
  }
});
