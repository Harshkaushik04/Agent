import { useState, useEffect} from "react";
import './../App.css'
import axios from "axios"
import { useChat } from "../hooks/useChat";
import * as CustomTypes from '../types'
import { useHtmlTextAreaRef } from "../hooks/useHtmlTextAreaRef";

function Chat() {
    const ctx=useChat()
    const Navigate=ctx.Navigate
    const setHistoryTitles=ctx.setHistoryTitles
    const historyTitles=ctx.historyTitles
    const historyChat=ctx.historyChat
    async function loadHistoryTitles(model:string="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
        const res=await axios.post<CustomTypes.loadHistoryTitlesType>("http://localhost:3000/load-history-titles",{
          model:model
        },{
          headers:{
            token:localStorage.getItem("token")
          }
        })
        if(!res.data.valid){
          Navigate("/login");
          return;
        }
        setHistoryTitles(res.data.titles);
    }

    async function loadNewChat(model:string="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
        const res=await axios.post<CustomTypes.loadNewChatType>("http://localhost:3000/load-new-chat",{
          model:model
        },{
          headers:{
            token:localStorage.getItem("token")
          }
        })
        if(!res.data.valid){
          Navigate("/login");
          return;
        }
        localStorage.setItem("chat_number",String(res.data.chat_number));
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
      <div><ScrollBoxWithClickableBoxesAndToggleBar width={"7vw"} height={"95vh"} titles={historyTitles}/>
      <button style={{width:80,height:40}}
      onClick={async()=>{await loadNewChat()}}>New Chat</button>
      <button style={{width:80,height:40}}
      onClick={()=>{logOut()}}>Log out</button></div>
      {/* <div><SearchBar whetherMessageSent={false}/></div> */}
      <div style={{marginLeft:10}}>{<ScrollBoxWithContentAndSearchBar width1={"90vw"} height1={"88vh"} width2={"80vw"} height2={"8vh"} content={historyChat}/>}</div>
    </div>
  );
}

function ScrollBoxWithContentAndSearchBar({ width1 = 300, height1 = "100vh", width2,height2,content}:CustomTypes.mainBarType) {
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
    }}><SearchBar placeholder="Conversation-model" width={width2} height={height2}/></div>
    </div>
  );
}

function ScrollBoxWithClickableBoxesAndToggleBar({ width = 300, height = "100vh",titles}:CustomTypes.sideBarType) {
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
        alignItems:"center"
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
          <ClickableBox title={content} color="white"/>
        </div>
      ))}
    </div>
  );
}

function ClickableBox({ title,color }:CustomTypes.boxType) {
  const ctx=useChat()
  const Navigate=ctx.Navigate
  const setHistoryChat=ctx.setHistoryChat
  const setHistoryTitles=ctx.setHistoryTitles
  async function handleClickHistory(title:string){
    // console.log("hi")
    const res=await axios.get<CustomTypes.clickHistoryType>("http://localhost:3000/click-history",
    {
      headers:{
        token:localStorage.getItem("token"),
        model:localStorage.getItem("model"),
        chat_number:Number(title.match(/\d+$/)![0])
      }
    }) 
    console.log(`res.data.valid:${res.data.valid}`)
    if(!res.data.valid){
      Navigate("/login");
      return;
    }
    localStorage.setItem("chat_number",title?.match(/\d+$/)![0]);
    // console.log("hi2")
    setHistoryChat(res.data.value_json);
  }
  async function loadHistoryTitles(model:string="DeepSeek-R1-Distill-Qwen-7B-Q4_K_M"){
    const res=await axios.post<CustomTypes.loadHistoryTitlesType>("http://localhost:3000/load-history-titles",{
      model:model
    },{
      headers:{
        token:localStorage.getItem("token")
      }
    })
    if(!res.data.valid){
      Navigate("/login");
      return;
    }
    setHistoryTitles(res.data.titles);
    }
  async function handleDelete(title:string){
    const res=await axios.delete<CustomTypes.deleteChatType>("http://localhost:3000/delete-chat",
      {
        headers:{
          token:localStorage.getItem("token"),
          model:localStorage.getItem("model"),
          chat_number:Number(title.match(/\d+$/)![0])
        }
      }
    )
    if(!res.data.valid){
      Navigate("/login");
      return;
    }
    localStorage.setItem("chat_number",String(res.data.chat_number));
    const storedModel=localStorage.getItem("model")
    if(!storedModel){
      throw new Error("model parameter doesnt exist in local storage")
    }
    await loadHistoryTitles(storedModel);
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

function ChatRenderer({ messages }:CustomTypes.chatMessagesType) {
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
  height = "40px" // Default  minimum height
}:CustomTypes.searchBarType) {
  const ctx=useChat()
  const Navigate=ctx.Navigate
  const setHistoryChat=ctx.setHistoryChat
  const [whetherMessageSent,setWhetherMessageSent]=useState(false);
  const [value, setValue] = useState("");
  const {textareaRef,getTextAreaRefCurrent}=useHtmlTextAreaRef()
  useEffect(() => {
    const textarea = getTextAreaRefCurrent();
    
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
        const userMessage:CustomTypes.messageType={
            role:"user",
            content:value,
            before_think:"",
            after_think:"",
            timestamp:new Date(Date.now())
          }
        setHistoryChat((prev:CustomTypes.messageType[])=>{
          return [...prev,userMessage]
        });
        setValue("");
        const res=await axios.post<CustomTypes.sendMessageType>("http://localhost:3000/send-message",{
          message:value,
          model:localStorage.getItem("model"),
          chat_number:localStorage.getItem("chat_number")
        },
        {
          headers:{
          token:localStorage.getItem("token")
        }})
        if(!res.data.valid) Navigate("/login");
        const res1=await axios.get<CustomTypes.updateChatType>("http://localhost:3000/update-chat",
      {
        headers:{
        token:localStorage.getItem("token"),
        model:localStorage.getItem("model"),
        chat_number:localStorage.getItem("chat_number")
      }})
        if(!res1.data.valid){
          Navigate("/login")
          return;
        }
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