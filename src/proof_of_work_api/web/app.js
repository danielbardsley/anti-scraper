const clientIdInput = document.getElementById("client-id");
const countInput = document.getElementById("count");
const fetchButton = document.getElementById("fetch-button");
const statusNode = document.getElementById("status");
const tierNode = document.getElementById("tier");
const stagesNode = document.getElementById("stages");
const solveTimeNode = document.getElementById("solve-time");
const requestCountNode = document.getElementById("request-count");
const responseOutputNode = document.getElementById("response-output");
const challengeOutputNode = document.getElementById("challenge-output");

const storageKey = "proof-of-work-demo-client-id";
const sha256Constants = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
];
let requestCounter = 0;

initializeUi().catch((error) => updateStatus(`Failed to initialize UI: ${error.message}`, true));
fetchButton.addEventListener("click", () => runRequest().catch((error) => handleFailure(error)));

async function initializeUi() {
  const config = await fetchJson("/v1/config");
  countInput.min = String(config.minCount);
  countInput.max = String(config.maxCount);
  countInput.value = String(config.defaultCount);
  requestCountNode.textContent = String(requestCounter);

  const existingClientId = window.localStorage.getItem(storageKey);
  const clientId = existingClientId || createClientId();
  window.localStorage.setItem(storageKey, clientId);
  clientIdInput.value = clientId;

  if (!canUseSubtleCrypto()) {
    updateStatus("Using JavaScript SHA-256 fallback because Web Crypto is unavailable on this HTTP origin.");
  }
}

async function runRequest() {
  fetchButton.disabled = true;
  updateStatus("Requesting challenge...");
  responseOutputNode.textContent = "No response yet.";

  const count = Number.parseInt(countInput.value, 10);
  const clientId = clientIdInput.value.trim();
  if (!clientId) {
    throw new Error("Client ID is required.");
  }

  const challenge = await fetchJson("/v1/pow/challenges", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ clientId, resource: "random-numbers", count })
  });

  challengeOutputNode.textContent = JSON.stringify(challenge, null, 2);
  tierNode.textContent = String(challenge.tier);
  stagesNode.textContent = String(challenge.algorithm.stages.length);

  updateStatus(`Solving tier ${challenge.tier} challenge with ${challenge.algorithm.stages.length} stage(s)...`);
  const solveStarted = performance.now();
  const proof = await solveChallenge(challenge);
  const solveDurationMs = performance.now() - solveStarted;
  solveTimeNode.textContent = `${solveDurationMs.toFixed(0)} ms`;

  updateStatus("Submitting proof and requesting random numbers...");
  const response = await fetchJson("/v1/random-numbers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clientId,
      count,
      challengeId: challenge.challengeId,
      proof: {
        nonces: proof.nonces,
        solverStartedAt: new Date(proof.startedAt).toISOString(),
        solverFinishedAt: new Date(proof.finishedAt).toISOString()
      }
    })
  });

  requestCounter += 1;
  requestCountNode.textContent = String(requestCounter);
  responseOutputNode.textContent = JSON.stringify(response, null, 2);
  updateStatus(`Success. Received ${response.numbers.length} random numbers.`);
  fetchButton.disabled = false;
}

async function solveChallenge(challenge) {
  const startedAt = Date.now();
  const nonces = [];
  let previousValue = challenge.seed;

  for (const stage of challenge.algorithm.stages) {
    const nonce = await solveStage(previousValue, stage.index, stage.targetBits);
    nonces.push(String(nonce));
    previousValue = await sha256Hex(`${previousValue}:${stage.index}:${nonce}`);
  }

  return {
    nonces,
    startedAt,
    finishedAt: Date.now()
  };
}

async function solveStage(previousValue, stageIndex, targetBits) {
  let nonce = 0;
  while (true) {
    const digestHex = await sha256Hex(`${previousValue}:${stageIndex}:${nonce}`);
    if (leadingZeroBitsFromHex(digestHex) >= targetBits) {
      return nonce;
    }
    nonce += 1;
    if (nonce % 500 === 0) {
      updateStatus(`Stage ${stageIndex + 1}: tested ${nonce.toLocaleString()} nonces...`);
      await yieldToUi();
    }
  }
}

async function sha256Hex(text) {
  if (canUseSubtleCrypto()) {
    const bytes = new TextEncoder().encode(text);
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
  }
  return sha256HexFallback(text);
}

function canUseSubtleCrypto() {
  return Boolean(window.crypto && window.crypto.subtle && typeof window.crypto.subtle.digest === "function");
}

function createClientId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `browser-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function leadingZeroBitsFromHex(hexValue) {
  let total = 0;
  for (let index = 0; index < hexValue.length; index += 2) {
    const value = Number.parseInt(hexValue.slice(index, index + 2), 16);
    if (value === 0) {
      total += 8;
      continue;
    }
    return total + (8 - value.toString(2).length);
  }
  return total;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body?.error?.message || `Request failed with status ${response.status}.`;
    throw new Error(message);
  }
  return body;
}

function updateStatus(message, isError = false) {
  statusNode.textContent = message;
  statusNode.style.color = isError ? "#fca5a5" : "#e2e8f0";
}

async function handleFailure(error) {
  responseOutputNode.textContent = JSON.stringify({ error: error.message }, null, 2);
  updateStatus(error.message, true);
  fetchButton.disabled = false;
}

function yieldToUi() {
  return new Promise((resolve) => window.setTimeout(resolve, 0));
}

function sha256HexFallback(message) {
  const messageBytes = Array.from(new TextEncoder().encode(message));
  const bitLength = messageBytes.length * 8;
  messageBytes.push(0x80);

  while ((messageBytes.length % 64) !== 56) {
    messageBytes.push(0);
  }

  const highBits = Math.floor(bitLength / 0x100000000);
  const lowBits = bitLength >>> 0;
  messageBytes.push(
    (highBits >>> 24) & 0xff,
    (highBits >>> 16) & 0xff,
    (highBits >>> 8) & 0xff,
    highBits & 0xff,
    (lowBits >>> 24) & 0xff,
    (lowBits >>> 16) & 0xff,
    (lowBits >>> 8) & 0xff,
    lowBits & 0xff
  );

  let h0 = 0x6a09e667;
  let h1 = 0xbb67ae85;
  let h2 = 0x3c6ef372;
  let h3 = 0xa54ff53a;
  let h4 = 0x510e527f;
  let h5 = 0x9b05688c;
  let h6 = 0x1f83d9ab;
  let h7 = 0x5be0cd19;

  const messageSchedule = new Array(64).fill(0);

  for (let offset = 0; offset < messageBytes.length; offset += 64) {
    for (let index = 0; index < 16; index += 1) {
      const base = offset + (index * 4);
      messageSchedule[index] = (
        (messageBytes[base] << 24) |
        (messageBytes[base + 1] << 16) |
        (messageBytes[base + 2] << 8) |
        messageBytes[base + 3]
      ) >>> 0;
    }

    for (let index = 16; index < 64; index += 1) {
      const sigma0 = rightRotate(messageSchedule[index - 15], 7)
        ^ rightRotate(messageSchedule[index - 15], 18)
        ^ (messageSchedule[index - 15] >>> 3);
      const sigma1 = rightRotate(messageSchedule[index - 2], 17)
        ^ rightRotate(messageSchedule[index - 2], 19)
        ^ (messageSchedule[index - 2] >>> 10);
      messageSchedule[index] = sum32(
        messageSchedule[index - 16],
        sigma0,
        messageSchedule[index - 7],
        sigma1
      );
    }

    let a = h0;
    let b = h1;
    let c = h2;
    let d = h3;
    let e = h4;
    let f = h5;
    let g = h6;
    let h = h7;

    for (let index = 0; index < 64; index += 1) {
      const sigma1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temp1 = sum32(h, sigma1, choice, sha256Constants[index], messageSchedule[index]);
      const sigma0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = sum32(sigma0, majority);

      h = g;
      g = f;
      f = e;
      e = sum32(d, temp1);
      d = c;
      c = b;
      b = a;
      a = sum32(temp1, temp2);
    }

    h0 = sum32(h0, a);
    h1 = sum32(h1, b);
    h2 = sum32(h2, c);
    h3 = sum32(h3, d);
    h4 = sum32(h4, e);
    h5 = sum32(h5, f);
    h6 = sum32(h6, g);
    h7 = sum32(h7, h);
  }

  return [h0, h1, h2, h3, h4, h5, h6, h7].map(toHex32).join("");
}

function rightRotate(value, amount) {
  return (value >>> amount) | (value << (32 - amount));
}

function sum32(...values) {
  let result = 0;
  for (const value of values) {
    result = (result + value) >>> 0;
  }
  return result;
}

function toHex32(value) {
  return (value >>> 0).toString(16).padStart(8, "0");
}
