import { useState, useRef, useEffect } from "react";
import './../App.css'
function Chat() {
  const [historyTitles,setHistoryTitles]=useState();
  const [historyChat,setHistoryChat]=useState();
  // 1. Added more items so the content exceeds 200px height
  const testItems = [
    "History 1", "History 2", "History 3", "History 4", 
    "History 5", "History 6", "History 7", "History 8", 
    "History 9", "History 10", "History 11", "History 12"
  ];

  return (
    <div style={{color:"yellow",display:"flex"}}>
      <div><ScrollBoxWithClickableBoxesAndToggleBar width={"7vw"} height={"95vh"} titles={testItems} />
      <button style={{width:80,height:40}}>Log out</button></div>
      {/* <div><SearchBar whetherMessageSent={false}/></div> */}
      <div style={{marginLeft:10}}>{<ScrollBoxWithContentAndSearchBar width1={"90vw"} height1={"88vh"} width2={"80vw"} content={random_text} whetherMessageSent={false}/>}</div>
    </div>
  );
}
function ScrollBoxWithContentAndSearchBar({ width1 = 300, height1 = "100vh", width2,height2,content,whetherMessageSent }) {
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
      {content}
    </div>
    <div style={{
      display:"flex",
      paddingTop:30,
      justifyContent:"center"
    }}><SearchBar placeholder="Conversation-model" width={width2} height={height2} whetherMessageSent={whetherMessageSent}/></div>
    </div>
  );
}

function ScrollBoxWithClickableBoxesAndToggleBar({ width = 300, height = "100vh", titles}) {
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
          <ClickableBox href={"https://www.youtube.com/"} content={content} color="white"/>
        </div>
      ))}
    </div>
  );
}
function ClickableBox({ href, content,color }) {
  return (
    <a className="hoverBox"
      href={href}
      style={{
        display: "block",
        textDecoration: "none",
        color: color,
      }}
    >
      {content}
    </a>
  );
}
function SearchBar({ 
  placeholder = "Conversation-model",
  width = "480px",
  height = "40px", // Default minimum height
  whetherMessageSent 
}) {

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
        />
      ) : (
        <img
          src="/send.png"
          alt="send"
          style={{ width: 18, height: 18, cursor: "pointer" }}
        />
      )}
    </div>
  );
}

let random_text = `
Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled.

In other words:

The element should not move when the page scrolls
The scrollbar inside the element should scroll normally
The element must always stay in the same spot on the screen

This is exactly what position: fixed does.

Solution: Use position: "fixed" on the scroll container

<div
  style=\{{
    position: "fixed",
    top: "20px",
    right: "20px",
    width: "300px",
    height: "400px",
    background: "#222",
    overflowY: "auto",
    color: "white",
    padding: "10px",
    borderRadius: "8px",
  }}
>
  \${items.map((t, i) => (
    <div key="\${i}">\${t}</div>
  ))}
</div>
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
In other words:

The element should not move when the page scrolls
The scrollbar inside the element should scroll normally
The element must always stay in the same spot on the screen

This is exactly what position: fixed does.

Solution: Use position: "fixed" on the scroll container

<div
  style=\{{
    position: "fixed",
    top: "20px",
    right: "20px",
    width: "300px",
    height: "400px",
    background: "#222",
    overflowY: "auto",
    color: "white",
    padding: "10px",
    borderRadius: "8px",
  }}
>
  \${items.map((t, i) => (
    <div key="\${i}">\${t}</div>
  ))}
</div>
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not
In other words:

The element should not move when the page scrolls
The scrollbar inside the element should scroll normally
The element must always stay in the same spot on the screen

This is exactly what position: fixed does.

Solution: Use position: "fixed" on the scroll container

<div
  style=\{{
    position: "fixed",
    top: "20px",
    right: "20px",
    width: "300px",
    height: "400px",
    background: "#222",
    overflowY: "auto",
    color: "white",
    padding: "10px",
    borderRadius: "8px",
  }}
>
  \${items.map((t, i) => (
    <div key="\${i}">\${t}</div>
  ))}
</div>
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not
In other words:

The element should not move when the page scrolls
The scrollbar inside the element should scroll normally
The element must always stay in the same spot on the screen

This is exactly what position: fixed does.

Solution: Use position: "fixed" on the scroll container

<div
  style=\{{
    position: "fixed",
    top: "20px",
    right: "20px",
    width: "300px",
    height: "400px",
    background: "#222",
    overflowY: "auto",
    color: "white",
    padding: "10px",
    borderRadius: "8px",
  }}
>
  \${items.map((t, i) => (
    <div key="\${i}">\${t}</div>
  ))}
</div>
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not move when the page scrolls The scrollbar inside the element should scroll normally The element must always stay in the same spot on the screen This is exactly what position: fixed does. ✅ Solution: Use position
let random_text=Ah okay — you want a scrollable box, and its scrollbar should stay fixed on the screen even when the page outside is scrolled. In other words: The element should not
...
`;


export default Chat;