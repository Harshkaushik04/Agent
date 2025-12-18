const express=require("express");
const { spawn } = require("child_process");
const fs = require("fs").promises;
const path = require("path");
// const mongoose=require("mongoose")
const { connectDB,userModel,sessionModel }=require("./db");
const PORT=3000;

connectDB();

app=express();
app.use(express.json());
/*
 * tools:
 * 1. search_query_generation(sentence): [list of strings,key string]
2. search_engine_1(search_query,top_k): [list of string top_k urls,key string]
3. search_engine_2(url): [raw_html(string),key string]
4. html_cleaner(raw_html,url): [cleaned_html(string),key string]
5. write_file(file_path,content,whether_addition): <no output>
6. read_file(file_path): [file_content(string)]
7. make_rag_database(data): [folder_path(string),key string]
8. retrieval_from_rag_database(search_query,top_k,database_folder_path): [list of Docs top_k chunks,key string]
9. generation_from_context(list of Docs top_k chunks,query): [full answer string, after think string,key string]
10. file_checker(file_path): updated_file_path(string)
11. video_to_text(video_link/video_path,whether_link_or_path): [text string,key string]
12. audio_to_text(audio_link/audio_path,whether_link_or_path): [text string,key string]
13. question_answer(text,query): [text string,key string]
14. summarise(text):[text string,key string]
new::15. complete_search_engine(search_query,top_k): [combined context,key string] 
new::16. retrieval_from_context(search_query,context,retrieve_n_results,chunk_size=1000,chunk_overlap=400): [retrieved_context,key string]
 */
function parseDeepSeekOutput(text) {
    // 1. Remove the Python log line first (Crucial step)
    let cleanText = text.replace("[make_plan.py] serving the request", "");

    // 2. Remove the thought block
    // The Regex explanation:
    // ^              -> Start of the string
    // (?:<think>)?   -> Optionally match "<think>" if it's there, but don't fail if it's missing
    // [\s\S]*?       -> Match everything (including newlines) non-greedily...
    // <\/think>      -> ...until we hit the closing tag
    cleanText = cleanText.replace(/^(?:<think>)?[\s\S]*?<\/think>/, "");

    return cleanText.trim();
}

// async function runPython(links_list,paths_list,texts_list,prompt){
//     let response={};
//     const args1 = JSON.stringify(links_list);
//     const args2 = JSON.stringify(paths_list);
//     const args3 = JSON.stringify(texts_list);
//     const args4 = JSON.stringify(prompt);
//     const PythonPromise=new Promise((resolve,reject)=>{
//         console.log("[runPython function] entered pythonPromise")
//         console.log("CWD:", process.cwd());
//         const py=spawn("python3",["-u",
//             "-W","ignore",
//             path.join(__dirname,"make_plan.py"),
//             "--links_list",args1,
//             "--paths_list",args2,
//             "--texts_list",args3,
//             "--prompt",args4]);
//         py.stdout.on("data", (data) => {
//             // console.log(data.toString());
//             process.stdout.write(data.toString());
//         });
//         py.stderr.on("data",(data)=>{
//             response.error=data.toString();
//             console.error(`[PYTHON ERROR]: ${data.toString()}`);
//         })
//         py.on("close",(code)=>{
//             if(code!==0){
//                 response.error="Python crashed!";
//             }
//             else resolve()
//         })
//     })
//     await PythonPromise; 
//     let raw_output="";
//     try {
//         raw_output = await fs.readFile("com/make_plan.txt", "utf-8");
//         } catch (e) {
//             throw new Error("Output JSON missing: " + e);
//         }
//     response.plan=raw_output;
//     return response;
// }
async function runPython(prompt) {
    const args1 = JSON.stringify(prompt);

    // We wrap everything in a Promise that returns the final clean string
    const planText = await new Promise((resolve, reject) => {
        console.log("[runPython function] entered pythonPromise");
        console.log("CWD:", process.cwd());

        const py = spawn("python3", [
            "-u",
            "-W", "ignore",
            path.join(__dirname, "make_plan.py"),
            "--prompt", args1
        ]);

        let fullRawOutput = ""; // Variable to store the stream

        py.stdout.on("data", (data) => {
            const chunk = data.toString();
            fullRawOutput += chunk;       // 1. Accumulate
            process.stdout.write(chunk);  // 2. Stream to console/UI
        });

        py.stderr.on("data", (data) => {
            // Log errors but don't reject immediately (often just warnings)
            console.error(`[PYTHON ERROR]: ${data.toString()}`);
        });

        py.on("close", (code) => {
            if (code !== 0) {
                reject(new Error("Python crashed!"));
            } else {
                // 3. Clean the accumulated output
                const cleaned = parseDeepSeekOutput(fullRawOutput);
                resolve(cleaned); // 4. Return the clean text
            }
        });
    });

    // Construct the response object
    return { plan: planText };
}

async function handle_login(username){
    let user=await userModel.findOne({
        username:username
    })
    if(!user){
        console.log(`[login] making new entry into users database: ${username}`);
        user=await userModel.create({
            username:username
        });
    }
    await sessionModel.create({
        username:username,
        sessionNumber:user.lastSessionNumber+1
    })  
    user.lastSessionNumber++;
    await user.save();
    return user.lastSessionNumber;
}

async function callTools(plan){
    
}

app.post("/make-plan",async (req,res)=>{
    console.log("[make-plan] request recieved to make plan")
    let prompt=req.body.prompt;
    let username=req.body.username;
    let sessionNumber=req.body.sessionNumber;
    // console.log(`[make-plan]type of:sessionNumber:${typeof sessionNumber}`)
    let session=await sessionModel.findOne({
        username:username,
        sessionNumber:sessionNumber
    })
    console.log(`[make-plan] sessionNumber: ${sessionNumber}`)
    try{
        session.prompt=prompt;
    }
    catch(e){}
    let response=await runPython(prompt);
    session.plan=response.plan;
    await session.save();
    res.json(response);
})

app.post("/login",async (req,res)=>{
    let username=req.body.username;
    console.log(`[login] request received to login with username ${username}`)
    let sessionNumber=await handle_login(username);
    // console.log(`[login] value of sessionNumber:${sessionNumber}`)
    res.json({
        sessionNumber:sessionNumber
    });
})

app.post("/use-tools",async (req,res)=>{
    let plan=req.body.plan;
    await callTools(plan);
    res.json({
        "response":"done"
    })
})

app.listen(PORT,()=>{console.log(`listening at post ${PORT}`)});