//to be edited
const express=require("express");
const cors=require("cors");
const jwt=require("jsonwebtoken")
let app=express();

let users=[];
const JWT_SECRET="randomnum1";

app.use(express.json());
app.use(cors({
    "origin":"http://127.0.0.1:5500"
}));

function authMiddleware(req,res,next){
    if(!req.headers.token){
        return res.json({
            "redirect":"http://127.0.0.1:5500/4_node/part5_jwt/sign_up.html"
        });
    }
    else{
        try {
            const decryptedData = jwt.verify(req.headers.token, JWT_SECRET);
            req.username = decryptedData.username; 
            next();
        } catch (err) {
            return res.json({
                redirect: "http://127.0.0.1:5500/4_node/part5_jwt/sign_up.html"
            });
        }
    }
}

app.post("/sign-up",(req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    for(let item of users){
        if(item.username==username){
            return res.json({"msg":"username already taken"});
        }
    }
    //username not taken=>make new id
    users.push({
        "username":username,
        "password":password
    });
    res.json({
        "resp":"http://127.0.0.1:5500/4_node/part5_jwt/sign_in.html"
    })
})

app.post("/sign-in",(req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    for(let item of users){
        if(item.username==username && item.password==password){
            item.token=jwt.sign(
            {
                "username":username
            },JWT_SECRET);
            return res.json({
                "username":username,
                "token":item.token,
                "resp":"http://127.0.0.1:5500/4_node/part5_jwt/home.html"
            })
        }
    }
    return res.json({"msg":"credentials dont match!"});
})

app.post("/me",(req,res)=>{
    res.json(users);
    console.log(users);
})
app.use(authMiddleware);
app.get("/",(req,res)=>{
    console.log("hit '/' url")
    res.json({
        "msg":"remain here",
        "username":req.username
    });
})

app.listen(3000);