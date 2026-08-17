import React, { useState, useEffect, useRef } from 'react';
import {
  Bot, User, Mic, MicOff, Image, Paperclip, Send, Square,
  Trash2, Shield, Radio, Volume2, Database, AlertTriangle,
  Activity, CloudRain, Clock, Play, FileText, CheckCircle2, RefreshCw, X, LogIn, LogOut
} from 'lucide-react';
import { authService, conversationService, documentService, apiClient } from './services/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Array<{ filename: string; excerpt: string; score: number }>;
  tool_calls?: Array<{ tool_name: string; result: any }>;
  image_url?: string;
  audio_url?: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

interface Document {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
}

interface PendingAction {
  action_id: string;
  tool_name: string;
  args: any;
}

export default function App() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [authUsername, setAuthUsername] = useState('jarvis_admin');
  const [authRole, setAuthRole] = useState('admin');

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const [sysHealth, setSysHealth] = useState<any>({ status: 'healthy', load: '1.24%' });
  const [aiProvider, setAiProvider] = useState('local_mock');
  const [aiModel, setAiModel] = useState('gpt-4o-mini');
  const [latency, setLatency] = useState<number>(120);

  const [streamingContent, setStreamingContent] = useState('');
  const [activeToolName, setActiveToolName] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const chatBottomRef = useRef<HTMLDivElement>(null);
  const sseSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const user = authService.getCurrentUser();
    if (user.token) {
      setCurrentUser(user);
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadConversations();
      loadDocuments();
    }
  }, [currentUser]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, activeToolName]);

  const loadConversations = async () => {
    try {
      const list = await conversationService.list();
      setConversations(list);
      if (list.length > 0 && !activeConversationId) {
        selectConversation(list[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadDocuments = async () => {
    try {
      const list = await documentService.list();
      setDocuments(list);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      try {
        await authService.register(authUsername, `${authUsername}@jarvis.ai`, authRole);
      } catch(err) {}

      const session = await authService.login(authUsername);
      setCurrentUser(session);
    } catch (err) {
      alert('Login failure. Please verify the backend status.');
    }
  };

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    setConversations([]);
    setActiveConversationId(null);
    setMessages([]);
  };

  const selectConversation = async (id: string) => {
    setActiveConversationId(id);
    setPendingAction(null);
    try {
      const msgs = await conversationService.getMessages(id);
      setMessages(msgs);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await conversationService.create(`Chat Session - ${new Date().toLocaleTimeString()}`);
      setConversations(prev => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      setPendingAction(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await conversationService.delete(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await documentService.upload(file);
        loadDocuments();
      } catch (err) {
        alert('File upload failed.');
      }
    }
  };

  const handleDeleteDocument = async (id: number) => {
    try {
      await documentService.delete(id);
      loadDocuments();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStopGeneration = () => {
    if (sseSourceRef.current) {
      sseSourceRef.current.close();
    }
    setIsGenerating(false);
    setActiveToolName(null);
  };

  const handleSubmitPrompt = async (e?: React.FormEvent, directPrompt?: string) => {
    if (e) e.preventDefault();
    const activePrompt = directPrompt || inputPrompt;
    if (!activePrompt.trim() && !uploadedImage) return;

    let cid = activeConversationId;
    if (!cid) {
      try {
        const newConv = await conversationService.create(`Chat Session`);
        setConversations(prev => [newConv, ...prev]);
        cid = newConv.id;
        setActiveConversationId(cid);
      } catch (err) {
        alert('Could not instantiate conversation');
        return;
      }
    }

    setInputPrompt('');
    setStreamingContent('');
    setIsGenerating(true);
    setPendingAction(null);
    setActiveToolName(null);

    const userMsgId = Date.now().toString();
    const newUserMsg: Message = {
      id: userMsgId,
      sender: 'user',
      content: activePrompt,
      image_url: imagePreview || undefined
    };
    setMessages(prev => [...prev, newUserMsg]);

    const formData = new FormData();
    formData.append('prompt', activePrompt);
    if (uploadedImage) {
      formData.append('image', uploadedImage);
    }

    setUploadedImage(null);
    setImagePreview(null);

    const url = `/api/v1/conversations/${cid}/messages/stream`;
    const token = localStorage.getItem('jarvis_token');

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('API status ' + response.status);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              const eventType = line.slice(7).trim();
              const nextLineIndex = lines.indexOf(line) + 1;
              const dataLine = lines[nextLineIndex];
              if (dataLine && dataLine.startsWith('data: ')) {
                const dataRaw = dataLine.slice(6).trim();
                try {
                  const data = JSON.parse(dataRaw);
                  handleSSEEvent(eventType, data);
                } catch (err) {}
              }
            }
          }
        }
      }
    } catch (err: any) {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'system',
        content: `Connection Interrupted: ${err.message || 'JARVIS core API not responding.'}`
      };
      setMessages(prev => [...prev, errMsg]);
      setIsGenerating(false);
    }
  };

  const handleSSEEvent = (event: string, data: any) => {
    switch (event) {
      case 'message_start':
        setIsGenerating(true);
        break;
      case 'message_delta':
        setStreamingContent(prev => prev + data.content);
        break;
      case 'tool_start':
        if (data.requires_confirmation) {
          setPendingAction({
            action_id: data.action_id,
            tool_name: data.tool_name,
            args: data.args
          });
        } else {
          setActiveToolName(data.tool_name);
        }
        break;
      case 'tool_result':
        setActiveToolName(null);
        break;
      case 'message_complete':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          sender: 'assistant',
          content: data.content,
          citations: data.citations
        }]);
        setStreamingContent('');
        setIsGenerating(false);
        setActiveToolName(null);
        if (isSpeaking) {
          playSpeechSynth(data.content);
        }
        break;
      case 'error':
        alert(`Error from JARVIS: ${data.detail}`);
        setIsGenerating(false);
        setActiveToolName(null);
        break;
    }
  };

  const handleConfirmAction = async (approved: boolean) => {
    if (!pendingAction) return;
    const actionId = pendingAction.action_id;
    setPendingAction(null);
    setIsGenerating(true);

    try {
      const res = await conversationService.confirmAction(actionId, approved);
      if (res.status === 'success') {
        const toolMsg: Message = {
          id: Date.now().toString(),
          sender: 'system',
          content: `✓ Action completed: ${pendingAction.tool_name} returned "${res.result}"`
        };
        setMessages(prev => [...prev, toolMsg]);
      } else {
        const rejectMsg: Message = {
          id: Date.now().toString(),
          sender: 'system',
          content: `✗ Action aborted: ${res.message || 'Rejected.'}`
        };
        setMessages(prev => [...prev, rejectMsg]);
      }
    } catch (err: any) {
      alert('Error during action confirmation execution.');
    } finally {
      setIsGenerating(false);
    }
  };

  const playSpeechSynth = async (text: string) => {
    try {
      const response = await apiClient.post('/voice/tts', `text=${encodeURIComponent(text)}`, {
        responseType: 'blob',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      const audioUrl = URL.createObjectURL(response.data);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (err) {
      console.error("TTS failure", err);
    }
  };

  const startVoiceRecording = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Browser voice not supported.");
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = 'ms-MY';
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    setIsRecording(true);

    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setInputPrompt(transcript);
      setIsRecording(false);
    };

    rec.onerror = () => {
      setIsRecording(false);
    };

    rec.onend = () => {
      setIsRecording(false);
    };

    rec.start();
  };

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#060a13] text-[#e2e8f0] px-4 font-sans">
        <div className="w-full max-w-md bg-[#0b0f19] border border-cyan-500/30 rounded-2xl p-8 glow-cyan relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-blue-600"></div>

          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-cyan-950/50 border border-cyan-500 rounded-full mb-4 animate-pulse">
              <Bot className="w-8 h-8 text-cyan-400" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-widest text-cyan-400">JARVIS</h1>
            <p className="text-xs text-slate-400 uppercase mt-1">Enterprise Intelligent Control Centre</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400 mb-2 font-semibold">Security Identifier (Username)</label>
              <input
                type="text"
                value={authUsername}
                onChange={e => setAuthUsername(e.target.value)}
                className="w-full bg-[#111827] border border-slate-700 rounded-lg px-4 py-3 text-[#e2e8f0] focus:outline-none focus:border-cyan-500 text-sm font-medium"
                placeholder="Enter authorized identity..."
                required
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400 mb-2 font-semibold">Clearance Level (Role)</label>
              <select
                value={authRole}
                onChange={e => setAuthRole(e.target.value)}
                className="w-full bg-[#111827] border border-slate-700 rounded-lg px-4 py-3 text-[#e2e8f0] focus:outline-none focus:border-cyan-500 text-sm font-medium"
              >
                <option value="user">Standard User</option>
                <option value="admin">Administrator (Audit, SQL, Health Access)</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full bg-cyan-500 text-black hover:bg-cyan-400 py-3 rounded-lg font-bold transition duration-200 text-sm uppercase tracking-wider flex items-center justify-center gap-2 glow-cyan"
            >
              <LogIn className="w-4 h-4" /> Initialize System
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#060a13] text-[#e2e8f0] overflow-hidden font-sans">
      <aside className="w-80 bg-[#0b0f19] border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div className="p-4 flex flex-col gap-4 overflow-y-auto h-full">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Bot className="w-6 h-6 text-cyan-400 animate-pulse" />
              <span className="font-bold text-lg tracking-widest text-cyan-400 uppercase">JARVIS</span>
            </div>
            <div className="flex items-center gap-1 bg-cyan-950/50 border border-cyan-800 px-2 py-0.5 rounded text-[10px] text-cyan-400 uppercase">
              <Shield className="w-3 h-3" /> {currentUser.role}
            </div>
          </div>

          <button
            onClick={handleNewConversation}
            className="w-full bg-cyan-950/40 hover:bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 rounded-lg py-2.5 font-semibold text-sm transition duration-150 flex items-center justify-center gap-2"
          >
            + New Session
          </button>

          <div className="space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">ACTIVE CONVERSATIONS</span>
            <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
              {conversations.map(c => (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`group flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer transition duration-150 ${activeConversationId === c.id ? 'bg-[#1e293b] text-cyan-400 font-medium' : 'text-slate-400 hover:bg-[#0d1527] hover:text-[#e2e8f0]'}`}
                >
                  <div className="truncate flex-1">{c.title}</div>
                  <button
                    onClick={(e) => handleDeleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 transition-opacity p-0.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-800 pt-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">KNOWLEDGE INGESTION</span>
              <label className="text-[10px] font-semibold text-cyan-400 hover:underline cursor-pointer">
                + Upload
                <input type="file" onChange={handleFileUpload} className="hidden" accept=".pdf,.docx,.xlsx,.csv,.txt" />
              </label>
            </div>

            <div className="max-h-44 overflow-y-auto space-y-2 pr-1">
              {documents.length === 0 ? (
                <div className="text-xs text-slate-500 italic text-center py-2">No documents indexed yet.</div>
              ) : (
                documents.map(d => (
                  <div key={d.id} className="flex items-center justify-between bg-[#0d1527] border border-slate-800 p-2 rounded-lg text-xs">
                    <div className="truncate flex-1 mr-2">
                      <div className="font-semibold text-slate-300 truncate">{d.filename}</div>
                      <div className="text-[10px] text-slate-500 uppercase">{d.file_type} ({(d.file_size / 1024).toFixed(1)} KB)</div>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(d.id)}
                      className="text-slate-500 hover:text-red-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-[#0d1527]">
          <div className="flex items-center gap-2 truncate">
            <div className="w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center font-bold text-sm uppercase tracking-wider text-cyan-400 border border-slate-700">
              {currentUser.username?.[0] || 'U'}
            </div>
            <div className="truncate">
              <div className="text-xs font-semibold text-slate-300 truncate">{currentUser.username}</div>
              <div className="text-[10px] text-slate-500 truncate uppercase">{currentUser.role} LEVEL</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-slate-400 hover:text-red-400 transition p-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col bg-[#060a13] relative overflow-hidden">
        <header className="h-16 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0b0f19]/50 backdrop-blur-sm z-10 shrink-0">
          <div>
            <h2 className="font-bold text-sm tracking-wide">JARVIS DASHBOARD V1.0</h2>
            <p className="text-[10px] text-slate-400 uppercase mt-0.5">End-To-End System Orchestrator</p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 bg-[#0d1527] border border-slate-800 px-3 py-1 rounded-full text-slate-400">
              <Activity className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
              <span>Latency: <strong className="text-slate-200">{latency} ms</strong></span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && !streamingContent && !activeToolName && !pendingAction ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
              <div className="w-16 h-16 bg-cyan-950/30 border border-cyan-500/20 rounded-full flex items-center justify-center text-cyan-400 mb-6 glow-cyan">
                <Bot className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold tracking-wider mb-2">INTELLIGENCE SYSTEM ONLINE</h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-6">
                Welcome. I am fully integrated into database queries, weather models, calculators, and document RAG pipelines.
              </p>
              <div className="grid grid-cols-2 gap-3 w-full">
                <button
                  onClick={() => handleNewConversation()}
                  className="bg-[#0b0f19] hover:bg-[#111827] border border-slate-800 p-4 rounded-xl text-left text-xs transition duration-150"
                >
                  <span className="font-bold text-cyan-400 block mb-1">✓ System Diagnostic</span>
                  Retrieve real-time metrics, system health logs and service statuses.
                </button>
                <button
                  onClick={() => {
                    setInputPrompt("Berapa hasil kiraan 25 * (40 - 2)?");
                  }}
                  className="bg-[#0b0f19] hover:bg-[#111827] border border-slate-800 p-4 rounded-xl text-left text-xs transition duration-150"
                >
                  <span className="font-bold text-cyan-400 block mb-1">✓ Math Evaluation</span>
                  Run formulas safely through isolated non-eval math environments.
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              {messages.map(m => (
                <div key={m.id} className={`flex gap-4 ${m.sender === 'user' ? 'justify-end' : ''}`}>
                  {m.sender !== 'user' && (
                    <div className="w-8 h-8 bg-cyan-950 border border-cyan-500/30 rounded-full flex items-center justify-center text-cyan-400 shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`max-w-[80%] rounded-2xl p-4 border ${m.sender === 'user' ? 'bg-cyan-950/20 border-cyan-500/30 text-slate-200' : 'bg-[#0b0f19] border-slate-800 text-slate-300'}`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</div>

                    {m.image_url && (
                      <div className="mt-3 rounded-lg overflow-hidden border border-slate-800">
                        <img src={m.image_url} alt="Uploaded attachment" className="max-h-48 object-cover w-full" />
                      </div>
                    )}

                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80">
                        <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider mb-2">SOURCES REFERENCE:</div>
                        <div className="space-y-1.5">
                          {m.citations.map((c, i) => (
                            <div key={i} className="text-[11px] text-slate-400 bg-[#0d1527] px-2.5 py-1.5 rounded border border-slate-800">
                              📄 <span className="font-semibold text-slate-300">{c.filename}</span> — Relevansi: {(c.score * 100).toFixed(0)}%
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {m.sender === 'user' && (
                    <div className="w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center font-bold text-xs uppercase text-cyan-400 shrink-0 border border-slate-700">
                      {currentUser.username?.[0] || 'U'}
                    </div>
                  )}
                </div>
              ))}

              {streamingContent && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-cyan-950 border border-cyan-500/30 rounded-full flex items-center justify-center text-cyan-400 shrink-0 animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="max-w-[80%] bg-[#0b0f19] border border-slate-800 rounded-2xl p-4 text-slate-300">
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{streamingContent}</div>
                  </div>
                </div>
              )}

              {activeToolName && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-slate-900 border border-slate-700 rounded-full flex items-center justify-center text-slate-400 shrink-0">
                    <Activity className="w-4 h-4 text-cyan-500 animate-spin" />
                  </div>
                  <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-3 text-xs text-slate-400 flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                    <span>⚙ Menjalankan alat: <strong className="text-slate-200">{activeToolName}</strong>...</span>
                  </div>
                </div>
              )}

              {pendingAction && (
                <div className="bg-red-950/20 border border-red-500/40 rounded-xl p-5 max-w-md mx-auto space-y-4 glow-red">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-sm text-red-400 uppercase tracking-wide">CONFIRMATION REQUIRED</h4>
                      <p className="text-xs text-slate-300 leading-relaxed mt-1">
                        JARVIS is requesting clearance to execute action: <strong className="text-slate-100 font-bold">{pendingAction.tool_name}</strong>.
                      </p>
                    </div>
                  </div>

                  <div className="bg-black/40 border border-red-950 p-3 rounded text-[11px] font-mono text-red-300">
                    Parameters: {JSON.stringify(pendingAction.args)}
                  </div>

                  <div className="flex gap-2 justify-end text-xs">
                    <button
                      onClick={() => handleConfirmAction(false)}
                      className="px-4 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleConfirmAction(true)}
                      className="px-4 py-2 rounded bg-red-500 hover:bg-red-400 text-black font-extrabold transition"
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-4 bg-[#0b0f19]/80 border-t border-slate-800/80 z-10 shrink-0">
          <form onSubmit={(e) => handleSubmitPrompt(e)} className="max-w-3xl mx-auto space-y-3">
            {imagePreview && (
              <div className="inline-flex items-center gap-2 bg-[#111827] border border-slate-800 px-3 py-1.5 rounded-lg text-xs">
                <img src={imagePreview} alt="upload preview" className="w-6 h-6 object-cover rounded" />
                <span className="text-slate-300 truncate max-w-xs">{uploadedImage?.name}</span>
                <button onClick={() => { setImagePreview(null); setUploadedImage(null); }} className="text-slate-500 hover:text-red-400 ml-1">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            <div className="flex items-center gap-2 bg-[#111827] border border-slate-800 rounded-xl px-3 py-2 focus-within:border-cyan-500/50 transition">
              <button
                type="button"
                onClick={startVoiceRecording}
                className={`p-2 rounded-lg transition shrink-0 ${isRecording ? 'bg-red-500 text-black animate-pulse' : 'text-slate-400 hover:text-[#e2e8f0] hover:bg-slate-800'}`}
                title="Speak to JARVIS"
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <label className="p-2 rounded-lg text-slate-400 hover:text-[#e2e8f0] hover:bg-slate-800 cursor-pointer transition shrink-0">
                <Image className="w-5 h-5" />
                <input type="file" onChange={handleImageSelect} className="hidden" accept="image/png,image/jpeg,image/webp" />
              </label>

              <input
                type="text"
                value={inputPrompt}
                onChange={e => setInputPrompt(e.target.value)}
                placeholder="Ask JARVIS (e.g. 'How is the weather today?' or 'Purge storage files')..."
                className="w-full bg-transparent text-sm focus:outline-none text-[#e2e8f0] px-2"
                disabled={isGenerating}
              />

              {isGenerating ? (
                <button
                  type="button"
                  onClick={handleStopGeneration}
                  className="p-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition shrink-0"
                  title="Stop Generating"
                >
                  <Square className="w-5 h-5" />
                </button>
              ) : (
                <button
                  type="submit"
                  className="p-2 bg-cyan-500 text-black hover:bg-cyan-400 rounded-lg transition shrink-0 glow-cyan"
                  title="Send to JARVIS"
                >
                  <Send className="w-5 h-5" />
                </button>
              )}
            </div>

            <div className="flex justify-between items-center text-[10px] text-slate-500 px-1">
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1">
                  <Volume2 className="w-3.5 h-3.5" /> Speak Reply:
                </span>
                <button
                  type="button"
                  onClick={() => setIsSpeaking(!isSpeaking)}
                  className={`px-2 py-0.5 rounded font-bold uppercase transition ${isSpeaking ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-slate-800 text-slate-400'}`}
                >
                  {isSpeaking ? 'ACTIVE' : 'MUTED'}
                </button>
              </div>
              <div>Bilingual Mode: English / Bahasa Melayu</div>
            </div>
          </form>
        </div>
      </main>

      <aside className="w-80 bg-[#0b0f19] border-l border-slate-800 flex flex-col p-4 gap-4 overflow-y-auto shrink-0">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-2">INTELLIGENCE CONFIGURATION</span>
          <div className="space-y-3 bg-[#0d1527] border border-slate-800 p-3 rounded-xl text-xs">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1">AI Provider</label>
              <select
                value={aiProvider}
                onChange={e => setAiProvider(e.target.value)}
                className="w-full bg-[#111827] border border-slate-700 px-2 py-1.5 rounded focus:outline-none focus:border-cyan-500 text-slate-300"
              >
                <option value="local_mock">Local Offline Mock</option>
                <option value="openai">OpenAI Compatible</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1">Model Name</label>
              <input
                type="text"
                value={aiModel}
                onChange={e => setAiModel(e.target.value)}
                className="w-full bg-[#111827] border border-slate-700 px-2 py-1.5 rounded focus:outline-none focus:border-cyan-500 text-slate-300"
              />
            </div>

            <div>
              <span className="block text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-1">Speech Synthesizer (TTS)</span>
              <div className="px-2.5 py-1.5 bg-[#111827] border border-slate-800 text-slate-400 rounded">
                Browser Speech Synth Engine
              </div>
            </div>
          </div>
        </div>

        {currentUser.role === 'admin' && (
          <div className="border-t border-slate-800 pt-4 flex flex-col gap-2">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">SAFE SQL QUERY CONSOLE</span>
            <div className="bg-[#0d1527] border border-slate-800 p-3 rounded-xl text-xs space-y-3">
              <p className="text-[10px] text-slate-400 leading-relaxed">
                Execute SELECT metrics or audit lists directly through the read-only database query tool safely.
              </p>

              <button
                onClick={() => {
                  setInputPrompt("SELECT username, email, role, is_active FROM users LIMIT 5;");
                }}
                className="w-full bg-cyan-950/40 hover:bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 rounded py-1.5 font-semibold transition flex items-center justify-center gap-1.5"
              >
                <Database className="w-3.5 h-3.5" /> Prepare Users Query
              </button>
            </div>
          </div>
        )}

        <div className="border-t border-slate-800 pt-4 flex-1 flex flex-col gap-2">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">REALTIME LOG AUDITING</span>
          <div className="bg-black/50 border border-slate-900 p-3 rounded-xl font-mono text-[9px] text-slate-400 space-y-2 overflow-y-auto flex-1 max-h-48">
            <div>[{new Date().toLocaleTimeString()}] INFO: JARVIS websocket channel established.</div>
            <div>[{new Date().toLocaleTimeString()}] INFO: Connection authorization validated.</div>
            <div>[{new Date().toLocaleTimeString()}] INFO: Vector similarity database status initialized.</div>
            {isGenerating && <div className="text-cyan-400 animate-pulse">[{new Date().toLocaleTimeString()}] DEBUG: Processing neural orchestrator feed...</div>}
          </div>
        </div>
      </aside>
    </div>
  );
}
