import "./../App.css"
import { useNavigate } from "react-router-dom";
function Landing(){
    const Navigate=useNavigate();
    return(<div>
        <div style={{
            width:"100vw",
            height:"15vh",
            display:"flex",
            justifyContent:"end"
        }}>
            <button className="button"
            style={{
                margin:20
            }} onClick={()=>{Navigate("/login")}}>Login</button>
            <button className="button" style={{
                margin:20
            }} onClick={()=>{Navigate("/signup")}}>Sign up</button>
        </div>
        <pre style={{
            color:"white",
            height:"65vh",
            display:"flex",
            flexDirection:"column",
            justifyContent:"center",
            textAlign: "center"
        }}>
                     {`                                                                                                         
                                                                                                                              
                                                                                                                              
                                                                  █                                           █         ███   
  ░███▒                                                    █                                █▒  ▒█            █           █   
 ░█▒ ░█                                                    █                                ██  ██            █           █   
 █▒      ███   █▒██▒  █░ ░█   ███    █▒██▒ ▒███▒  ░███░  █████  ███     ███   █▒██▒         ██░░██  ███    ██▓█   ███     █   
 █      █▓ ▓█  █▓ ▒█  ▓▒ ▒▓  ▓▓ ▒█   ██  █ █▒ ░█  █▒ ▒█    █      █    █▓ ▓█  █▓ ▒█         █▒▓▓▒█ █▓ ▓█  █▓ ▓█  ▓▓ ▒█    █   
 █      █   █  █   █  ▒█ █▒  █   █   █     █▒░        █    █      █    █   █  █   █         █ ██ █ █   █  █   █  █   █    █   
 █      █   █  █   █   █ █   █████   █     ░███▒  ▒████    █      █    █   █  █   █   ███   █ █▓ █ █   █  █   █  █████    █   
 █▒     █   █  █   █   █▓█   █       █        ▒█  █▒  █    █      █    █   █  █   █         █    █ █   █  █   █  █        █   
 ░█▒ ░▓ █▓ ▓█  █   █   ▒█▒   ▓▓  █   █     █░ ▒█  █░ ▓█    █░     █    █▓ ▓█  █   █         █    █ █▓ ▓█  █▓ ▓█  ▓▓  █    █░  
  ▒███▒  ███   █   █   ░█░    ███▒   █     ▒███▒  ▒██▒█    ▒██  █████   ███   █   █         █    █  ███    ██▓█   ███▒    ▒██ 
                                                                                                                              
                                                                                                                              
                                                                                                                                                                                                                             
                    `}                                                                                                   
                                                                                                                       
        </pre>
    </div>)
}

export default Landing;