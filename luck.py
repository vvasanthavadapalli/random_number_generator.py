from flask import Flask, render_template_string, request, jsonify
import random

app = Flask(__name__)

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lucky Number Lab</title>
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    min-height: 100vh;
    font-family: Arial, sans-serif;
    color: #fff;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #1c1045, #271354, #1b1046, #39206e);
    background-size: 300% 300%;
    animation: backgroundFlow 8s ease infinite;
}

body.spinning {
    animation: backgroundBlink 0.7s steps(2, end) infinite;
}

@keyframes backgroundFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes backgroundBlink {
    0% { background: #1b1046; }
    50% { background: #34206d; }
    100% { background: #24104d; }
}

.container {
    width: 100%;
    max-width: 720px;
    padding: 28px 18px;
}

h1 {
    margin: 12px 0 20px;
    font-size: clamp(34px, 6vw, 44px);
    letter-spacing: 1px;
}

.subtitle {
    margin-bottom: 24px;
    color: #d9ccef;
    font-size: 18px;
}

.stage {
    height: 310px;
    display: flex;
    align-items: center;
    justify-content: center;
    perspective: 1000px;
    position: relative;
}

.shadow {
    position: absolute;
    width: 190px;
    height: 28px;
    bottom: 28px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.55);
    filter: blur(12px);
    transform: rotate(28deg);
}

.dice {
    width: 120px;
    height: 120px;
    position: relative;
    transform-style: preserve-3d;
    transform: rotateX(-22deg) rotateY(-28deg);
    z-index: 2;
}

.face {
    position: absolute;
    width: 120px;
    height: 120px;
    border: 2px solid #e5e1f2;
    border-radius: 9px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    place-items: center;
    padding: 18px;
    backface-visibility: hidden;
    box-shadow: inset 0 0 9px rgba(80, 55, 140, 0.12);
}

.front  { transform: translateZ(60px); background: #ffffff; }
.back   { transform: rotateY(180deg) translateZ(60px); background: #e8e4f8; }
.right  { transform: rotateY(90deg) translateZ(60px); background: #c9bde9; }
.left   { transform: rotateY(-90deg) translateZ(60px); background: #f6f4ff; }
.top    { transform: rotateX(90deg) translateZ(60px); background: #ffffff; }
.bottom { transform: rotateX(-90deg) translateZ(60px); background: #b8a8df; }

.pip {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #38236e;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.22);
}

.controls {
    margin: 22px auto;
    display: flex;
    justify-content: center;
    align-items: end;
    flex-wrap: wrap;
    gap: 24px;
}

.field { text-align: center; }

label {
    display: block;
    margin-bottom: 8px;
    color: #e3d7f5;
    font-size: 18px;
}

input {
    width: 116px;
    padding: 7px 9px;
    border: 1px solid #b9a3e8;
    border-radius: 0;
    background: #fff;
    color: #171024;
    font-size: 20px;
    text-align: center;
}

button {
    padding: 17px 32px;
    border: none;
    border-radius: 0;
    background: #a78bfa;
    color: #24134b;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}

button:hover { background: #c4b5fd; }
button:disabled { opacity: 0.65; cursor: wait; }

.result-label {
    margin-top: 0;
    color: #fff;
    font-size: 34px;
    font-weight: bold;
    min-height: 42px;
}

#status {
    min-height: 22px;
    margin-top: 12px;
    color: #e0d4f3;
    font-size: 14px;
}

.error { color: #ffb4c0 !important; }

@media (max-width: 420px) {
    .stage { height: 275px; }
    .result-label { font-size: 27px; }
    .controls { gap: 14px; }
}
</style>
</head>
<body>
<div class="container">
    <h1>LUCKY NUMBER LAB</h1>
    <p class="subtitle">Set your range and test your luck!</p>

    <div class="stage">
        <div class="shadow"></div>
        <div class="dice" id="dice">
            <div class="face front" data-value="1"></div>
            <div class="face back" data-value="6"></div>
            <div class="face right" data-value="3"></div>
            <div class="face left" data-value="4"></div>
            <div class="face top" data-value="2"></div>
            <div class="face bottom" data-value="5"></div>
        </div>
    </div>

    <div class="result-label">Your number: <span id="result">1</span></div>

    <div class="controls">
        <div class="field">
            <label for="minimum">Minimum</label>
            <input id="minimum" type="number" value="1" step="1">
        </div>
        <div class="field">
            <label for="maximum">Maximum</label>
            <input id="maximum" type="number" value="100" step="1">
        </div>
    </div>

    <button id="rollButton" onclick="rollDice()">🎲 &nbsp; ROLL THE DICE</button>
    <div id="status">Ready when you are!</div>
</div>

<script>
const dice = document.getElementById("dice");
const result = document.getElementById("result");
const button = document.getElementById("rollButton");
const statusText = document.getElementById("status");

let spinning = false;
let rotX = -22;
let rotY = -28;
let rotZ = 0;

const patterns = {
    1: [4],
    2: [0, 8],
    3: [0, 4, 8],
    4: [0, 2, 6, 8],
    5: [0, 2, 4, 6, 8],
    6: [0, 2, 3, 5, 6, 8]
};

document.querySelectorAll(".face").forEach(face => {
    const value = Number(face.dataset.value);
    for (let i = 0; i < 9; i++) {
        const pip = document.createElement("span");
        if (patterns[value].includes(i)) pip.className = "pip";
        face.appendChild(pip);
    }
});

function easeOutQuint(t) {
    return 1 - Math.pow(1 - t, 5);
}

async function rollDice() {
    if (spinning) return;

    const minText = document.getElementById("minimum").value.trim();
    const maxText = document.getElementById("maximum").value.trim();

    if (!minText || !maxText) {
        statusText.textContent = "Please enter both minimum and maximum values.";
        statusText.className = "error";
        return;
    }

    const low = Number(minText);
    const high = Number(maxText);

    if (!Number.isSafeInteger(low) || !Number.isSafeInteger(high)) {
        statusText.textContent = "Please enter valid whole numbers.";
        statusText.className = "error";
        return;
    }

    if (low > high) {
        statusText.textContent = "Minimum must be less than or equal to maximum.";
        statusText.className = "error";
        return;
    }

    spinning = true;
    button.disabled = true;
    statusText.className = "";
    statusText.textContent = "Spinning fast...";

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({minimum: low, maximum: high})
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not generate number.");

        document.body.classList.add("spinning");

        const startX = rotX;
        const startY = rotY;
        const startZ = rotZ;
        const endX = startX + 360 * 5;
        const endY = startY + 360 * 6;
        const endZ = startZ + 360 * 2;
        const startTime = performance.now();
        const duration = 5500;

        await new Promise(resolve => {
            function animate(now) {
                const progress = Math.min((now - startTime) / duration, 1);
                const eased = easeOutQuint(progress);

                rotX = startX + (endX - startX) * eased;
                rotY = startY + (endY - startY) * eased;
                rotZ = startZ + (endZ - startZ) * eased;

                dice.style.transform =
                    `rotateX(${rotX}deg) rotateY(${rotY}deg) rotateZ(${rotZ}deg)`;

                statusText.textContent =
                    progress < 0.4 ? "Spinning fast..." :
                    progress < 0.8 ? "Gradually slowing down..." :
                    "Almost stopped...";

                if (progress < 1) requestAnimationFrame(animate);
                else resolve();
            }
            requestAnimationFrame(animate);
        });

        result.textContent = data.lucky;
        statusText.textContent = `Finished! Range: ${data.minimum} to ${data.maximum}.`;

    } catch (error) {
        statusText.textContent = error.message;
        statusText.className = "error";
    } finally {
        document.body.classList.remove("spinning");
        spinning = false;
        button.disabled = false;
    }
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}

    try:
        first = int(data["minimum"])
        second = int(data["maximum"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Please enter valid whole numbers."}), 400

    if not (-1_000_000_000 <= first <= 1_000_000_000 and
            -1_000_000_000 <= second <= 1_000_000_000):
        return jsonify({"error": "Number is outside the supported range."}), 400

    # Built-in functions: find the lower and upper boundaries.
    lower = min(first, second)
    upper = max(first, second)

    # Generate a random integer within the selected range.
    lucky = random.randint(lower, upper)

    return jsonify({
        "minimum": lower,
        "maximum": upper,
        "lucky": lucky
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
