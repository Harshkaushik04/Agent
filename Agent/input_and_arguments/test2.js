const fs=require("fs").promises

async function read_file(){
    let output=await fs.readFile("../com/make_plan.txt","utf-8");
    console.log(output);
}

read_file();