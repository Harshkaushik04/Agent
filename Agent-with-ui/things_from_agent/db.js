const mongoose = require("mongoose");
require("dotenv").config();
const MONGO_URL = process.env.MONGO_URL;

const connectDB = async () => {
    try {
        await mongoose.connect(MONGO_URL);
        console.log("MongoDB Connected Successfully");
    } catch (err) {
        console.error("MongoDB Connection Error:", err);
        process.exit(1);
    }
};

// 1. User Schema (Replaces users.json)
// Keeps track of valid users.
const userSchema = new mongoose.Schema({
    username: { 
        type: String, 
        required: true, 
        unique: true,
        trim: true 
    },
    createdAt: { 
        type: Date, 
        default: Date.now 
    },
    lastSessionNumber:{type:Number,default:0}
});

// 2. Session Schema (Replaces the complex nested part of db.json)
// Each document represents ONE session for ONE user.
const sessionSchema = new mongoose.Schema({
    username: { type: String, required: true, index: true },
    sessionNumber: { type: Number, required: true },
    plan: { type: String, default: "" },
    links_list: { type:[String] },
    paths_list: { type: [String] },
    texts_list: { type: [String] },
    prompt:{type: String},
    summaries: { 
        type: Map, 
        of: String 
    },
    question_answers: { 
        type: Map, 
        of: String 
    },
    top_k_context_chunks: { 
        type: Map, 
        of: [String] 
    },
    database_for_rag: { 
        type: Map, 
        of: String 
    },
    transcripted_audio_to_text: { 
        type: Map, 
        of: String 
    },
    transcripted_video_to_text: { 
        type: Map, 
        of: String 
    },
    sentences: { 
        type: Map, 
        of: String 
    },
    search_queries: { 
        type: Map, 
        of: [String] 
    },
    urls: { 
        type: Map, 
        of: [String] 
    },
    raw_htmls: { 
        type: Map, 
        of: String 
    },
    cleaned_htmls: { 
        type: Map, 
        of: String 
    },
    generation: { 
        type: Map, 
        of: [String] 
    }
}, { timestamps: true });

sessionSchema.index({ username: 1, sessionNumber: 1 }, { unique: true });
const userModel = mongoose.model("User", userSchema);
const sessionModel = mongoose.model("Session", sessionSchema);

module.exports = { connectDB, userModel, sessionModel };