import mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();
const MONGO_URL="mongodb://localhost:27017/ConversationModel"

export async function connectDB(){
    mongoose.connect(MONGO_URL);
}
 // PROXY_MODEL,username,PROXY_TITLE---->num_chats
const history=new mongoose.Schema({
    username:String,
    model:String,
    title:String,
    messages:[{
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:{type:Date,default:Date.now}
}]
});
const users=new mongoose.Schema({
    username:String,
    password:String
});

history.index({username:1,model:1,title:1},{unique:true});

export const HistoryModel=mongoose.model("history",history);
export const UserModel=mongoose.model("users",users);
