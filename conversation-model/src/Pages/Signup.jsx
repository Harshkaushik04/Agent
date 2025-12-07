import { useState,useRef, useEffect } from "react";
import axios from "axios"
import { useNavigate } from "react-router-dom";
function Signup() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  let err_ref=useRef();
  let Navigate=useNavigate();
  async function handleSubmit(e) {
    e.preventDefault();
    const res=await axios.post("http://localhost:3000/signup",{
        username:username,
        password:password
    })
    if(!res.data.whetherDuplicate){
        Navigate("/login");
    }
    else{
        err_ref.current.style.display="block";
    }
  }
  useEffect(()=>{
    err_ref.current.style.display="none";
  },[])

  return (
    <div
      style={{
        width: "100%",
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "black",         // BLACK BACKGROUND
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: "320px",
          padding: "24px",
          borderRadius: "12px",
          background: "#111",         // dark container
          boxShadow: "0 2px 12px rgba(255,255,255,0.15)",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          border: "1px solid #222",
        }}
      >
        <h2
          style={{
            textAlign: "center",
            margin: 0,
            color: "white",
            fontWeight: "500",
          }}
        >
          Signup
        </h2>

        {/* Username */}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #333",
            backgroundColor: "#222",
            color: "white",
            fontSize: "15px",
          }}
        />

        {/* Password */}
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #333",
            backgroundColor: "#222",
            color: "white",
            fontSize: "15px",
          }}
        />

        {/* Signup Button */}
        <button
          type="submit"
          style={{
            padding: "10px",
            borderRadius: "6px",
            background: "#4285f4",
            color: "white",
            fontSize: "16px",
            border: "none",
            cursor: "pointer",
            transition: "0.2s",
          }}
        >
          Signup
        </button>
        <div ref={err_ref} style={{color:"white"}}>Duplicate username</div>
      </form>
    </div>
  );
}

export default Signup;