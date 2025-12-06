import {connectDB,HistoryModel,UserModel} from "./db.js"
const express=require("express");
const cors=require("cors");
const jwt=require("jsonwebtoken")
let app=express();

const JWT_SECRET="randomnum1";
const PORT=3000;
app.use(express.json());
app.use(cors({
    "origin":"http://localhost:5173"
}));

function authMiddleware(req,res,next){
    if(!req.headers.token){
        return res.json({
            valid:false
        });
    }
    else{
        try {
            const decryptedData = jwt.verify(req.headers.token, JWT_SECRET);
            req.username = decryptedData.username; 
            next();
        } catch (err) {
            return res.json({
                valid:false
            });
        }
    }
}

app.post("/signup",async (req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    let user=await UserModel.findOne({
        username:username
    })
    if(user){
        res.json({
            whetherDuplicate:true
        })
    }
    //username not taken=>make new id
    await UserModel.create({
        username:username,
        password:password
    })
    res.json({
        whetherDuplicate:false
    })
})

app.post("/login",async (req,res)=>{
    let username=req.body.username;
    let password=req.body.password;
    let user=await UserModel.findOne({
        username:username,
        password:password
    });
    if(user){
        let jwt_token=jwt.sign({
            "username":username
        },JWT_SECRET);
        res.json({
            username:username,
            token:jwt_token,
            valid:true
        })
    }
    else{
        res.json({
            valid:false
        });
    }
})

app.use(authMiddleware);
app.get("/",(req,res)=>{

})
app.get("/chat",(req,res)=>{
    
})

app.listen(PORT,()=>{
    console.log(`server listening at port ${PORT}`)
})