import { useState, useRef, useEffect } from "react";
import './../App.css'
import axios from "axios"
import { useNavigate } from "react-router-dom";

function Chat() {
    const [historyTitles,setHistoryTitles]=useState([]);
    const [historyChat,setHistoryChat]=useState([]);
    const Navigate=useNavigate();
    async function loadHistoryTitles(model="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
        const res=await axios.post("http://localhost:3000/load-history-titles",{
          model:model
        },{
          headers:{
            token:localStorage.getItem("token")
          }
        })
        if(!res.data.valid) Navigate("/login");
        setHistoryTitles(res.data.titles);
    }

    async function loadNewChat(model="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
        const res=await axios.post("http://localhost:3000/load-new-chat",{
          model:model
        },{
          headers:{
            token:localStorage.getItem("token")
          }
        })
        if(!res.data.valid) Navigate("/login");
        localStorage.setItem("chat_number",res.data.chat_number);
        await loadHistoryTitles(model);
    }

    function logOut(){
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        Navigate("/login");
    }
    useEffect(()=>{
      loadHistoryTitles()
    },[])

    return (
      <div style={{color:"yellow",display:"flex"}}>
        <div><ScrollBoxWithClickableBoxesAndToggleBar width={"7vw"} height={"95vh"} titles={historyTitles} setHistoryChat={setHistoryChat} Navigate={Navigate} setHistoryTitles={setHistoryTitles}/>
        <button style={{width:80,height:40}}
        onClick={async()=>{await loadNewChat()}}>New Chat</button>
        <button style={{width:80,height:40}}
        onClick={()=>{logOut()}}>Log out</button></div>
        {/* <div><SearchBar whetherMessageSent={false}/></div> */}
        <div style={{marginLeft:10}}>{<ScrollBoxWithContentAndSearchBar width1={"90vw"} height1={"88vh"} width2={"80vw"} content={historyChat} setHistoryChat={setHistoryChat}/>}</div>
      </div>
    );
  }
function ScrollBoxWithContentAndSearchBar({ width1 = 300, height1 = "100vh", width2,height2,content,setHistoryChat }) {
  return (
    <div style={{
      // border: "1px solid #ccc"
      }}>
    <div
      style={{
        width:width1,
        height:height1,
        // border: "1px solid #ccc",
        overflowY: "scroll", // Scrollbar appears only when needed
        overflowX: "hidden",
        padding: "8px",
        // Optional: Force scrollbar to always show (even if empty) for testing:
        // overflowY: "scroll" 
      }}
    >
      <ChatRenderer messages={content}/>
    </div>
    <div style={{
      display:"flex",
      paddingTop:30,
      justifyContent:"center"
    }}><SearchBar placeholder="Conversation-model" width={width2} height={height2} historyChat={content} setHistoryChat={setHistoryChat}/></div>
    </div>
  );
}

function ScrollBoxWithClickableBoxesAndToggleBar({ width = 300, height = "100vh", titles,setHistoryChat,Navigate,setHistoryTitles}) {
  const [removeSideBar,setRemoveSideBar]=useState(false);
  function toggle(){
    setRemoveSideBar(removeSideBar=>!removeSideBar)
  }
  return (
    <div
      style={{
        width:width,
        height:height,
        // border: "1px solid #ccc",
        overflowY: "scroll", // Scrollbar appears only when needed
        overflowX: "hidden",
        padding: "8px",
        // Optional: Force scrollbar to always show (even if empty) for testing:
        // overflowY: "scroll" 
      }}
    >
      <div className="hoverBox"
      style={{
        color:"white",
        width:20,
        height:20,
        cursor:"pointer",
        marginBottom:10,
        fontSize:25,
        display:"flex",
        atitles:"center"
      }}><button onClick={()=>{
        toggle();
      }}>☰</button></div>
      {titles.map((content, i) => (
        (!removeSideBar)&&<div
          key={i}
          style={{
            color: "green", // <--- 2. FIXED: Added quotes around "white"
            marginBottom: "6px",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          <ClickableBox title={content} color="white" setHistoryChat={setHistoryChat} Navigate={Navigate} setHistoryTitles={setHistoryTitles}/>
        </div>
      ))}
    </div>
  );
}
function ClickableBox({ title,color,setHistoryChat,Navigate,setHistoryTitles }) {
  async function handleClickHistory(title){
    // console.log("hi")
    const res=await axios.get("http://localhost:3000/click-history",
    {
      headers:{
        token:localStorage.getItem("token"),
        model:localStorage.getItem("model"),
        chat_number:Number(title.match(/\d+$/)[0])
      }
    }) 
    console.log(`res.data.valid:${res.data.valid}`)
    if(!res.data.valid) Navigate("/login");
    localStorage.setItem("chat_number",title.match(/\d+$/)[0]);
    // console.log("hi2")
    await setHistoryChat(res.data.value_json);
  }
  async function loadHistoryTitles(model="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
    const res=await axios.post("http://localhost:3000/load-history-titles",{
      model:model
    },{
      headers:{
        token:localStorage.getItem("token")
      }
    })
    if(!res.data.valid) Navigate("/login");
    setHistoryTitles(res.data.titles);
    }
  async function handleDelete(title){
    const res=await axios.delete("http://localhost:3000/delete-chat",
      {
        headers:{
          token:localStorage.getItem("token"),
          model:localStorage.getItem("model"),
          chat_number:Number(title.match(/\d+$/)[0])
        }
      }
    )
    if(!res.data.valid) Navigate("/login");
    localStorage.setItem("chat_number",res.data.chat_number);
    await loadHistoryTitles(localStorage.getItem("model"));
  }
  return (
    <div>
    <span className="hoverBox"
      onClick={
        async ()=>{await handleClickHistory(title)}}
      style={{
        display: "inline-block",
        textDecoration: "none",
        color: color,
        cursor:"pointer"
      }}
    >
      {title}
    </span>
    <span style={{marginLeft:5,cursor:"pointer"}} 
    onClick={async ()=>{await handleDelete(title)}}><img src="/delete.png" style={{width:15,height:15,backgroundColor:"white"}}/></span>
    </div>
  );
}
function ChatRenderer({ messages }) {
  return (
      <div style={{ fontFamily: "monospace", padding: "10px" }}>
          {messages?.map((msg, index) => (
              <div key={index} style={{ marginBottom: "12px" }}>

                  {/* USER */}
                  {msg.role == "user" && (
                      <div style={{ color: "white" }}>
                          <strong>USER:</strong> {msg.content}
                      </div>
                  )}

                  {/* MODEL */}
                  {msg.role =="model" && (
                      <>  
                        <span style={{ color: "white" }}>
                          <strong>MODEL:</strong> 
                        </span>
                          <div style={{ color: "#4CAF50" }}>  
                              {msg.before_think}
                          </div>
                          <div style={{ color: "yellow" }}>
                              {msg.after_think}
                          </div>
                      </>
                  )}
                  {/* SYSTEM */}
                  {msg.role =="system" && (
                      <>  
                          <span style={{ color: "white" }}>
                          <strong>SYSTEM:</strong> {msg.content}
                        </span>
                      </>
                  )}

              </div>
          ))}
      </div>
  );
}

function SearchBar({ 
  placeholder = "Conversation-model",
  width = "480px",
  height = "40px" // Default minimum height
  ,historyChat,setHistoryChat,Navigate
}) {
  const [whetherMessageSent,setWhetherMessageSent]=useState(false);
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = "auto"; 
    
    const lineHeight = 20;          
    const maxLines = 10;

    const scrollHeight = textarea.scrollHeight;
    const maxHeight = lineHeight * maxLines;

    // Set the new height
    textarea.style.height = Math.min(scrollHeight, maxHeight) + "px";
    
    // Handle scrollbar visibility
    textarea.style.overflowY = scrollHeight > maxHeight ? "auto" : "hidden";
    
  }, [value]);
  async function sendMessage(){
        setWhetherMessageSent(true);
        setHistoryChat((prev)=>{
          return [...prev,{
            role:"user",
            content:value
          }]
        });
        setValue("");
        const res=await axios.post("http://localhost:3000/send-message",{
          message:value,
          model:localStorage.getItem("model"),
          chat_number:localStorage.getItem("chat_number")
        },
        {
          headers:{
          token:localStorage.getItem("token")
        }})
        if(!res.data.valid) Navigate("/login");
        const res1=await axios.get("http://localhost:3000/update-chat",
      {
        headers:{
        token:localStorage.getItem("token"),
        model:localStorage.getItem("model"),
        chat_number:localStorage.getItem("chat_number")
      }})
        console.log(`res1.data.value_json:${res1.data.value_json}`)
        setHistoryChat(res1.data.value_json);
        setWhetherMessageSent(false);
    }
    function stopMessage(){
        setWhetherMessageSent(false);
    }
  return (
    <div
      style={{
        // --- UPDATED LAYOUT TO GROW UPWARDS ---
        position: "fixed",      // Remove this if you want it to sit in the normal flow
        bottom: "20px",         // Anchors it to the bottom
        left: "50%",            // Centers it horizontally
        transform: "translateX(-50%)", // Centers it horizontally
        zIndex: 1000,           // Ensures it stays on top of other content
        // -------------------------------------

        width: width,        
        minHeight: height,   
        
        display: "flex",
        alignItems: "center", 
        backgroundColor: "#808080",
        borderRadius: "30px",
        padding: "6px 10px",
        gap: "8px",
      }}
    >
      {/* LEFT ICON */}
      <img 
        src="/search.svg"
        alt="search"
        style={{ width: 16, height: 16 }}
      />

      {/* TEXTAREA */}
      <textarea
        ref={textareaRef}
        value={value}
        rows={1}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        style={{
          flex: 1,
          border: "none",
          outline: "none",
          fontSize: "14px",
          background: "transparent",
          resize: "none",
          overflowY: "hidden",
          padding: 0,
          
          lineHeight: "20px", 
          minHeight: "20px",
          
          boxSizing: "content-box", 
          margin: 0,
        }}
      />

      {/* RIGHT ICON */}
      {whetherMessageSent ? (
        <img
          src="/stop.png"
          alt="stop"
          style={{ width: 18, height: 18, cursor: "pointer" }} 
          onClick={()=>{setWhetherMessageSent(false)}}
        />
      ) : (
        <img
          src="/send.png"
          alt="send"
          style={{ width: 18, height: 18, cursor: "pointer" }}
          onClick={async ()=>{await sendMessage()}}
        />
      )}
    </div>
  );
}


export default Chat;