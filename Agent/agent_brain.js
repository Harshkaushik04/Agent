const express=require("express");
const { spawn } = require("child_process");
const fs = require("fs").promises;
const path = require("path");

const MAIN_DATABASE="db.json";
const USERS_DATABASE="users.json"
const PORT=3000;
app=express();
app.use(express.json());
/*
 * tools:
 * 
 */
let response={};
async function runPython(links_list,paths_list,texts_list,prompt){
    const args1 = JSON.stringify(links_list);
    const args2 = JSON.stringify(paths_list);
    const args3 = JSON.stringify(texts_list);
    const args4 = JSON.stringify(prompt);
    const PythonPromise=new Promise((resolve,reject)=>{
        console.log("[runPython function] entered pythonPromise")
        console.log("CWD:", process.cwd());
        const py=spawn("python3",["-u",
            "-W","ignore",
            path.join(__dirname,"make_plan.py"),
            "--links_list",args1,
            "--paths_list",args2,
            "--texts_list",args3,
            "--prompt",args4]);
        py.stdout.on("data", (data) => {
            // console.log(data.toString());
            process.stdout.write(data.toString());
        });
        py.stderr.on("data",(data)=>{
            response.error=data.toString();
            console.error(`[PYTHON ERROR]: ${data.toString()}`);
        })
        py.on("close",(code)=>{
            if(code!==0){
                response.error="Python crashed!";
            }
            else resolve()
        })
    })
    await PythonPromise;
    let raw_output="";
    try {
        raw_output = await fs.readFile("com/make_plan.txt", "utf-8");
        } catch (e) {
            throw new Error("Output JSON missing: " + e);
        }
    response.plan=raw_output;
}

async function handle_login(username,sessionNumber){
    const raw = await fs.readFile(USERS_DATABASE, "utf-8");
    const extracted = JSON.parse(raw);
    let len=extracted["users"].length;
    for(let i=0;i<len;i++){
        if(extracted["users"][i]==username){

        }
    }

}

app.post("/make-plan",async (req,res)=>{
    console.log("[make-plan] request recieved to make plan")
    let links_list=req.body.links_list;
    let paths_list=req.body.paths_list;
    let texts_list=req.body.texts_list;
    let prompt=req.body.prompt;
    let username=req.body.username;
    let sessionNumber=req.body.sessionNumber;

    await runPython(links_list,paths_list,texts_list,prompt);
    res.json(response);
})

app.listen(PORT,()=>{console.log(`listening at post ${PORT}`)});