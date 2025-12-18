const readline = require("readline");

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

let lines = [];
let lastWasEmpty = false;

console.log("Enter text (press Enter twice to finish):");

rl.on("line", (input) => {
    if (input === "") {
        if (lastWasEmpty) {
            rl.close();
            return;
        }
        lines.push("");
        lastWasEmpty = true;
        return;
    }

    lines.push(input);
    lastWasEmpty = false;
});

rl.on("close", () => {
    console.log("\nFinal output (no quotes):");
    console.log(lines.join("\n"));
});
