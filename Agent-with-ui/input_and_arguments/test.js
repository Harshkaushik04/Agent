const args = require("minimist")(process.argv.slice(2));

const rawList = args.links_list;

let list = [];
if (rawList) {
    try {
        list = JSON.parse(rawList);
    } catch (err) {
        console.error("Invalid JSON array:", rawList);
    }
}

console.log("Raw Input:", rawList);
console.log("Parsed List:", list);
console.log("Element 0:", list[0]);
