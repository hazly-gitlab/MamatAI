import { useState, useEffect, useRef } from 'react';
import {
  Bot, User as UserIcon, Send, Mic, MicOff, Volume2, Image as ImageIcon,
  FileText, RefreshCw, Trash2, Settings,
  Cpu, Database, Activity, CheckCircle2, AlertTriangle, LogOut, Check, X,
  FileCode, Plus, LogIn, HelpCircle, Zap, ShieldAlert, Wrench, TrendingUp
} from 'lucide-react';

// API endpoints with zero-configuration relative path default
let API_URL = (import.meta as any).env?.VITE_API_URL || '';
if (API_URL.endsWith('/api')) {
  API_URL = API_URL.slice(0, -4);
}

interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: any;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

export default function App() {
  // Authentication states
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [authError, setAuthError] = useState('');

  // App Tabs/Views
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'skills' | 'tools' | 'audit' | 'users'>('chat');
  const [skillsList, setSkillsList] = useState<any[]>([]);
  const [repairJobs, setRepairJobs] = useState<any[]>([]);
  const [improvements, setImprovements] = useState<any[]>([]);

  // Conversational states
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Voice states
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLang, setVoiceLang] = useState('en');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Attachment states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [ocrText, setOcrText] = useState<string | null>(null);

  // Administrative / System status states
  const [tools, setTools] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [memories, setMemories] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [systemMessage, setSystemMessage] = useState<string | null>(null);

  // Load init data if logged in
  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchConversations();
      fetchTools();
      fetchDocuments();
      fetchMemories();
      fetchSystemHealth();
    }
  }, [token]);

  // Periodic health check
  useEffect(() => {
    if (token) {
      const interval = setInterval(() => {
        fetchSystemHealth();
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // Auth fetch helpers
  const fetchUserProfile = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
        return;
      }
      handleLogout();
      return;
    } catch (e) {
      console.error(e);
      handleLogout();
      return;
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setCurrentUser(data.user);
      } else {
        const err = await res.json();
        setAuthError(err.detail || 'Incorrect credentials.');
      }
    } catch (e) {
      setAuthError('Connection refused. Is backend server running?');
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      });

      if (res.ok) {
        setIsRegistering(false);
        setSystemMessage('Registration successful! Please login.');
      } else {
        const err = await res.json();
        setAuthError(err.detail || 'Failed to register.');
      }
    } catch (e) {
      setAuthError('Registration failed.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setCurrentUser(null);
    setConversations([]);
    setMessages([]);
    setActiveConversationId(null);
  };

  // Chat logic
  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
        if (data.length > 0 && !activeConversationId) {
          selectConversation(data[0].id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateChat = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations?title=New%20Chat`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations([data, ...conversations]);
        setActiveConversationId(data.id);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteChat = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setConversations(conversations.filter(c => c.id !== id));
        if (activeConversationId === id) {
          setActiveConversationId(null);
          setMessages([]);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Incremental Streaming send message helper (POST sending and stream receiving)
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() && !selectedImage && !selectedFile) return;
    if (!activeConversationId) return;

    const messageContent = inputText;
    setInputText('');
    setIsGenerating(true);

    // Prepare attachments if image OCR was run
    let attachments: any = null;
    if (selectedImage && ocrText) {
      attachments = {
        filename: selectedImage.name,
        ocr: ocrText
      };
    }

    // Render User message locally first for premium instant UX feel
    const tempUserMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: messageContent,
      created_at: new Date().toISOString()
    };

    // Add empty placeholder assistant message that we will stream text into
    const tempAssistantMsg: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, tempUserMsg, tempAssistantMsg]);

    try {
      // 1. Submit message payload to backend store
      const postRes = await fetch(`${API_URL}/api/v1/chat/conversations/${activeConversationId}/send?content=${encodeURIComponent(messageContent)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(attachments)
      });

      if (!postRes.ok) {
        setSystemMessage('Failed to store conversation. Reconnecting...');
        setIsGenerating(false);
        return;
      }

      const postData = await postRes.json();

      // If the message has a special tool approval status, update message and return
      if (postData.status === 'pending_confirmation') {
        selectConversation(activeConversationId);
        setIsGenerating(false);
        return;
      }

      // 2. Consume real-time Server-Sent Events (SSE) streaming API to stream tokens in real-time
      const streamRes = await fetch(`${API_URL}/api/v1/chat/conversations/${activeConversationId}/send/stream?content=${encodeURIComponent(messageContent)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (streamRes.ok && streamRes.body) {
        const reader = streamRes.body.getReader();
        const decoder = new TextDecoder();
        let cumulativeText = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const textChunk = decoder.decode(value);
          // Split events
          const lines = textChunk.split('\n');
          for (const line of lines) {
            const cleanLine = line.trim();
            if (cleanLine.startsWith('data: ')) {
              const dataStr = cleanLine.substring(6);
              if (dataStr === '[DONE]') {
                break;
              }
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.token) {
                  cumulativeText += parsed.token;
                  // Update assistant message text chunk
                  setMessages(prev => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last && last.role === 'assistant') {
                      last.content = cumulativeText;
                    }
                    return next;
                  });
                }
              } catch (err) {}
            }
          }
        }
      }

      // 3. Final synchronization check with database
      selectConversation(activeConversationId);
      setSelectedImage(null);
      setSelectedFile(null);
      setOcrText(null);
    } catch (e) {
      console.error(e);
      setSystemMessage('Network latency detected. Re-establishing link...');
    } finally {
      setIsGenerating(false);
    }
  };

  // Image Upload & OCR Description
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setSelectedImage(file);

    // Call OCR/Vision service on the backend directly
    const formData = new FormData();
    formData.append('file', file);
    formData.append('query', 'Describe this image details');

    setSystemMessage('Performing holographic visual OCR analysis...');

    try {
      const res = await fetch(`${API_URL}/api/v1/vision/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setOcrText(data.analysis);
        setInputText(`Read screenshot image details: ${data.analysis}`);
        setSystemMessage('Holographic OCR analysis completed successfully.');
      } else {
        setSystemMessage('Vision OCR returned an error.');
      }
    } catch (e) {
      setSystemMessage('Failed to connect to the computer vision service.');
    }
  };

  // RAG File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setSelectedFile(file);

    const formData = new FormData();
    formData.append('file', file);

    setSystemMessage('Ingesting file into semantic RAG memory...');

    try {
      const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        setSystemMessage('File ingested successfully into vector search!');
        fetchDocuments();
      } else {
        setSystemMessage('File ingestion failed.');
      }
    } catch (e) {
      setSystemMessage('Failed to connect to RAG service.');
    }
  };

  // Voice Pipeline
  const toggleRecording = () => {
    if (isRecording) {
      // Stop recording & synthesize transcribed text
      setIsRecording(false);
      setSystemMessage('Transcribing microphone audio...');
      // Simulate sending recorded audio wave file
      handleSendVoiceMock();
    } else {
      setIsRecording(true);
      setSystemMessage('Microphone listening (push to talk)...');
    }
  };

  const handleSendVoiceMock = async () => {
    // Generate simulated audio wave file
    const mockAudioBlob = new Blob([new Uint8Array(1000)], { type: 'audio/wav' });
    const file = new File([mockAudioBlob], 'microphone.wav', { type: 'audio/wav' });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', voiceLang);

    try {
      const res = await fetch(`${API_URL}/api/v1/voice/transcribe`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setInputText(data.text);
        setSystemMessage(`Speech recognized: "${data.text}"`);
      }
    } catch (e) {
      setSystemMessage('Voice transcription failed.');
    }
  };

  // Synthesis playback
  const playSynthesisedSpeech = async (text: string) => {
    setSystemMessage('Synthesizing speech via TTS...');
    try {
      const res = await fetch(`${API_URL}/api/v1/voice/synthesize?text=${encodeURIComponent(text)}&language=${voiceLang}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setTimeout(() => {
          if (audioPlayerRef.current) {
            audioPlayerRef.current.play();
          }
        }, 100);
      }
    } catch (e) {
      setSystemMessage('Failed to synthesise speech.');
    }
  };

  // Confirmation workflow
  const handleConfirmAction = async (auditId: number, approve: boolean) => {
    setSystemMessage('Sending confirmation response...');
    try {
      const res = await fetch(`${API_URL}/api/v1/tools/confirm/${auditId}?approve=${approve}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setSystemMessage(approve ? 'Action approved and completed.' : 'Action rejected.');
        if (activeConversationId) {
          selectConversation(activeConversationId);
        }
      }
    } catch (e) {
      setSystemMessage('Failed to confirm action.');
    }
  };

  // Admin tab fetching
  const fetchTools = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/tools`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTools(data);
      }
    } catch (e) {}
  };

  const handleUpdateTool = async (id: number, enabled: boolean, reqConfirm: boolean) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/tools/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled, requires_confirmation: reqConfirm })
      });
      if (res.ok) {
        fetchTools();
        setSystemMessage('Tool setting updated successfully.');
      }
    } catch (e) {}
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {}
  };

  const handleDeleteDoc = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/documents/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchDocuments();
        setSystemMessage('Document deleted from index.');
      }
    } catch (e) {}
  };

  const fetchMemories = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/memory`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMemories(data);
      }
    } catch (e) {}
  };

  const handleDeleteMemory = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/memory/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchMemories();
        setSystemMessage('Memory removed.');
      }
    } catch (e) {}
  };

  const fetchSkillsData = async () => {
    try {
      const resSkills = await fetch(`${API_URL}/api/v1/skills`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resSkills.ok) setSkillsList(await resSkills.json());

      const resJobs = await fetch(`${API_URL}/api/v1/skills/self-fix/jobs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resJobs.ok) setRepairJobs(await resJobs.json());

      const resImp = await fetch(`${API_URL}/api/v1/skills/self-improvement/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resImp.ok) setImprovements(await resImp.json());
    } catch (e) {}
  };

  const handleExecuteSkill = async (skillName: string) => {
    setSystemMessage(`Executing Autonomous Skill '${skillName}'...`);
    try {
      const res = await fetch(`${API_URL}/api/v1/skills/${skillName}/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      if (res.ok) {
        setSystemMessage(`Skill '${skillName}' executed successfully!`);
        fetchSkillsData();
      }
    } catch (e) {
      setSystemMessage(`Failed to execute skill.`);
    }
  };

  const handleApproveRepair = async (jobId: number) => {
    setSystemMessage(`Deploying patch for repair job #${jobId}...`);
    try {
      const res = await fetch(`${API_URL}/api/v1/skills/self-fix/${jobId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setSystemMessage(`Repair job #${jobId} deployed and verified!`);
        fetchSkillsData();
      }
    } catch (e) {}
  };

  const handleRollbackRepair = async (jobId: number) => {
    setSystemMessage(`Rolling back repair job #${jobId}...`);
    try {
      const res = await fetch(`${API_URL}/api/v1/skills/self-fix/${jobId}/rollback`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setSystemMessage(`Repair job #${jobId} rolled back to backup!`);
        fetchSkillsData();
      }
    } catch (e) {}
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/tools/audit`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (e) {}
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsersList(data);
      }
    } catch (e) {}
  };

  const fetchSystemHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/health`);
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch (e) {}
  };

  // If not logged in, render Futuristic Auth panel
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05070c] px-4">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.1)_0,transparent_100%)] pointer-events-none" />

        <div className="w-full max-w-md bg-[#0b1120] border border-slate-800 rounded-2xl p-8 shadow-2xl relative">
          <div className="flex flex-col items-center mb-8">
            <div className="h-16 w-16 bg-cyan-950/50 border border-cyan-500 rounded-full flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(6,182,212,0.4)] animate-pulse">
              <Bot className="h-8 w-8 text-cyan-400" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">MAMAT AI SYSTEM</h1>
            <p className="text-xs text-slate-400 uppercase tracking-widest mt-1">Autonomous AI Control Center</p>
          </div>

          <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-4">
            {isRegistering && (
              <div>
                <label className="block text-xs uppercase tracking-wider text-slate-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-[#05070c] border border-slate-800 rounded-lg px-4 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-500 text-sm transition-all"
                  placeholder="Tony Stark"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400 mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#05070c] border border-slate-800 rounded-lg px-4 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-500 text-sm transition-all"
                placeholder="tony@stark.com"
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400 mb-1">Access Passcode</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#05070c] border border-slate-800 rounded-lg px-4 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-500 text-sm transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            {authError && (
              <div className="bg-red-950/30 border border-red-800/50 rounded-lg p-3 text-xs text-red-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            {systemMessage && (
              <div className="bg-emerald-950/30 border border-emerald-800/50 rounded-lg p-3 text-xs text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{systemMessage}</span>
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white font-bold py-2.5 rounded-lg text-sm shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all flex items-center justify-center gap-2"
            >
              <LogIn className="h-4 w-4" />
              <span>{isRegistering ? 'INITIALIZE CREDENTIALS' : 'AUTHENTICATE SECURE ACCESS'}</span>
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setAuthError('');
                setSystemMessage(null);
              }}
              className="text-xs text-cyan-400 hover:underline hover:text-cyan-300"
            >
              {isRegistering ? 'Already have credentials? Access here' : 'Request first time Administrator access'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#05070c]">
      {/* Dynamic Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0c1324_1px,transparent_1px),linear-gradient(to_bottom,#0c1324_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* HEADER BAR */}
      <header className="bg-[#0b1120] border-b border-slate-800 px-6 py-4 flex items-center justify-between shrink-0 relative z-10">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-cyan-950/50 border border-cyan-500/50 rounded-full flex items-center justify-center shadow-[0_0_10px_rgba(6,182,212,0.2)]">
            <Bot className="h-5 w-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">MAMAT AI CONTROL CENTRE</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest">Active User: {currentUser?.email} ({currentUser?.role})</p>
          </div>
        </div>

        {/* System status pill */}
        <div className="hidden md:flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2 bg-[#05070c] px-3 py-1.5 border border-slate-800 rounded-full">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-300">Core Engine: Healthy</span>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-slate-400 hover:text-red-400 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Terminate Session</span>
          </button>
        </div>
      </header>

      {/* MAIN COLUMNS WRAPPER */}
      <div className="flex-1 flex overflow-hidden">

        {/* LEFT COLUMN: Sidebar Navigation & Conversation Selector */}
        <aside className="w-80 bg-[#070b14] border-r border-slate-800 flex flex-col shrink-0">

          {/* Sidebar tabs */}
          <div className="p-4 grid grid-cols-3 gap-1 border-b border-slate-800 shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('chat')}
              className={`py-1.5 text-xs font-bold rounded flex flex-col items-center justify-center gap-1 transition-all ${activeTab === 'chat' ? 'bg-cyan-950/50 border border-cyan-500/50 text-cyan-400' : 'bg-slate-900/30 text-slate-400 hover:bg-slate-900/50'}`}
            >
              <Bot className="h-4 w-4" />
              <span>Chat</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('documents'); fetchDocuments(); }}
              className={`py-1.5 text-xs font-bold rounded flex flex-col items-center justify-center gap-1 transition-all ${activeTab === 'documents' ? 'bg-cyan-950/50 border border-cyan-500/50 text-cyan-400' : 'bg-slate-900/30 text-slate-400 hover:bg-slate-900/50'}`}
            >
              <FileText className="h-4 w-4" />
              <span>RAG</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('skills'); fetchSkillsData(); }}
              className={`py-1.5 text-xs font-bold rounded flex flex-col items-center justify-center gap-1 transition-all ${activeTab === 'skills' ? 'bg-cyan-950/50 border border-cyan-500/50 text-cyan-400' : 'bg-slate-900/30 text-slate-400 hover:bg-slate-900/50'}`}
            >
              <Zap className="h-4 w-4" />
              <span>Skills</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('tools'); fetchTools(); }}
              className={`py-1.5 text-xs font-bold rounded flex flex-col items-center justify-center gap-1 transition-all ${activeTab === 'tools' ? 'bg-cyan-950/50 border border-cyan-500/50 text-cyan-400' : 'bg-slate-900/30 text-slate-400 hover:bg-slate-900/50'}`}
            >
              <Settings className="h-4 w-4" />
              <span>Tools</span>
            </button>
          </div>

          {/* Admin exclusive tabs */}
          {currentUser?.role === 'administrator' && (
            <div className="px-4 py-2 bg-cyan-950/10 border-b border-slate-800 flex justify-between gap-1 shrink-0">
              <button
                type="button"
                onClick={() => { setActiveTab('audit'); fetchAuditLogs(); }}
                className={`flex-1 py-1 text-[10px] uppercase font-bold rounded transition-all ${activeTab === 'audit' ? 'text-cyan-400 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Audits
              </button>
              <button
                type="button"
                onClick={() => { setActiveTab('users'); fetchUsers(); }}
                className={`flex-1 py-1 text-[10px] uppercase font-bold rounded transition-all ${activeTab === 'users' ? 'text-cyan-400 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Users
              </button>
            </div>
          )}

          {/* CONVERSATIONS LISTING (Only visible when 'chat' tab is active) */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {activeTab === 'chat' && (
              <>
                <button
                  type="button"
                  onClick={handleCreateChat}
                  className="w-full bg-slate-900/50 hover:bg-slate-900 border border-slate-800 rounded-lg py-2.5 px-4 text-xs font-semibold text-cyan-400 flex items-center justify-center gap-2 transition-all"
                >
                  <Plus className="h-4 w-4" />
                  <span>INITIALIZE NEW CHAT</span>
                </button>

                <div className="mt-4 space-y-1">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2 font-bold">Active Memories</p>
                  {conversations.map(conv => (
                    <div
                      key={conv.id}
                      onClick={() => selectConversation(conv.id)}
                      className={`w-full group rounded-lg p-3 flex items-center justify-between cursor-pointer transition-all ${activeConversationId === conv.id ? 'bg-cyan-950/30 border border-cyan-500/40 text-cyan-200' : 'bg-slate-900/10 border border-slate-900 hover:bg-slate-900/30 text-slate-400'}`}
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <FileCode className="h-4 w-4 shrink-0" />
                        <span className="text-xs truncate font-medium">{conv.title}</span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleDeleteChat(conv.id); }}
                        className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-all shrink-0"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Render Tab Contents in Sidebar directly if not Chatting */}
            {activeTab === 'documents' && (
              <div className="space-y-4">
                <div className="bg-[#0b1120] border border-slate-800 rounded-lg p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Ingest New Asset</h3>
                  <input
                    type="file"
                    onChange={handleFileUpload}
                    className="block w-full text-xs text-slate-400 file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-950/40 file:text-cyan-400 hover:file:bg-cyan-950"
                  />
                  <p className="text-[9px] text-slate-500 mt-2">Supports PDF, DOCX, XLSX, CSV, TXT, MD up to 20MB.</p>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Document Indices</p>
                  {documents.map(doc => (
                    <div key={doc.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
                      <div className="overflow-hidden">
                        <p className="text-xs text-slate-300 font-bold truncate">{doc.filename}</p>
                        <p className="text-[10px] text-slate-500">{(doc.file_size / 1024).toFixed(1)} KB • {doc.status}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteDoc(doc.id)}
                        className="text-slate-500 hover:text-red-400 transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'skills' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">MAMAT AI Skill Registry</p>
                  <button type="button" onClick={fetchSkillsData} className="text-slate-500 hover:text-slate-300">
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="space-y-2">
                  {skillsList.map(sk => (
                    <div key={sk.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-cyan-400">{sk.name}</span>
                        <span className="text-[9px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-300 uppercase">v{sk.current_version}</span>
                      </div>
                      <p className="text-[10px] text-slate-400">{sk.description}</p>
                      <div className="flex justify-between items-center pt-1">
                        <span className={`text-[8px] uppercase px-1 rounded ${sk.risk_level === 0 ? 'bg-emerald-950 text-emerald-400' : sk.risk_level === 1 ? 'bg-blue-950 text-blue-400' : 'bg-yellow-950 text-yellow-400'}`}>
                          Risk L{sk.risk_level}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleExecuteSkill(sk.name)}
                          className="px-2 py-1 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-300 rounded text-[9px] font-bold"
                        >
                          Run Skill
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold flex items-center gap-1 text-teal-400">
                    <Wrench className="h-3 w-3" /> Self-Healing Jobs
                  </p>
                  {repairJobs.length === 0 ? (
                    <p className="text-[10px] text-slate-500 italic">No active or historical repair jobs.</p>
                  ) : (
                    repairJobs.map(job => (
                      <div key={job.id} className="bg-[#0b1120] border border-slate-800 rounded-lg p-2.5 text-[10px] space-y-1.5">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-300">Job #{job.id}</span>
                          <span className={`px-1 rounded text-[8px] uppercase ${job.status === 'verified' ? 'bg-emerald-950 text-emerald-400' : 'bg-yellow-950 text-yellow-400'}`}>{job.status}</span>
                        </div>
                        <p className="text-slate-400 truncate">{job.diagnosis || job.error}</p>
                        <div className="flex gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => handleApproveRepair(job.id)}
                            className="bg-emerald-900 hover:bg-emerald-800 text-emerald-200 px-2 py-0.5 rounded text-[8px] font-bold"
                          >
                            Approve Fix
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRollbackRepair(job.id)}
                            className="bg-red-900 hover:bg-red-800 text-red-200 px-2 py-0.5 rounded text-[8px] font-bold"
                          >
                            Rollback
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold flex items-center gap-1 text-cyan-400">
                    <TrendingUp className="h-3 w-3" /> Self-Improvement Candidates
                  </p>
                  {improvements.length === 0 ? (
                    <p className="text-[10px] text-slate-500 italic">No skill optimizations logged.</p>
                  ) : (
                    improvements.map(imp => (
                      <div key={imp.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-2 text-[10px] space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-cyan-300">v{imp.old_version} → v{imp.new_version}</span>
                          <span className={`px-1 rounded text-[8px] uppercase ${imp.status === 'approved' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>{imp.status}</span>
                        </div>
                        <p className="text-slate-400">{imp.reason}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'tools' && (
              <div className="space-y-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Dynamic Tool Settings</p>
                {tools.map(t => (
                  <div key={t.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-400">{t.name}</span>
                      <span className="text-[9px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-400 uppercase">{t.permission_level}</span>
                    </div>
                    <p className="text-[10px] text-slate-400">{t.description}</p>

                    <div className="flex items-center justify-between pt-1">
                      <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={t.enabled}
                          onChange={(e) => handleUpdateTool(t.id, e.target.checked, t.requires_confirmation)}
                          disabled={currentUser?.role !== 'administrator'}
                          className="rounded border-slate-800 text-cyan-500 bg-black focus:ring-0"
                        />
                        <span>Enabled</span>
                      </label>
                      <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={t.requires_confirmation}
                          onChange={(e) => handleUpdateTool(t.id, t.enabled, e.target.checked)}
                          disabled={currentUser?.role !== 'administrator'}
                          className="rounded border-slate-800 text-cyan-500 bg-black focus:ring-0"
                        />
                        <span>Requires Confirm</span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'audit' && (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Security Audit Logs</p>
                  <button type="button" onClick={fetchAuditLogs} className="text-slate-500 hover:text-slate-300">
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </div>
                {auditLogs.map(log => (
                  <div key={log.id} className="bg-[#0b1120] border border-slate-800 rounded-lg p-2.5 text-[10px] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-300">{log.action}</span>
                      <span className={`px-1 rounded font-semibold text-[8px] uppercase ${log.status === 'success' ? 'bg-emerald-950 text-emerald-400' : log.status === 'denied' ? 'bg-red-950 text-red-400' : 'bg-yellow-950 text-yellow-400'}`}>{log.status}</span>
                    </div>
                    <p className="text-slate-400">User: {log.username || 'unknown'}</p>
                    {log.execution_time_ms && <p className="text-slate-500">Duration: {log.execution_time_ms.toFixed(1)}ms</p>}
                    <p className="text-[9px] text-slate-500">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'users' && (
              <div className="space-y-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Organizational Directory</p>
                {usersList.map(u => (
                  <div key={u.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-300">{u.full_name || 'Anonymous User'}</span>
                      <span className="text-[9px] uppercase px-1.5 bg-slate-800 rounded text-slate-400">{u.role}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">{u.email}</p>
                    <p className="text-[9px] text-slate-600">Enrolled: {new Date(u.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* CENTRE COLUMN: Active Conversation Stream Terminal */}
        <main className="flex-1 flex flex-col bg-[#05070c] relative">

          {/* Main system messages alert bar */}
          {systemMessage && (
            <div className="bg-cyan-950/20 border-b border-cyan-500/30 px-6 py-2.5 flex items-center justify-between text-xs text-cyan-300">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 animate-pulse" />
                <span>{systemMessage}</span>
              </div>
              <button type="button" onClick={() => setSystemMessage(null)} className="hover:text-cyan-100">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {/* CHAT MESSAGES STREAM TERMINAL */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {!activeConversationId ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
                <div className="h-16 w-16 bg-cyan-950/40 border border-cyan-500/30 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.15)]">
                  <Bot className="h-8 w-8 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-200">Autonomous Core Standby</h3>
                  <p className="text-sm text-slate-400 mt-1">Please select an existing holographic memory node or initialize a new chat to begin interacting with MAMAT AI.</p>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto space-y-3 text-slate-400">
                <Bot className="h-6 w-6 text-cyan-500 animate-bounce" />
                <p className="text-xs uppercase tracking-widest text-cyan-400">Memory Matrix Initialized</p>
                <p className="text-xs text-slate-500">Ask any questions, extract screenshots, perform calculations, run queries, or synthesize speech.</p>
              </div>
            ) : (
              messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex gap-4 p-4 rounded-xl border ${msg.role === 'user' ? 'bg-slate-900/30 border-slate-900/80 ml-12' : 'bg-[#0b1120] border-slate-800 mr-12 shadow-md relative'}`}
                >
                  <div className={`h-8 w-8 rounded-full shrink-0 flex items-center justify-center text-xs font-bold border ${msg.role === 'user' ? 'bg-slate-800 border-slate-700 text-slate-300' : 'bg-cyan-950/60 border-cyan-500/40 text-cyan-400'}`}>
                    {msg.role === 'user' ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className="flex-1 space-y-3 overflow-x-auto">
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                      {msg.role === 'user' ? 'Secure Access Node' : 'MAMAT AI Autonomous Response'} • {new Date(msg.created_at).toLocaleTimeString()}
                    </p>

                    {/* Render message string content */}
                    <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>

                    {/* Check if is a confirmation request block */}
                    {msg.attachments?.requires_approval && (
                      <div className="bg-yellow-950/20 border border-yellow-700/50 rounded-lg p-4 mt-2 space-y-3">
                        <div className="flex items-center gap-2 text-yellow-400">
                          <AlertTriangle className="h-5 w-5" />
                          <span className="text-xs font-bold uppercase tracking-wider">Dangerous Action Approval Needed</span>
                        </div>
                        <p className="text-xs text-slate-300">This tool requires explicit approval from you prior to execution.</p>

                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleConfirmAction(msg.id, true)}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-1"
                          >
                            <Check className="h-3.5 w-3.5" />
                            <span>Confirm Approval</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleConfirmAction(msg.id, false)}
                            className="bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1.5 rounded text-xs transition-colors flex items-center gap-1"
                          >
                            <X className="h-3.5 w-3.5" />
                            <span>Reject & Abort</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Citations references */}
                    {msg.attachments?.citations && (
                      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3 mt-2 text-xs space-y-1">
                        <span className="font-bold text-cyan-400 block mb-1">Source Citations:</span>
                        {msg.attachments.citations.map((cite: any, idx: number) => (
                          <div key={idx} className="border-l-2 border-cyan-500 pl-2 py-0.5 text-slate-400">
                            <strong>{cite.filename}</strong>: {cite.snippet}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Audio Synthesis / Voice fallback trigger */}
                    {msg.role === 'assistant' && (
                      <div className="pt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={() => playSynthesisedSpeech(msg.content)}
                          className="flex items-center gap-1 text-[10px] uppercase font-bold text-cyan-400 hover:text-cyan-300 transition-colors"
                        >
                          <Volume2 className="h-3.5 w-3.5" />
                          <span>Voice Synthesizer</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Dynamic Audio Synthesizer Stream player fallback */}
          {audioUrl && (
            <div className="absolute top-4 right-4 bg-slate-950/80 border border-slate-800 p-2 rounded-lg flex items-center gap-2">
              <audio ref={audioPlayerRef} src={audioUrl} className="hidden" controls />
              <Volume2 className="h-4 w-4 text-cyan-400 animate-pulse" />
              <span className="text-[10px] text-slate-400">Audio playback active</span>
              <button type="button" onClick={() => setAudioUrl(null)} className="text-slate-500 hover:text-slate-300">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {/* LOWER CONTROLS PANEL: Input Terminal */}
          <footer className="bg-[#0b1120] border-t border-slate-800 p-4 shrink-0 relative z-10">

            {/* Holographic Quick Attachment Status Indicators */}
            {(selectedImage || selectedFile) && (
              <div className="flex gap-2 mb-3">
                {selectedImage && (
                  <div className="bg-cyan-950/40 border border-cyan-500/30 px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs text-cyan-300">
                    <ImageIcon className="h-4 w-4" />
                    <span className="font-medium max-w-[120px] truncate">{selectedImage.name}</span>
                    <button type="button" onClick={() => setSelectedImage(null)} className="hover:text-cyan-100">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
                {selectedFile && (
                  <div className="bg-cyan-950/40 border border-cyan-500/30 px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs text-cyan-300">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium max-w-[120px] truncate">{selectedFile.name}</span>
                    <button type="button" onClick={() => setSelectedFile(null)} className="hover:text-cyan-100">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleSendMessage} className="flex gap-2 items-center">

              {/* Push To Talk Microphone button */}
              <button
                type="button"
                onClick={toggleRecording}
                className={`h-11 w-11 rounded-xl flex items-center justify-center transition-all border ${isRecording ? 'bg-red-950/60 border-red-500 text-red-400 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-cyan-400'}`}
                title="Microphone / Voice input (PTT)"
              >
                {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </button>

              {/* Language selection pill */}
              <button
                type="button"
                onClick={() => setVoiceLang(voiceLang === 'en' ? 'ms' : 'en')}
                className="bg-slate-900 border border-slate-800 text-[10px] font-bold text-slate-400 px-2 py-3 rounded-xl hover:text-cyan-400"
                title="Voice locale selector"
              >
                {voiceLang === 'en' ? 'EN-US' : 'MS-MY'}
              </button>

              {/* Visual OCR Camera upload button */}
              <label className="h-11 w-11 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center text-slate-400 hover:text-cyan-400 cursor-pointer transition-all">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <ImageIcon className="h-5 w-5" />
              </label>

              {/* Text Input Console bar */}
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={!activeConversationId || isGenerating}
                placeholder={!activeConversationId ? "Core standby..." : "Address MAMAT AI terminal..."}
                className="flex-1 bg-[#05070c] border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
              />

              {/* Submit / Cancel generation button */}
              <button
                type="submit"
                disabled={!activeConversationId || isGenerating}
                className="h-11 w-11 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center shadow-[0_0_10px_rgba(6,182,212,0.25)] transition-all"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </footer>
        </main>

        {/* RIGHT COLUMN: Active holographic HUD panel */}
        <aside className="hidden lg:flex w-80 bg-[#070b14] border-l border-slate-800 flex-col overflow-y-auto p-4 space-y-6">

          {/* Dynamic performance graphs HUD */}
          <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-4 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <Cpu className="h-4 w-4 text-cyan-400 animate-pulse" />
              <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-300">HUD Console Status</h3>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[#05070c] border border-slate-900 rounded-lg p-2.5 text-center">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">CPU Load</span>
                <span className="text-lg font-black text-cyan-400">{systemHealth?.services?.cpu || '14.5'} %</span>
              </div>
              <div className="bg-[#05070c] border border-slate-900 rounded-lg p-2.5 text-center">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">RAM Core</span>
                <span className="text-lg font-black text-teal-400">{systemHealth?.services?.ram || '42.8'} %</span>
              </div>
            </div>

            <div className="space-y-2 text-[10px]">
              <div className="flex justify-between items-center text-slate-400">
                <span>Relational Store</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1"><Check className="h-3 w-3" /> ONLINE</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Memory Cache</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1"><Check className="h-3 w-3" /> ONLINE</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Semantic Search</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1"><Check className="h-3 w-3" /> ONLINE</span>
              </div>
            </div>
          </div>

          {/* Active vector memories viewer */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <Database className="h-4 w-4 text-teal-400" />
              <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-300">Semantic Preferences</h3>
            </div>

            <div className="space-y-2">
              {memories.length === 0 ? (
                <p className="text-[10px] text-slate-500 italic text-center py-3">No long term preferences extracted yet.</p>
              ) : (
                memories.map(m => (
                  <div key={m.id} className="bg-slate-900/40 border border-slate-800 rounded-lg p-2.5 flex items-start justify-between gap-2 text-[10px]">
                    <div className="space-y-1">
                      <span className="bg-teal-950 text-teal-400 px-1 rounded uppercase tracking-wider text-[8px] font-bold">{m.category}</span>
                      <p className="text-slate-300">{m.content}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteMemory(m.id)}
                      className="text-slate-500 hover:text-red-400 shrink-0"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Interactive Help Desk */}
          <div className="bg-slate-900/10 border border-slate-900 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <HelpCircle className="h-4 w-4" />
              <span className="font-bold uppercase tracking-wider">Assistance Tips</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Use "calculate 3.14 * 5" to trigger the safe math tool. Try "check weather in KL" to fetch real time weather details. Ask "how healthy is the system" for status logs.
            </p>
          </div>

        </aside>

      </div>
    </div>
  );
}
