import {BrowserRouter,Route,Routes} from 'react-router-dom'
import Landing from './Pages/Landing.js'
import Login from './Pages/Login.js'
import Signup from './Pages/Signup.js'
import Chat from './Pages/Chat.js'
import './App.css'
import { ChatContextProvider } from './context/ChatContextProvider.js'
import { LoginContextProvider } from './context/LoginContextProvider.js'
import { SignUpContextProvider } from './context/SignUpContextProvider.js'
import { WebSocketContextProvider } from './context/WebSocketContextProvider.js'

function App() {
  return (
    <div>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing/>}/>
          <Route path="/login" element={<LoginContextProvider><Login/></LoginContextProvider>}/>
          <Route path="/signup" element={<SignUpContextProvider><Signup/></SignUpContextProvider>}/>
          <Route path="/chat" element={<WebSocketContextProvider><ChatContextProvider><Chat/></ChatContextProvider></WebSocketContextProvider>}/>
        </Routes>
      </BrowserRouter>
    </div>
  )
}

export default App
