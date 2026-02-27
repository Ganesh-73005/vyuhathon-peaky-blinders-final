import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'sonner';
import { 
  MessageSquare, LayoutDashboard, TrendingUp, Settings, Menu, X, 
  Mic, MicOff, Send, Paperclip, Volume2, VolumeX, Globe,
  Plus, Package, DollarSign, ShoppingCart, AlertTriangle, Users,
  Star, MapPin, ChevronRight, RefreshCw, FileText, LogOut, User,
  Check, XCircle, Calendar, Sparkles, Upload, Eye, EyeOff
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Language translations
const translations = {
  english: {
    chat: 'Chat',
    dashboard: 'Dashboard',
    insights: 'Insights',
    settings: 'Settings',
    sendMessage: 'Type your message...',
    voiceMode: 'Voice Mode',
    language: 'Language',
    totalSales: 'Total Sales',
    transactions: 'Transactions',
    lowStock: 'Low Stock',
    pendingCredit: 'Pending Credit',
    addSale: 'Add Sale',
    addStock: 'Add Stock',
    addExpense: 'Add Expense',
    competitors: 'Nearby Competitors',
    reviews: 'Reviews Analysis',
    opportunities: 'Opportunities',
    listening: 'Listening...',
    processing: 'Processing...',
    send: 'Send',
    welcome: 'Hello! I am Hisaab, your AI shop accountant. Tell me about your sales, purchases, or ask me anything!',
    itemName: 'Item Name',
    quantity: 'Quantity',
    price: 'Price',
    submit: 'Submit',
    cancel: 'Cancel',
    login: 'Login',
    signup: 'Sign Up',
    email: 'Email',
    password: 'Password',
    shopName: 'Shop Name',
    businessType: 'Business Type',
    selectLocation: 'Select Location on Map',
    confirm: 'Confirm',
    reject: 'Reject',
    festivals: 'Upcoming Festivals',
    stockSuggestions: 'Stock Suggestions',
    uploadPdf: 'Upload Bill/Invoice',
    salesBill: 'Sales Bill',
    stockBill: 'Stock/Purchase Bill'
  },
  tamil: {
    chat: 'அரட்டை',
    dashboard: 'டாஷ்போர்டு',
    insights: 'நுண்ணறிவு',
    settings: 'அமைப்புகள்',
    sendMessage: 'உங்கள் செய்தியை தட்டச்சு செய்யுங்கள்...',
    voiceMode: 'குரல் பயன்முறை',
    language: 'மொழி',
    totalSales: 'மொத்த விற்பனை',
    transactions: 'பரிவர்த்தனைகள்',
    lowStock: 'குறைந்த இருப்பு',
    pendingCredit: 'நிலுவை கடன்',
    addSale: 'விற்பனை சேர்',
    addStock: 'இருப்பு சேர்',
    addExpense: 'செலவு சேர்',
    competitors: 'அருகிலுள்ள போட்டியாளர்கள்',
    reviews: 'மதிப்புரைகள் பகுப்பாய்வு',
    opportunities: 'வாய்ப்புகள்',
    listening: 'கேட்கிறேன்...',
    processing: 'செயலாக்கம்...',
    send: 'அனுப்பு',
    welcome: 'வணக்கம்! நான் ஹிசாப், உங்கள் AI கடை கணக்காளர். விற்பனை, கொள்முதல் சொல்லுங்கள் அல்லது எதையும் கேளுங்கள்!',
    itemName: 'பொருள் பெயர்',
    quantity: 'எண்ணிக்கை',
    price: 'விலை',
    submit: 'சமர்ப்பி',
    cancel: 'ரத்து',
    login: 'உள்நுழை',
    signup: 'பதிவு செய்',
    email: 'மின்னஞ்சல்',
    password: 'கடவுச்சொல்',
    shopName: 'கடை பெயர்',
    businessType: 'வணிக வகை',
    selectLocation: 'வரைபடத்தில் இடத்தை தேர்ந்தெடுக்கவும்',
    confirm: 'உறுதிப்படுத்து',
    reject: 'நிராகரி',
    festivals: 'வரவிருக்கும் திருவிழாக்கள்',
    stockSuggestions: 'இருப்பு பரிந்துரைகள்',
    uploadPdf: 'பில் பதிவேற்றவும்',
    salesBill: 'விற்பனை பில்',
    stockBill: 'கொள்முதல் பில்'
  }
};

const businessTypes = [
  { value: 'kirana', label: 'Kirana Store', labelTa: 'கிரானா கடை' },
  { value: 'bakery', label: 'Bakery', labelTa: 'பேக்கரி' },
  { value: 'hotel', label: 'Hotel/Restaurant', labelTa: 'ஹோட்டல்' },
  { value: 'supermarket', label: 'Supermarket', labelTa: 'சூப்பர் மார்க்கெட்' },
  { value: 'pharmacy', label: 'Pharmacy', labelTa: 'மருந்தகம்' },
  { value: 'vegetable_shop', label: 'Vegetable Shop', labelTa: 'காய்கறி கடை' },
  { value: 'fruit_shop', label: 'Fruit Shop', labelTa: 'பழக்கடை' },
  { value: 'general_store', label: 'General Store', labelTa: 'பொது கடை' },
  { value: 'other', label: 'Other', labelTa: 'மற்றவை' }
];

// Login/Signup Component
function AuthPage({ onLogin, language }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [shopName, setShopName] = useState('');
  const [businessType, setBusinessType] = useState('kirana');
  const [location, setLocation] = useState({ lat: 13.0827, lng: 80.2707, address: 'Chennai, Tamil Nadu' });
  const [loading, setLoading] = useState(false);
  const t = translations[language];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/signup';
      const body = isLogin 
        ? { email, password }
        : { 
            email, 
            password, 
            shop_name: shopName, 
            business_type: businessType,
            latitude: location.lat,
            longitude: location.lng,
            address: location.address,
            city: 'Chennai'
          };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (data.success || data.access_token) {
        localStorage.setItem('hisaab_token', data.access_token);
        localStorage.setItem('hisaab_user', JSON.stringify(data.user));
        onLogin(data.user);
        toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!');
      } else {
        toast.error(data.detail || 'Authentication failed');
      }
    } catch (error) {
      toast.error('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMapClick = () => {
    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            address: 'Current Location'
          });
          toast.success('Location captured!');
        },
        () => toast.error('Could not get location')
      );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-black font-black text-3xl">H</span>
          </div>
          <h1 className="text-3xl font-bold">Hisaab</h1>
          <p className="text-muted-foreground mt-2">
            {language === 'tamil' ? 'உங்கள் AI கடை கணக்காளர்' : 'Your AI Shop Accountant'}
          </p>
        </div>

        {/* Auth Form */}
        <div className="card">
          <div className="flex mb-6">
            <button
              data-testid="login-tab"
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 text-center rounded-lg transition-colors ${
                isLogin ? 'bg-primary text-black font-semibold' : 'text-muted-foreground'
              }`}
            >
              {t.login}
            </button>
            <button
              data-testid="signup-tab"
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 text-center rounded-lg transition-colors ${
                !isLogin ? 'bg-primary text-black font-semibold' : 'text-muted-foreground'
              }`}
            >
              {t.signup}
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">{t.email}</label>
              <input
                data-testid="email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input w-full mt-1"
                placeholder="shop@example.com"
                required
              />
            </div>

            <div>
              <label className="text-sm text-muted-foreground">{t.password}</label>
              <div className="relative">
                <input
                  data-testid="password-input"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input w-full mt-1 pr-10"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {!isLogin && (
              <>
                <div>
                  <label className="text-sm text-muted-foreground">{t.shopName}</label>
                  <input
                    data-testid="shop-name-input"
                    type="text"
                    value={shopName}
                    onChange={(e) => setShopName(e.target.value)}
                    className="input w-full mt-1"
                    placeholder="My Kirana Store"
                    required
                  />
                </div>

                <div>
                  <label className="text-sm text-muted-foreground">{t.businessType}</label>
                  <select
                    data-testid="business-type-select"
                    value={businessType}
                    onChange={(e) => setBusinessType(e.target.value)}
                    className="input w-full mt-1"
                  >
                    {businessTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {language === 'tamil' ? type.labelTa : type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm text-muted-foreground">{t.selectLocation}</label>
                  <button
                    type="button"
                    data-testid="location-btn"
                    onClick={handleMapClick}
                    className="w-full mt-1 p-4 border border-border rounded-xl flex items-center justify-center gap-2 hover:bg-secondary transition-colors"
                  >
                    <MapPin className="w-5 h-5 text-primary" />
                    <span className="text-sm">
                      {location.address || 'Tap to get location'}
                    </span>
                  </button>
                  {location.lat && (
                    <p className="text-xs text-muted-foreground mt-1">
                      📍 {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                    </p>
                  )}
                </div>
              </>
            )}

            <button
              data-testid="auth-submit-btn"
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 disabled:opacity-50"
            >
              {loading ? 'Please wait...' : (isLogin ? t.login : t.signup)}
            </button>
          </form>
        </div>

        {/* Language Toggle */}
        <div className="mt-4 text-center">
          <button
            data-testid="auth-language-toggle"
            onClick={() => {}}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            <Globe className="w-4 h-4 inline mr-1" />
            {language === 'english' ? 'தமிழ்' : 'English'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Confirmation Table Component for Chat
function ConfirmationTable({ data, onConfirm, onReject, language }) {
  const t = translations[language];
  const items = data?.items || [];
  const total = data?.total || items.reduce((sum, i) => sum + (i.quantity * i.unit_price), 0);

  return (
    <div className="bg-card border border-border rounded-xl p-4 my-2 animate-fadeIn">
      <h4 className="font-semibold mb-3 flex items-center gap-2">
        <FileText className="w-4 h-4 text-primary" />
        {data?.type === 'stock_add' ? 'Stock Addition' : 'Transaction'} Summary
      </h4>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2">Item</th>
              <th className="text-right py-2">Qty</th>
              <th className="text-right py-2">Price</th>
              <th className="text-right py-2">Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} className="border-b border-border/50">
                <td className="py-2">{item.item_name}</td>
                <td className="text-right">{item.quantity}</td>
                <td className="text-right">₹{item.unit_price}</td>
                <td className="text-right">₹{item.quantity * item.unit_price}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="font-semibold">
              <td colSpan="3" className="py-2 text-right">Total:</td>
              <td className="text-right text-primary">₹{total}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          data-testid="reject-btn"
          onClick={onReject}
          className="flex-1 py-2 px-4 bg-destructive/20 text-destructive rounded-lg flex items-center justify-center gap-2 hover:bg-destructive/30 transition-colors"
        >
          <XCircle className="w-4 h-4" />
          {t.reject}
        </button>
        <button
          data-testid="confirm-btn"
          onClick={onConfirm}
          className="flex-1 py-2 px-4 bg-primary text-black rounded-lg flex items-center justify-center gap-2 hover:bg-green-400 transition-colors"
        >
          <Check className="w-4 h-4" />
          {t.confirm}
        </button>
      </div>
    </div>
  );
}

// PDF Type Selection Component
function PdfTypeSelector({ onSelect, language }) {
  const t = translations[language];
  
  return (
    <div className="bg-card border border-border rounded-xl p-4 my-2 animate-fadeIn">
      <h4 className="font-semibold mb-3">What type of bill is this?</h4>
      <div className="flex gap-3">
        <button
          data-testid="sales-bill-btn"
          onClick={() => onSelect('sales')}
          className="flex-1 py-3 px-4 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
        >
          <DollarSign className="w-5 h-5 mx-auto mb-1" />
          <span className="text-sm">{t.salesBill}</span>
        </button>
        <button
          data-testid="stock-bill-btn"
          onClick={() => onSelect('stock')}
          className="flex-1 py-3 px-4 bg-blue-500/20 text-blue-500 rounded-lg hover:bg-blue-500/30 transition-colors"
        >
          <Package className="w-5 h-5 mx-auto mb-1" />
          <span className="text-sm">{t.stockBill}</span>
        </button>
      </div>
    </div>
  );
}

// Enhanced Chat Page Component
function ChatPage({ language, voiceEnabled, setVoiceEnabled, t, user, onDataChange }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: t.welcome, content_tamil: translations.tamil.welcome }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [pendingPdfData, setPendingPdfData] = useState(null);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text, isConfirmation = false) => {
    if (!text.trim() && !isConfirmation) return;
    
    const userMessage = { role: 'user', content: text };
    if (!isConfirmation) {
      setMessages(prev => [...prev, userMessage]);
    }
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: user?.user_id || 'demo_user',
          shop_id: user?.user_id || 'demo_shop',
          language: language,
          conversation_id: conversationId
        })
      });

      const data = await response.json();
      
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        content_tamil: data.response_tamil,
        audio_url: data.audio_url,
        data: data.data,
        show_table: data.show_table,
        table_data: data.table_data || data.pending_data,
        clear_pending: data.clear_pending,
        success: data.success
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Trigger dashboard refresh if transaction was successful
      if (data.success && onDataChange) {
        onDataChange();
      }

      // Play audio if voice mode is enabled
      if (voiceEnabled && data.audio_url) {
        try {
          const audioUrl = data.audio_url.startsWith('http') ? data.audio_url : `${API_URL}${data.audio_url}`;
          console.log('Playing audio from:', audioUrl);
          const audio = new Audio(audioUrl);
          audio.play().catch(err => {
            console.error('Audio playback error:', err);
            toast.error('Could not play voice response');
          });
        } catch (err) {
          console.error('Audio setup error:', err);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = () => {
    sendMessage('confirm', true);
  };

  const handleReject = () => {
    sendMessage('cancel', true);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendVoiceMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      toast.info(t.listening);
    } catch (error) {
      console.error('Recording error:', error);
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    setIsLoading(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.webm');
    formData.append('user_id', user?.user_id || 'demo_user');
    formData.append('shop_id', user?.user_id || 'demo_shop');
    formData.append('language', language);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    try {
      const response = await fetch(`${API_URL}/api/chat/voice`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages(prev => [...prev, 
        { role: 'user', content: '[Voice Message]', isVoice: true },
        { 
          role: 'assistant', 
          content: data.response, 
          content_tamil: data.response_tamil, 
          audio_url: data.audio_url,
          show_table: data.show_table,
          table_data: data.table_data || data.pending_data
        }
      ]);

      if (voiceEnabled && data.audio_url) {
        try {
          const audioUrl = data.audio_url.startsWith('http') ? data.audio_url : `${API_URL}${data.audio_url}`;
          console.log('Playing voice audio from:', audioUrl);
          const audio = new Audio(audioUrl);
          audio.play().catch(err => {
            console.error('Voice audio playback error:', err);
            toast.error('Could not play voice response');
          });
        } catch (err) {
          console.error('Voice audio setup error:', err);
        }
      }
    } catch (error) {
      console.error('Voice error:', error);
      toast.error('Voice message failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', user?.user_id || 'demo_user');
    formData.append('shop_id', user?.user_id || 'demo_shop');
    formData.append('language', language);

    try {
      const response = await fetch(`${API_URL}/api/pdf/parse`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.success) {
        setMessages(prev => [...prev,
          { role: 'user', content: `📄 Uploaded: ${file.name}`, isPdf: true },
          { 
            role: 'assistant', 
            content: data.message,
            content_tamil: data.message_tamil,
            show_pdf_selector: true,
            pdf_data: data.analysis
          }
        ]);
        setPendingPdfData(data.analysis);
      } else {
        toast.error(data.detail || 'Failed to parse PDF');
      }
    } catch (error) {
      console.error('PDF error:', error);
      toast.error('Failed to upload PDF');
    } finally {
      setIsLoading(false);
      e.target.value = '';
    }
  };

  const handlePdfTypeSelect = async (billType) => {
    if (!pendingPdfData) return;

    setIsLoading(true);
    try {
      console.log('Confirming PDF with type:', billType);
      console.log('PDF data:', pendingPdfData);

      const response = await fetch(`${API_URL}/api/pdf/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bill_type: billType,
          data: pendingPdfData,
          user_id: user?.user_id || 'demo_user',
          shop_id: user?.user_id || 'demo_shop'
        })
      });

      const data = await response.json();
      console.log('PDF confirm response:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to confirm PDF');
      }

      if (data.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message,
          success: true
        }]);
        toast.success(data.message);
        setPendingPdfData(null);

        // Trigger data refresh if callback provided
        if (onDataChange) {
          onDataChange();
        }
      } else {
        throw new Error(data.message || 'Failed to save PDF data');
      }
    } catch (error) {
      console.error('PDF confirm error:', error);
      toast.error(error.message || 'Failed to save PDF data');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <div 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
              data-testid={`chat-message-${idx}`}
            >
              <div 
                className={`max-w-[85%] md:max-w-[70%] px-4 py-3 rounded-2xl ${
                  msg.role === 'user' 
                    ? 'chat-bubble-user rounded-br-md' 
                    : 'chat-bubble-ai rounded-bl-md'
                } ${msg.success ? 'border border-primary' : ''}`}
              >
                {msg.isVoice && <Mic className="w-4 h-4 inline mr-1 opacity-60" />}
                {msg.isPdf && <FileText className="w-4 h-4 inline mr-1 opacity-60" />}
                <p className={language === 'tamil' ? 'font-tamil' : ''} style={{ whiteSpace: 'pre-line' }}>
                  {language === 'tamil' && msg.content_tamil ? msg.content_tamil : msg.content}
                </p>
                {msg.data && msg.data.transaction_id && (
                  <p className="text-xs mt-2 opacity-70">
                    ✓ Transaction: {msg.data.transaction_id}
                  </p>
                )}
              </div>
            </div>
            
            {/* Show confirmation table */}
            {msg.show_table && msg.table_data && (
              <ConfirmationTable 
                data={msg.table_data}
                onConfirm={handleConfirm}
                onReject={handleReject}
                language={language}
              />
            )}
            
            {/* Show PDF type selector */}
            {msg.show_pdf_selector && (
              <PdfTypeSelector 
                onSelect={handlePdfTypeSelect}
                language={language}
              />
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start animate-fadeIn">
            <div className="chat-bubble-ai px-4 py-3 rounded-2xl rounded-bl-md">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 glass border-t border-border safe-bottom">
        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            className="hidden"
          />
          <button 
            data-testid="attachment-btn"
            className="p-3 rounded-xl bg-secondary hover:bg-zinc-600 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <div className="flex-1 relative">
            <input
              data-testid="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
              placeholder={t.sendMessage}
              className="input w-full pr-12"
              disabled={isLoading || isRecording}
            />
          </div>

          <button
            data-testid="voice-btn"
            className={`p-3 rounded-xl transition-all ${
              isRecording
                ? 'bg-destructive voice-pulse'
                : 'bg-secondary hover:bg-zinc-600'
            }`}
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
          >
            {isRecording ? <Mic className="w-5 h-5" /> : <Mic className="w-5 h-5 opacity-60" />}
          </button>

          <button
            data-testid="send-btn"
            className="p-3 rounded-xl bg-primary text-black hover:bg-green-400 transition-colors disabled:opacity-50"
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Dashboard Page Component
function DashboardPage({ language, t, user, refreshTrigger, onDataChange }) {
  const [stats, setStats] = useState(null);
  const [stock, setStock] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [showAddModal, setShowAddModal] = useState(null);
  const [showTransactionsModal, setShowTransactionsModal] = useState(false);
  const [formData, setFormData] = useState({
    item_name: '',
    quantity: '',
    price: '',
    type: 'sale',
    selectedItem: null
  });

  const fetchData = useCallback(async () => {
    try {
      const userId = user?.user_id || 'demo_user';
      const shopId = user?.user_id || 'demo_shop';

      console.log('Fetching dashboard data for:', { userId, shopId });

      const [revenueRes, stockRes, transactionsRes] = await Promise.all([
        fetch(`${API_URL}/api/analytics/revenue?days=30&user_id=${userId}&shop_id=${shopId}`),
        fetch(`${API_URL}/api/stock/?user_id=${userId}&shop_id=${shopId}`),
        fetch(`${API_URL}/api/analytics/transactions?days=30&user_id=${userId}&shop_id=${shopId}&limit=100`)
      ]);

      if (!revenueRes.ok || !stockRes.ok || !transactionsRes.ok) {
        console.error('API error:', {
          revenue: revenueRes.status,
          stock: stockRes.status,
          transactions: transactionsRes.status
        });
        throw new Error('API error');
      }

      const revenueData = await revenueRes.json();
      const stockData = await stockRes.json();
      const transactionsData = await transactionsRes.json();

      console.log('Dashboard data received:', {
        revenue: revenueData,
        stockCount: stockData.items?.length,
        transactionsCount: transactionsData.transactions?.length
      });

      setStats(revenueData);
      setStock(stockData.items || []);
      setTransactions(transactionsData.transactions || []);
    } catch (error) {
      console.error('Dashboard error:', error);
      // Set defaults on error
      setStats({
        total_revenue: 0,
        total_transactions: 0,
        total_expenses: 0,
        low_stock_count: 0,
        total_stock_value: 0
      });
      setStock([]);
      setTransactions([]);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshTrigger]);

  const handleItemSelect = (itemName) => {
    if (showAddModal === 'sale') {
      // Find the selected item from stock
      const selectedStock = stock.find(item => item.name === itemName);
      if (selectedStock) {
        setFormData({
          ...formData,
          item_name: itemName,
          price: selectedStock.selling_price.toString(),
          selectedItem: selectedStock
        });
      }
    } else {
      setFormData({
        ...formData,
        item_name: itemName,
        selectedItem: null
      });
    }
  };

  const handleSubmit = async () => {
    const userId = user?.user_id || 'demo_user';

    // Validation
    if (!formData.item_name.trim()) {
      toast.error('Please enter item name');
      return;
    }
    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      toast.error('Please enter valid quantity');
      return;
    }
    if (!formData.price || parseFloat(formData.price) <= 0) {
      toast.error('Please enter valid price');
      return;
    }

    try {
      if (showAddModal === 'sale' || showAddModal === 'expense') {
        const response = await fetch(`${API_URL}/api/transactions/manual`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: showAddModal,
            items: [{
              item_name: formData.item_name,
              quantity: parseFloat(formData.quantity),
              unit_price: parseFloat(formData.price)
            }],
            payment_mode: 'cash',
            user_id: userId,
            shop_id: userId
          })
        });

        const data = await response.json();

        if (!response.ok) {
          // Handle stock validation errors
          if (data.detail && data.detail.issues) {
            const errorMsg = data.detail.issues.join('\n');
            toast.error(errorMsg);
          } else if (data.detail && data.detail.error) {
            toast.error(data.detail.error);
          } else {
            toast.error(data.detail || 'Failed to add transaction');
          }
          return;
        }

        toast.success(`${showAddModal.charAt(0).toUpperCase() + showAddModal.slice(1)} added successfully!`);
      } else if (showAddModal === 'stock') {
        const response = await fetch(`${API_URL}/api/stock/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.item_name,
            category: 'general',
            quantity: parseFloat(formData.quantity),
            cost_price: parseFloat(formData.price) * 0.8,
            selling_price: parseFloat(formData.price),
            user_id: userId,
            shop_id: userId
          })
        });

        const data = await response.json();

        if (!response.ok) {
          toast.error(data.detail || 'Failed to add stock');
          return;
        }

        toast.success('Stock added successfully!');
      }

      setShowAddModal(null);
      setFormData({ item_name: '', quantity: '', price: '', type: 'sale', selectedItem: null });
      await fetchData();

      // Trigger parent refresh if callback provided
      if (onDataChange) {
        onDataChange();
      }
    } catch (error) {
      console.error('Submit error:', error);
      toast.error('Failed to add entry. Please try again.');
    }
  };

  const lowStockItems = stock.filter(item => item.current_stock < (item.reorder_point || 10));

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-y-auto h-full">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card" data-testid="total-sales-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t.totalSales}</p>
              <p className="text-xl font-bold">₹{stats?.total_revenue?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <button
          className="card hover:border-primary transition-colors cursor-pointer text-left"
          data-testid="transactions-card"
          onClick={() => setShowTransactionsModal(true)}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <ShoppingCart className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t.transactions}</p>
              <p className="text-xl font-bold">{stats?.total_transactions || 0}</p>
            </div>
          </div>
        </button>

        <div className="card" data-testid="low-stock-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-accent/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t.lowStock}</p>
              <p className="text-xl font-bold">{stats?.low_stock_count || lowStockItems.length}</p>
            </div>
          </div>
        </div>

        <div className="card" data-testid="stock-value-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Stock Value</p>
              <p className="text-xl font-bold">₹{stats?.total_stock_value?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-3 gap-3">
        <button 
          data-testid="add-sale-btn"
          className="card flex flex-col items-center gap-2 hover:border-primary transition-colors"
          onClick={() => setShowAddModal('sale')}
        >
          <Plus className="w-6 h-6 text-primary" />
          <span className="text-sm">{t.addSale}</span>
        </button>
        <button 
          data-testid="add-stock-btn"
          className="card flex flex-col items-center gap-2 hover:border-primary transition-colors"
          onClick={() => setShowAddModal('stock')}
        >
          <Package className="w-6 h-6 text-blue-500" />
          <span className="text-sm">{t.addStock}</span>
        </button>
        <button 
          data-testid="add-expense-btn"
          className="card flex flex-col items-center gap-2 hover:border-primary transition-colors"
          onClick={() => setShowAddModal('expense')}
        >
          <DollarSign className="w-6 h-6 text-accent" />
          <span className="text-sm">{t.addExpense}</span>
        </button>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <div className="card border-accent/50">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-accent" />
            {t.lowStock} Items
          </h3>
          <div className="space-y-2">
            {lowStockItems.slice(0, 5).map((item, idx) => (
              <div key={idx} className="flex justify-between items-center p-2 bg-secondary rounded-lg">
                <span>{item.name}</span>
                <span className="text-accent font-medium">{item.current_stock} {item.unit}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock List */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Stock Inventory</h3>
          <button onClick={fetchData} className="p-2 hover:bg-secondary rounded-lg">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {stock.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center p-3 bg-secondary rounded-lg">
              <div>
                <p className="font-medium">{item.name}</p>
                <p className="text-sm text-muted-foreground">{item.category}</p>
              </div>
              <div className="text-right">
                <p className="font-medium">{item.current_stock} {item.unit}</p>
                <p className="text-sm text-primary">₹{item.selling_price}</p>
              </div>
            </div>
          ))}
          {stock.length === 0 && (
            <p className="text-center text-muted-foreground py-4">No stock items yet</p>
          )}
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md animate-slideUp">
            <h3 className="text-lg font-semibold mb-4 capitalize">Add {showAddModal}</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground">{t.itemName}</label>
                {showAddModal === 'sale' && stock.length > 0 ? (
                  <select
                    data-testid="modal-item-select"
                    className="input w-full mt-1"
                    value={formData.item_name}
                    onChange={(e) => handleItemSelect(e.target.value)}
                  >
                    <option value="">Select an item...</option>
                    {stock.map((item, idx) => (
                      <option key={idx} value={item.name}>
                        {item.name} - ₹{item.selling_price} ({item.current_stock} {item.unit} available)
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    data-testid="modal-item-name"
                    type="text"
                    className="input w-full mt-1"
                    value={formData.item_name}
                    onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
                    placeholder="e.g., Samosa, Rice"
                  />
                )}
              </div>

              {/* Show available stock for selected item */}
              {showAddModal === 'sale' && formData.selectedItem && (
                <div className="p-3 bg-secondary rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Available Stock:</span>
                    <span className="font-medium text-primary">
                      {formData.selectedItem.current_stock} {formData.selectedItem.unit}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-muted-foreground">Price per unit:</span>
                    <span className="font-medium">₹{formData.selectedItem.selling_price}</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">{t.quantity}</label>
                  <input
                    data-testid="modal-quantity"
                    type="number"
                    className="input w-full mt-1"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    placeholder="10"
                    min="0"
                    step="1"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">
                    {showAddModal === 'sale' ? 'Price per unit' : t.price}
                  </label>
                  <input
                    data-testid="modal-price"
                    type="number"
                    className="input w-full mt-1"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    placeholder="100"
                    min="0"
                    step="0.01"
                    readOnly={showAddModal === 'sale' && formData.selectedItem}
                  />
                </div>
              </div>

              {/* Show total for sales */}
              {showAddModal === 'sale' && formData.quantity && formData.price && (
                <div className="p-3 bg-primary/10 rounded-lg border border-primary/20">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Total Amount:</span>
                    <span className="text-xl font-bold text-primary">
                      ₹{(parseFloat(formData.quantity) * parseFloat(formData.price)).toFixed(2)}
                    </span>
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  data-testid="modal-cancel-btn"
                  className="btn-secondary flex-1"
                  onClick={() => {
                    setShowAddModal(null);
                    setFormData({ item_name: '', quantity: '', price: '', type: 'sale', selectedItem: null });
                  }}
                >
                  {t.cancel}
                </button>
                <button
                  data-testid="modal-submit-btn"
                  className="btn-primary flex-1"
                  onClick={handleSubmit}
                >
                  {t.submit}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Transactions Modal */}
      {showTransactionsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-4xl max-h-[80vh] flex flex-col animate-slideUp">
            <div className="flex justify-between items-center mb-4 pb-4 border-b border-border">
              <h3 className="text-lg font-semibold">Transaction History</h3>
              <button
                onClick={() => setShowTransactionsModal(false)}
                className="p-2 hover:bg-secondary rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto flex-1">
              {transactions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <ShoppingCart className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No transactions yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {transactions.map((txn, idx) => (
                    <div key={idx} className="p-4 bg-secondary rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              txn.type === 'sale' ? 'bg-primary/20 text-primary' :
                              txn.type === 'purchase' ? 'bg-blue-500/20 text-blue-500' :
                              'bg-accent/20 text-accent'
                            }`}>
                              {txn.type.toUpperCase()}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(txn.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            ID: {txn.transaction_id}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-bold">₹{txn.total_amount.toLocaleString()}</p>
                          <p className="text-xs text-muted-foreground capitalize">{txn.payment_mode}</p>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-medium text-muted-foreground mb-2">Items:</p>
                        <div className="space-y-1">
                          {txn.items.map((item, itemIdx) => (
                            <div key={itemIdx} className="flex justify-between text-sm">
                              <span>
                                {item.item_name} × {item.quantity} {item.unit}
                              </span>
                              <span className="font-medium">
                                ₹{item.unit_price} × {item.quantity} = ₹{item.total}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {txn.source && (
                        <div className="mt-2 pt-2 border-t border-border/50">
                          <span className="text-xs text-muted-foreground">
                            Source: <span className="capitalize">{txn.source}</span>
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-border">
              <button
                className="btn-secondary w-full"
                onClick={() => setShowTransactionsModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Enhanced Insights Page Component
function InsightsPage({ language, t, user }) {
  const [competitors, setCompetitors] = useState([]);
  const [summary, setSummary] = useState(null);
  const [festivals, setFestivals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);

  useEffect(() => {
    const fetchInsights = async () => {
      const location = user?.location?.city || 'Chennai';
      const userId = user?.user_id || 'demo_user';
      const shopId = user?.user_id || 'demo_shop';

      try {
        const [compRes, summaryRes, festRes] = await Promise.all([
          fetch(`${API_URL}/api/insights/competitors/detailed?location=${location}&user_id=${userId}`),
          fetch(`${API_URL}/api/insights/summary?language=${language}&user_id=${userId}&shop_id=${shopId}`),
          fetch(`${API_URL}/api/insights/festivals?location=Tamil Nadu&user_id=${userId}`)
        ]);

        const compData = await compRes.json();
        const summaryData = await summaryRes.json();
        const festData = await festRes.json();

        console.log('Insights data:', { compData, summaryData, festData });

        setCompetitors(compData.competitors || []);
        setSummary({...summaryData, strategic: compData.strategic_insights, shop_name: compData.data?.shop_name});
        setFestivals(festData.festivals || []);
      } catch (error) {
        console.error('Insights error:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, [language, user]);

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-y-auto h-full">
      {/* Business Summary */}
      <div className="card">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          {summary?.shop_name ? `${summary.shop_name} - Business Summary (7 Days)` : 'Business Summary (7 Days)'}
        </h3>
        {loading ? (
          <div className="animate-pulse space-y-2">
            <div className="h-4 bg-secondary rounded w-3/4" />
            <div className="h-4 bg-secondary rounded w-1/2" />
          </div>
        ) : summary?.insight ? (
          <div>
            <p className={`text-muted-foreground ${language === 'tamil' ? 'font-tamil' : ''}`}>
              {language === 'tamil' ? summary.insight.tamil : summary.insight.english}
            </p>
            {summary?.data && (
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="bg-secondary p-3 rounded-lg">
                  <div className="text-xs text-muted-foreground">Business Type</div>
                  <div className="text-sm font-semibold capitalize">{summary.data.business_type}</div>
                </div>
                <div className="bg-secondary p-3 rounded-lg">
                  <div className="text-xs text-muted-foreground">Stock Items</div>
                  <div className="text-sm font-semibold">{summary.data.stock_items_count || 0}</div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted-foreground">No summary available</p>
        )}
      </div>

      {/* Strategic Insights */}
      {summary?.strategic && (
        <div className="card border-primary/30">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Strategic Insights
          </h3>
          {summary.strategic.key_opportunities && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-muted-foreground mb-2">{t.opportunities}</h4>
              <div className="space-y-2">
                {summary.strategic.key_opportunities.map((opp, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2 bg-secondary rounded-lg">
                    <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                    <p className="text-sm">{opp}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {summary.strategic.recommended_actions && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Recommended Actions</h4>
              <div className="space-y-2">
                {summary.strategic.recommended_actions.map((action, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2 bg-primary/10 rounded-lg">
                    <Check className="w-4 h-4 text-primary mt-0.5" />
                    <p className="text-sm">{action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upcoming Festivals */}
      <div className="card">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-accent" />
          {t.festivals}
        </h3>
        <div className="space-y-3">
          {festivals.map((fest, idx) => (
            <div key={idx} className="p-3 bg-secondary rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium">{fest.festival?.name || fest.name}</h4>
                <span className="text-xs px-2 py-1 bg-accent/20 text-accent rounded-full">
                  {fest.festival?.type || fest.type || 'Festival'}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mb-2">
                {fest.festival?.description || fest.description}
              </p>
              {(fest.suggested_items || fest.festival?.suggested_items) && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">{t.stockSuggestions}:</p>
                  <div className="flex flex-wrap gap-1">
                    {(fest.suggested_items || fest.festival?.suggested_items || []).slice(0, 6).map((item, i) => (
                      <span key={i} className="text-xs px-2 py-1 bg-primary/20 text-primary rounded-full">
                        {typeof item === 'string' ? item : item.item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {festivals.length === 0 && !loading && (
            <p className="text-center text-muted-foreground py-4">No upcoming festivals</p>
          )}
        </div>
      </div>

      {/* Competitors */}
      <div className="card">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-500" />
          {t.competitors}
        </h3>
        <div className="space-y-3">
          {competitors.map((comp, idx) => (
            <div 
              key={idx} 
              className="p-3 bg-secondary rounded-xl cursor-pointer hover:bg-zinc-700 transition-colors"
              onClick={() => setSelectedCompetitor(selectedCompetitor === idx ? null : idx)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{comp.competitor?.name}</p>
                    {comp.threat_level === 'high' && (
                      <span className="text-xs px-2 py-0.5 bg-destructive/20 text-destructive rounded-full">
                        High Threat
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{comp.competitor?.address}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-accent" />
                  <span>{comp.competitor?.rating || 'N/A'}</span>
                  <ChevronRight className={`w-4 h-4 text-muted-foreground transition-transform ${selectedCompetitor === idx ? 'rotate-90' : ''}`} />
                </div>
              </div>
              
              {/* Expanded Details */}
              {selectedCompetitor === idx && comp.review_analysis && (
                <div className="mt-3 pt-3 border-t border-border animate-fadeIn">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-muted-foreground">Avg Rating</p>
                      <p className="font-medium">{comp.review_analysis.avg_rating?.toFixed(1) || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Reviews</p>
                      <p className="font-medium">{comp.review_analysis.total_reviews || 0}</p>
                    </div>
                  </div>
                  {comp.review_analysis.opportunities?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-muted-foreground mb-1">Your Opportunities:</p>
                      <div className="space-y-1">
                        {comp.review_analysis.opportunities.map((opp, i) => (
                          <p key={i} className="text-xs text-primary">• {opp}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {competitors.length === 0 && !loading && (
            <p className="text-center text-muted-foreground py-4">No competitors data</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('chat');
  const [language, setLanguage] = useState('english');
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Check for existing session
  useEffect(() => {
    const token = localStorage.getItem('hisaab_token');
    const savedUser = localStorage.getItem('hisaab_user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setLanguage(userData.language_preference || 'english');
    setVoiceEnabled(userData.voice_enabled ?? true);
  };

  const handleLogout = () => {
    localStorage.removeItem('hisaab_token');
    localStorage.removeItem('hisaab_user');
    setUser(null);
    toast.success('Logged out successfully');
  };

  const t = translations[language];

  const navItems = [
    { id: 'chat', icon: MessageSquare, label: t.chat },
    { id: 'dashboard', icon: LayoutDashboard, label: t.dashboard },
    { id: 'insights', icon: TrendingUp, label: t.insights },
    { id: 'settings', icon: Settings, label: t.settings }
  ];

  // Show auth page if not logged in
  if (!user) {
    return (
      <>
        <Toaster position="top-center" theme="dark" />
        <AuthPage onLogin={handleLogin} language={language} />
      </>
    );
  }

  return (
    <div className="h-screen flex flex-col md:flex-row overflow-hidden">
      <Toaster position="top-center" theme="dark" />
      
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-60 bg-card border-r border-border p-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
            <span className="text-black font-bold text-lg">H</span>
          </div>
          <h1 className="text-xl font-bold">Hisaab</h1>
        </div>
        
        {/* User Info */}
        <div className="mb-6 p-3 bg-secondary rounded-xl">
          <p className="font-medium truncate">{user.shop_name}</p>
          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
        </div>

        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                currentPage === item.id 
                  ? 'bg-primary text-black font-semibold' 
                  : 'hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Settings Section */}
        <div className="border-t border-border pt-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{t.language}</span>
            <button
              data-testid="language-toggle-desktop"
              onClick={() => setLanguage(language === 'english' ? 'tamil' : 'english')}
              className="flex items-center gap-2 px-3 py-1.5 bg-secondary rounded-lg text-sm"
            >
              <Globe className="w-4 h-4" />
              {language === 'english' ? 'EN' : 'தமி'}
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{t.voiceMode}</span>
            <button
              data-testid="voice-toggle-desktop"
              onClick={() => setVoiceEnabled(!voiceEnabled)}
              className={`p-2 rounded-lg ${voiceEnabled ? 'bg-primary text-black' : 'bg-secondary'}`}
            >
              {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
          </div>
          <button
            data-testid="logout-btn"
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-card border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-black font-bold">H</span>
          </div>
          <div>
            <h1 className="font-bold text-sm">{user.shop_name}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            data-testid="language-toggle-mobile"
            onClick={() => setLanguage(language === 'english' ? 'tamil' : 'english')}
            className="p-2 bg-secondary rounded-lg"
          >
            <Globe className="w-5 h-5" />
          </button>
          <button
            data-testid="voice-toggle-mobile"
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={`p-2 rounded-lg ${voiceEnabled ? 'bg-primary text-black' : 'bg-secondary'}`}
          >
            {voiceEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentPage === 'chat' && (
          <ChatPage
            language={language}
            voiceEnabled={voiceEnabled}
            setVoiceEnabled={setVoiceEnabled}
            t={t}
            user={user}
            onDataChange={() => setRefreshTrigger(prev => prev + 1)}
          />
        )}
        {currentPage === 'dashboard' && (
          <DashboardPage
            language={language}
            t={t}
            user={user}
            refreshTrigger={refreshTrigger}
            onDataChange={() => setRefreshTrigger(prev => prev + 1)}
          />
        )}
        {currentPage === 'insights' && (
          <InsightsPage language={language} t={t} user={user} />
        )}
        {currentPage === 'settings' && (
          <div className="p-6 overflow-y-auto h-full">
            <h2 className="text-2xl font-bold mb-4">{t.settings}</h2>
            <div className="space-y-4 max-w-md">
              <div className="card">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Account
                </h3>
                <div className="space-y-2 text-sm">
                  <p><span className="text-muted-foreground">Shop:</span> {user.shop_name}</p>
                  <p><span className="text-muted-foreground">Email:</span> {user.email}</p>
                  <p><span className="text-muted-foreground">Type:</span> {user.business_type}</p>
                </div>
              </div>
              
              <div className="card">
                <h3 className="font-semibold mb-3">Preferences</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>{t.language}</span>
                    <select
                      data-testid="language-select"
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="input"
                    >
                      <option value="english">English</option>
                      <option value="tamil">தமிழ் (Tamil)</option>
                    </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>{t.voiceMode}</span>
                    <button
                      data-testid="voice-toggle-settings"
                      onClick={() => setVoiceEnabled(!voiceEnabled)}
                      className={`px-4 py-2 rounded-lg ${voiceEnabled ? 'bg-primary text-black' : 'bg-secondary'}`}
                    >
                      {voiceEnabled ? 'On' : 'Off'}
                    </button>
                  </div>
                </div>
              </div>
              
              <button
                data-testid="logout-btn-settings"
                onClick={handleLogout}
                className="w-full py-3 bg-destructive/20 text-destructive rounded-xl hover:bg-destructive/30 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden flex items-center justify-around bg-card border-t border-border py-2 safe-bottom">
        {navItems.map((item) => (
          <button
            key={item.id}
            data-testid={`mobile-nav-${item.id}`}
            onClick={() => setCurrentPage(item.id)}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-colors ${
              currentPage === item.id 
                ? 'text-primary' 
                : 'text-muted-foreground'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="text-xs">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

export default App;
