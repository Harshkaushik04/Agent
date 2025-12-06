const mongoose=require("mongoose")
require("dotenv").config();
const MONGO_URL=process.env.MONGO_URL;

async function connectDB(){
    mongoose.connect(MONGO_URL);
}

const history=new mongoose.Schema({
    username:String,
    model:String,
    title:String,
    messages:{
        role:String,
        text:String,
        timestamp:{type:Date,default:Date.now}
    }
});
const users=new mongoose.Schema({
    username:String,
    password:String
});

history.index({username:1,model:1,title:1},{unique:true});

const HistoryModel=mongoose.model("history",history);
const UserModel=mongoose.model("users",users);

module.exports={connectDB,HistoryModel,UserModel};