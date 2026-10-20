// The FlowForge API. Calls POST /flow with the choices from the form.
const API_URL = "https://6meaj75jv4.execute-api.us-east-1.amazonaws.com/flow";

const SCREENS = ["form", "preview", "guided", "done"];

let currentFlow = null;   // the flow the API last returned
let lastRequest = null;   // the choices that made it, so "Build a different one" can reuse them

// Guided mode state
let steps = [];
let stepIndex = 0;
let endTime = 0;          // when the current step ends (a clock time, so the timer cannot drift)
let remainingMs = 0;
let paused = false;
let ticker = null;
let wakeLock = null;
let audioContext = null;


// ---------- Small helpers ----------

function $(id) {
  return document.getElementById(id);
}

function showScreen(name) {
  for (const screen of SCREENS) {
    $("screen-" + screen).hidden = screen !== name;
  }
  window.scrollTo(0, 0);
}

function showError(id, message) {
  $(id).textContent = message;
  $(id).hidden = message === "";
}

function formatTime(totalSeconds) {
  const whole = Math.max(0, Math.ceil(totalSeconds));
  const minutes = Math.floor(whole / 60);
  const seconds = whole % 60;
  return minutes + ":" + String(seconds).padStart(2, "0");
}

// A pose done on each side becomes two steps, so the timer can tell you when to switch
function buildSteps(poses) {
  const result = [];
  for (const pose of poses) {
    if (pose.side_mode === "per_side") {
      const half = pose.flow_seconds / 2;
      result.push({ name: pose.name, label: "Right side", seconds: half });
      result.push({ name: pose.name, label: "Left side", seconds: half });
    } else {
      result.push({ name: pose.name, label: "", seconds: pose.flow_seconds });
    }
  }
  return result;
}


// ---------- Talking to the API ----------

async function requestFlow(choices) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(choices),
  });

  let data = {};
  try {
    data = await response.json();
  } catch (error) {
    data = {};
  }

  if (response.status === 429) {
    throw new Error("Lots of people are building flows right now. Wait a moment and try again.");
  }
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}


// ---------- Screen 1: the form ----------

function readChoices() {
  const checked = document.querySelectorAll("#areas input[name=area]:checked");
  const areas = Array.from(checked).map((input) => input.value);
  const difficulty = document.querySelector("input[name=difficulty]:checked").value;
  const minutes = Number($("minutes").value);

  // "Full body" replaces any individual areas
  if (areas.includes("full body")) {
    return { body_areas: ["full body"], difficulty: difficulty, minutes: minutes };
  }
  return { body_areas: areas, difficulty: difficulty, minutes: minutes };
}

// Picking "Full body" clears the other areas, and picking any other area clears "Full body"
function keepAreasConsistent(event) {
  const changed = event.target;
  if (changed.name !== "area" || !changed.checked) {
    return;
  }
  const all = document.querySelectorAll("#areas input[name=area]");
  for (const input of all) {
    if (changed.value === "full body" && input !== changed) {
      input.checked = false;
    }
    if (changed.value !== "full body" && input.value === "full body") {
      input.checked = false;
    }
  }
}

async function buildFlow(choices, errorId, buttonId) {
  const button = $(buttonId);
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Building...";
  showError(errorId, "");

  try {
    currentFlow = await requestFlow(choices);
    lastRequest = choices;
    renderPreview();
    showScreen("preview");
  } catch (error) {
    showError(errorId, error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function onSubmit(event) {
  event.preventDefault();
  const choices = readChoices();
  if (choices.body_areas.length === 0) {
    showError("form-error", "Pick at least one area to focus on.");
    return;
  }
  buildFlow(choices, "form-error", "build-button");
}


// ---------- Screen 2: the preview ----------

function renderPreview() {
  const list = $("pose-list");
  list.replaceChildren();

  for (const pose of currentFlow.poses) {
    const item = document.createElement("li");

    // textContent (not innerHTML) so text from the API can never be run as code
    const name = document.createElement("span");
    name.textContent = pose.name;

    const time = document.createElement("span");
    time.className = "time";
    time.textContent = formatTime(pose.flow_seconds) + (pose.side_mode === "per_side" ? " (both sides)" : "");

    item.append(name, time);
    list.append(item);
  }

  $("preview-summary").textContent =
    currentFlow.poses.length + " poses, " + formatTime(currentFlow.total_seconds) + " total";
}


// ---------- Screen 3: guided mode ----------

function primeAudio() {
  // Browsers only allow sound after a tap, so this runs when you press Start
  try {
    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
    audioContext.resume();
  } catch (error) {
    audioContext = null;
  }
}

function beep() {
  if (!audioContext) {
    return;
  }
  try {
    const oscillator = audioContext.createOscillator();
    const volume = audioContext.createGain();
    oscillator.frequency.value = 660;
    volume.gain.value = 0.08;
    oscillator.connect(volume);
    volume.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.25);
  } catch (error) {
    // Sound is a nice extra, so a failure is ignored
  }
}

async function keepScreenAwake() {
  try {
    if ("wakeLock" in navigator) {
      wakeLock = await navigator.wakeLock.request("screen");
    }
  } catch (error) {
    wakeLock = null;
  }
}

function releaseScreen() {
  if (wakeLock) {
    wakeLock.release().catch(() => {});
    wakeLock = null;
  }
}

function startGuided() {
  steps = buildSteps(currentFlow.poses);
  stepIndex = 0;
  primeAudio();
  keepScreenAwake();
  showScreen("guided");
  beginStep();
}

function beginStep() {
  const step = steps[stepIndex];
  $("step-count").textContent = "Step " + (stepIndex + 1) + " of " + steps.length;
  $("step-name").textContent = step.name;
  $("step-label").textContent = step.label;

  remainingMs = step.seconds * 1000;
  endTime = Date.now() + remainingMs;
  paused = false;
  $("pause-button").textContent = "Pause";

  clearInterval(ticker);
  ticker = setInterval(tick, 200);
  tick();
}

function tick() {
  if (paused) {
    return;
  }
  const step = steps[stepIndex];
  remainingMs = endTime - Date.now();
  $("timer").textContent = formatTime(remainingMs / 1000);

  const done = 1 - remainingMs / (step.seconds * 1000);
  $("bar-fill").style.width = Math.min(100, Math.max(0, done * 100)) + "%";

  if (remainingMs <= 0) {
    nextStep();
  }
}

function nextStep() {
  if (stepIndex >= steps.length - 1) {
    finishGuided();
    return;
  }
  stepIndex++;
  beep();
  beginStep();
}

function previousStep() {
  if (stepIndex > 0) {
    stepIndex--;
  }
  beginStep();
}

function togglePause() {
  if (paused) {
    endTime = Date.now() + remainingMs;
    paused = false;
    $("pause-button").textContent = "Pause";
  } else {
    remainingMs = endTime - Date.now();
    paused = true;
    $("pause-button").textContent = "Resume";
  }
}

function finishGuided() {
  clearInterval(ticker);
  releaseScreen();
  beep();
  showScreen("done");
}

function endEarly() {
  clearInterval(ticker);
  releaseScreen();
  showScreen("preview");
}


// ---------- Wire up the buttons ----------

$("flow-form").addEventListener("submit", onSubmit);
$("areas").addEventListener("change", keepAreasConsistent);
$("start-button").addEventListener("click", startGuided);
$("regenerate-button").addEventListener("click", () => buildFlow(lastRequest, "preview-error", "regenerate-button"));
$("change-button").addEventListener("click", () => showScreen("form"));
$("prev-button").addEventListener("click", previousStep);
$("pause-button").addEventListener("click", togglePause);
$("next-button").addEventListener("click", nextStep);
$("quit-button").addEventListener("click", endEarly);
$("again-button").addEventListener("click", () => showScreen("form"));