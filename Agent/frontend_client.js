const args = require("minimist")(process.argv.slice(2));
const axios = require("axios");
const readline = require("readline");

const links_list = args.links_list;
const paths_list = args.paths_list;
const texts_list = args.texts_list;
const prompt = args.prompt;

function askUser(what_to_ask) {
    return new Promise((resolve) => {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        rl.question(`${what_to_ask}`, (answer) => {
            rl.close();
            resolve(answer.trim());
        });
    });
}

async function sendRequest(username,sessionNumber) {
    let user_input = "disapprove";
    let res = {};
    while (user_input !== "approve") {
        res = await axios.post("http://localhost:3000/make-plan", {
            links_list:links_list,
            paths_list:paths_list,
            texts_list:texts_list,
            prompt:prompt,
            username:username,
            sessionNumber:sessionNumber
        });
        console.log(`PLAN:\n${res.data.plan}`);
        user_input = await askUser("enter(approve/disapprove)");
    }

    const res1 = await axios.post("http://localhost:3000/use-tools", {
        plan: res.data.plan
    });

    console.log(`Response:\n${res1.data.response}`);
}
async function userLogin(){
    let user_input=await askUser("enter username:");
    let approval=await askUser("confirm?(yes/no)");
    while(approval!="yes"){
        user_input=await askUser("enter username:");
    }
    const res=await axios.post("http://localhost:3000/login",{
        username:user_input
    });
    let sessionNumber=res.data.sessionNumber;
    // console.log(`type of sessionNumber:${typeof sessionNumber}`)
    return {username:user_input,sessionNumber:sessionNumber};
}

async function main(){
    let {username,sessionNumber}=await userLogin();
    await sendRequest(username,sessionNumber);
}
main();

