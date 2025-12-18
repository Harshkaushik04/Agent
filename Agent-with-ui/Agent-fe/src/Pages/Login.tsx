import { useEffect } from "react";
import { useLogin } from "../hooks/useLogin";
import axios from "axios"
import { useHtmlDivRef } from "../hooks/useHtmlDivRef";
import * as CustomTypes from '../types'
function Login() {
  const {username,setUsername,password,setPassword,Navigate}=useLogin()
  const {divRef,getDivRefCurrent}=useHtmlDivRef()
  let err_ref=divRef
  let err_ref_current=getDivRefCurrent()
  async function handleSubmit(e:React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const res=await axios.post<CustomTypes.loginType>("http://localhost:3000/login",{
        username:username,
        password:password
    })
    if(res.data.valid){
        localStorage.setItem("token",res.data.token);
        localStorage.setItem("username",res.data.username);
        localStorage.setItem("model","DeepSeek-R1-Distill-Qwen-7B-Q4_K_M")
        console.log("hi");
        Navigate("/chat");
    }
    else{
        err_ref_current.style.display="block";
    }
  }
  useEffect(()=>{
    err_ref_current.style.display="none";
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
          Login
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

        {/* Login Button */}
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
          Login
        </button>
        <div ref={err_ref} style={{color:"white"}}>Wrong username or password</div>
      </form>
    </div>
  );
}

export default Login;