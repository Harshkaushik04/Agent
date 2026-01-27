import mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();
const MONGO_URL="mongodb://localhost:27017/ConversationModel"
import * as CustomTypes from "./types.js"
import { timeStamp } from "console";

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
    }]
});

const completeHistory=new mongoose.Schema<CustomTypes.completeHistorySchemaType>({
    username:String,
    model:String,
    title:String,
    messages:[{
        role:String,
        content:String,
        messageType:String,
        timeStamp:{type:Date,default:Date.now}
    }]
});

const users=new mongoose.Schema<CustomTypes.userSchemaType>({
    username:String,
    password:String
});

const episodicMemory=new mongoose.Schema<CustomTypes.episodicMemorySchemaType>({
    username:String,
    memories:[{
        serial_number:Number,
        description:String,
        content:String
    }]
})
//to get back to same working memory after disconnected
const workingMemory=new mongoose.Schema<CustomTypes.workingMemoryWithUserSchemaType>({
    username:String,
    model:String,
    title:String,
    chat_history:[{
        serial_number:Number,
        role:String,
        content:String
    }],
    previous_actions_and_logs:[{
        serial_number:Number,
        description:String,
        function_name:String,
        inputs:{
            type:Map,
            of:mongoose.Schema.Types.Mixed
        },
        outputs:{
            type:Map,
            of:mongoose.Schema.Types.Mixed   
        },
        log:String,
        filter_words:[{type:String,default:[]}]
    }],
    final_goal:String,
    current_goal:String,
    rough_plan_to_reach_goal:[{
        serial_number:Number,
        description:String,
        function_name:String,
        inputs:{
            type:Map,
            of:mongoose.Schema.Types.Mixed
        },
        brief_expected_outputs:[{type:String,default:[]}],
        status:String
    }],
    variables:[{
        serial_number:Number,
        variable_type:String,
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
    current_function_to_execute:{
        function_name:String,
        inputs:{
            type:Map,
            of:mongoose.Schema.Types.Mixed
        }
    },
    things_to_note:[{
        serial_number:Number,
        description:String,
        content:String
    }],
    final_goal_completed:String
})

const episodicMemoryDescriptions=new mongoose.Schema<CustomTypes.episodicMemoryDescriptionsSchemaType>({
    username:String,
    memory_descriptions:[{
        serial_number:Number,
        description:String
    }]
})

history.index({username:1,model:1,title:1},{unique:true});
episodicMemory.index({username:1},{unique:true});
workingMemory.index({username:1,title:1,model:1},{unique:true});
episodicMemoryDescriptions.index({username:1},{unique:true});
export const HistoryModel=mongoose.model("history",history);
export const CompleteHistoryModel=mongoose.model("completeHistory",completeHistory)
export const UserModel=mongoose.model("users",users);
export const EpisodicMemoryModel=mongoose.model("episodicMemory",episodicMemory)
export const WorkingMemoryModel=mongoose.model("workingMemory",workingMemory)
export const EpisodicMemoryDescriptionsModel=mongoose.model("episodicMemoryDescriptions",episodicMemoryDescriptions)

/**
mongo db run command:
mongod --dbpath ~/mongodb-data
chroma db run command:
sudo docker run -d --name chroma-server \
  -p 8000:8000 \
  -v /home/harsh/RAG/Agent-with-ui/Agent-be/my_chroma_data:/chroma/chroma \
  -e IS_PERSISTENT=TRUE \
  -e PERSIST_DIRECTORY=/chroma/chroma \
  chromadb/chroma:latest
 */