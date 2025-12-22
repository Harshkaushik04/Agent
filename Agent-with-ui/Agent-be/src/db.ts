import mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();
const MONGO_URL="mongodb://localhost:27017/ConversationModel"
import * as CustomTypes from "./types.js"

export async function connectDB():Promise<void>{
    mongoose.connect(MONGO_URL);
}
 // PROXY_MODEL,username,PROXY_TITLE---->num_chats
const history=new mongoose.Schema<CustomTypes.historySchemaType>({
    username:String,
    model:String,
    title:String,
    messages:[{
        role:String,
        content:String,
        before_think:String,
        after_think:String,
        timestamp:{type:Date,default:Date.now}
    }],
    summaries:[{
        description:String,
        content:String
    }]
});
const users=new mongoose.Schema<CustomTypes.userSchemaType>({
    username:String,
    password:String
});

const episodicMemory=new mongoose.Schema<CustomTypes.episodicMemorySchemaType>({
    username:String,
    title:String,
    memories:[{
        description:String,
        content:String
    }]
})
//to get back to same working memory after disconnected
const workingMemory=new mongoose.Schema<CustomTypes.workingMemorySchemaType>({
    chat_history:[{
        serial_number:Number,
        role:String,
        content:String
    }],
    previous_actions_and_logs:[{
        serial_number:Number,
        description:String,
        function:String,
        inputs:{
            type:Map,
            of:String
        },
        outputs:{
            type:Map,
            of:String    
        },
        log:String,
        filter_words:[{type:String,default:[]}]
    }],
    final_goal:String,
    current_goal:String,
    rough_plan_to_reach_goal:[{
        serial_number:Number,
        description:String,
        function:String,
        inputs:{
            type:Map,
            of:String
        },
        brief_expected_outputs:{
            type:Map,
            of:String
        },
        status:String
    }],
    summaries:[{
        serial_number:Number,
        description:String,
        content:String,
        filter_words:[{type:String,defualt:[]}]
    }],
    env_state:[{
        serial_number:Number,
        description:String,
        content:String
    }],
    episodic_memory_descriptions:[{
        serial_number:Number,
        description:String
    }],
    current_function_to_execuete:{
        function_name:String,
        inputs:{
            type:Map,
            of:String
        }
    },
    things_to_note:{
        serial_number:Number,
        description:String,
        content:String
    },
    final_goal_completed:String
})

history.index({username:1,model:1,title:1},{unique:true});
episodicMemory.index({username:1,title:1},{unique:true})
export const HistoryModel=mongoose.model("history",history);
export const UserModel=mongoose.model("users",users);
export const EpisodicMemoryModel=mongoose.model("episodicMemory",episodicMemory)
export const workingMemoryModel=mongoose.model("workingMemory",workingMemory)