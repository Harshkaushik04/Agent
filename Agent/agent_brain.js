const express=require("express");
const { spawn } = require("child_process");
const fs = require("fs").promises;
const path = require("path");
const moongoose=require("mongoose")
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
4. html_cleaner(raw_html): [cleaned_html(string),key string]
5. write_file(file_path,content,whether_addition): <no output>
6. read_file(file_path): [file_content(string)]
7. make_rag_database(data): [folder_path(string),key string]
8. retrieval_from_rag_database(search_query,top_k,database_folder_path): [list of string top_k chunks,key string]
9. generation(list of string top_k chunks,query): [full answer string, after think string,key string]
10. file_checker(file_path): updated_file_path(string)
11. video_to_text(video_link/video_path,whether_link_or_path): [text string,key string]
12. audio_to_text(audio_link/audio_path,whether_link_or_path): [text string,key string]
13. question_answer(text,query): [text string,key string]
14. summarise(text):[text string,key string]
 */
async function runPython(links_list,paths_list,texts_list,prompt){
    let response={};
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
    return response;
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
    let links_list=req.body.links_list;
    let paths_list=req.body.paths_list;
    let texts_list=req.body.texts_list;
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
        session.links_list=links_list;
    }
    catch(e){}
    try{
        session.paths_list=paths_list;
    }
    catch(e){}
    try{
        session.texts_list=texts_list;
    }
    catch(e){}
    try{
        session.prompt=prompt;
    }
    catch(e){}
    let response=await runPython(links_list,paths_list,texts_list,prompt);
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