import React, { useState } from 'react';
import {
  Bot,
  Send,
  CheckCircle2,
  AlertTriangle,
  Terminal,
  Copy,
  Check,
  ExternalLink,
  Sliders,
  User,
  FileText,
  Sparkles,
  RefreshCw,
  Play,
  ShieldCheck,
  Code2,
  Bell,
  CheckCheck,
  KeyRound,
  MessageCircle,
} from 'lucide-react';

interface SimulatedThreadsPost {
  id: string;
  title: string;
  username: string;
  url: string;
  published: string;
  text: string;
  tags: string[];
  filterResult: {
    passed: boolean;
    reason: string;
  };
  aiDraft?: {
    isOpportunity: boolean;
    relevance: number;
    summary: string;
    commentDraft: string;
    dmDraft: string;
    failedAi?: boolean;
  };
}

const SAMPLE_THREADS_POSTS: SimulatedThreadsPost[] = [
  {
    id: "18045920194819201",
    title: "Dicari Senior Flutter Developer untuk startup edutech (Remote/Kontrak)",
    username: "startup_recruiter",
    url: "https://www.threads.net/@startup_recruiter/post/C9x81YzLmpQ",
    published: "Baru saja (20 menit lalu)",
    text: "Halo warga Threads! Kami sedang dicari Senior Flutter Developer untuk memimpin revamp aplikasi edutech kami. Butuh yang mahir Bloc, clean architecture, & offline-first. Kontrak freelance 3 bulan rate $30/jam. Silakan DM portofolio GitHub atau kirim CV ke careers@edutech.io!",
    tags: ["flutter", "dicari", "freelance", "kontrak", "dm"],
    filterResult: {
      passed: true,
      reason: "Lolos filter: Mengandung kata utuh \\bflutter\\b dan sinyal peluang \\bdicari\\b, \\bfreelance\\b, \\bdm\\b",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 9,
      summary: "Startup edutech mencari Senior Flutter Developer untuk revamp aplikasi dengan Bloc & clean architecture ($30/jam).",
      commentDraft: "Hi! I have 4+ years building production-grade Flutter apps with Bloc and offline caching. Would love to help revamp the app—mind if I send you a DM with my portfolio?",
      dmDraft: "Halo! Saya membaca postingan lowongan Anda di Threads untuk posisi Flutter Developer. Saya berpengalaman membangun aplikasi Flutter berskala besar dengan Bloc, Clean Architecture, dan sinkronisasi data offline. Portofolio & GitHub saya: https://github.com/yourusername. Kapan waktu yang nyaman untuk mengobrol singkat mengenai roadmap revamp ini? Terima kasih!",
    },
  },
  {
    id: "18099238491823941",
    title: "Need Android Kotlin Developer for Fintech Application",
    username: "fintech_founder",
    url: "https://www.threads.net/@fintech_founder/post/C9z01BaKnmP",
    published: "1 jam lalu",
    text: "We are hiring an Android Kotlin engineer to help ship our wallet payment flow. Must be strong with Jetpack Compose and biometric security APIs. Remote contract, open position immediate start. DM me if interested!",
    tags: ["kotlin", "android developer", "hiring", "open position", "dm"],
    filterResult: {
      passed: true,
      reason: "Lolos filter: Mengandung kata utuh \\bkotlin\\b, \\bandroid developer\\b dan sinyal \\bhiring\\b, \\bdm\\b",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 9,
      summary: "Founder fintech mencari Android Kotlin Developer (Jetpack Compose) untuk fitur wallet dan biometric security secara remote.",
      commentDraft: "Hi! Experienced Android developer here with Jetpack Compose & secure biometric authentication flows. Just sent you a DM with my work history!",
      dmDraft: "Hi there! I saw your Threads post looking for an Android Kotlin developer for your payment flow. I specialize in modern Android with Jetpack Compose, Coroutines, and secure SDK integrations. Here is my GitHub with similar mobile fintech modules: https://github.com/yourusername. Would love to connect and hear more about the timeline! Thanks.",
    },
  },
  {
    id: "18012398471293847",
    title: "Looking for a React Native & Expo developer for freelance gig",
    username: "agency_lead",
    url: "https://www.threads.net/@agency_lead/post/C9y77LaPqxZ",
    published: "2 jam lalu",
    text: "Hey Threads, looking for a freelance React Native developer familiar with modern Expo SDK 52 and TypeScript for an MVP project. Send CV or portfolio via DM.",
    tags: ["react native", "expo", "looking for", "freelance", "dm"],
    filterResult: {
      passed: true,
      reason: "Lolos filter: Mengandung kata utuh \\bexpo\\b, \\breact native\\b dan sinyal \\blooking for\\b, \\bfreelance\\b",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 8,
      summary: "Agency mencari Freelance React Native & Expo developer untuk pengerjaan project MVP berbasis TypeScript.",
      commentDraft: "Hi! I build smooth, production-ready apps with modern Expo SDK and TypeScript. Can I shoot you a quick DM with my recent apps?",
      dmDraft: "Hi! I saw your post looking for a React Native & Expo developer. I've built multiple cross-platform apps with Expo, TypeScript, and fast turnaround MVPs. You can check out my live apps and code here: https://github.com/yourusername. Looking forward to discussing your project scope! Best regards.",
    },
  },
  {
    id: "18055667788990011",
    title: "Thoughts on mobile app developer exposure in modern marketing",
    username: "tech_influencer",
    url: "https://www.threads.net/@tech_influencer/post/C9w22MmKqpS",
    published: "3 jam lalu",
    text: "Discussing how brand exposure affects mobile apps nowadays. Great exposure helps remote projects succeed.",
    tags: ["exposure", "diskusi"],
    filterResult: {
      passed: false,
      reason: "REJECTED by Filter: Kata 'exposure' tidak mencocokkan kata utuh \\bexpo\\b, dan tidak ada sinyal penawaran kerja spesifik (hiring, dicari, butuh).",
    },
  },
  {
    id: "18077889900112233",
    title: "[Open to work] Junior Flutter developer available for hire",
    username: "flutter_novice",
    url: "https://www.threads.net/@flutter_novice/post/C9u11LlOopT",
    published: "4 jam lalu",
    text: "Hi everyone, I am open to work and looking for a job as junior mobile developer. DM me if anyone is looking for hire.",
    tags: ["open to work", "job seeker"],
    filterResult: {
      passed: false,
      reason: "REJECTED by Filter: Terdeteksi kata kunci pencari kerja 'open to work' & 'looking for a job' (Bukan lowongan).",
    },
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'threads_setup' | 'profile' | 'config'>('simulator');
  const [selectedPost, setSelectedPost] = useState<SimulatedThreadsPost>(SAMPLE_THREADS_POSTS[0]);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isRunningDryRun, setIsRunningDryRun] = useState(false);
  const [dryRunOutput, setDryRunOutput] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleSimulateRun = () => {
    setIsRunningDryRun(true);
    setDryRunOutput("Menjalankan pipeline: Memindai Meta Threads API via keyword_search...");

    setTimeout(() => {
      setDryRunOutput(
        `2026-10-27 [INFO] JobBot-Threads: Memulai pemindaian Meta Threads API resmi (Token: THQW...789x)\n` +
        `2026-10-27 [INFO] sources.threads: Mencari keyword: 'flutter developer', 'kotlin android', 'react native developer'...\n` +
        `2026-10-27 [INFO] sources.threads: Total postingan Threads diambil: 48\n` +
        `2026-10-27 [INFO] core.filters: 45 postingan di-reject (diskusi umum, pencari kerja, exposure bukan expo)\n` +
        `2026-10-27 [INFO] core.filters: 3 postingan lolos filter bertahap (kata utuh mobile + sinyal peluang spesifik)\n` +
        `2026-10-27 [INFO] core.gemini_client: Evaluasi AI (gemini-3.1-flash-lite) berhasil untuk 3 postingan (Skor: 9/10, 9/10, 8/10)\n` +
        `2026-10-27 [INFO] core.notifier: Format notifikasi Telegram dengan tombol 'Buka di Threads' siap dikirim.\n` +
        `2026-10-27 [INFO] JobBot-Threads: Total notifikasi yang AKAN dikirim (dry-run, tidak dikirim): 3`
      );
      setIsRunningDryRun(false);
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header Banner */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/20 text-white font-bold">
              🧵
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Mobile Job Opportunity Bot (Meta Threads)
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Threads Graph API Resmi
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Khusus Meta Threads (No Scraping) • Filter Kata Utuh Regex (\b) • Gemini AI • Notif Telegram
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleSimulateRun}
              disabled={isRunningDryRun}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-sm disabled:opacity-50"
            >
              {isRunningDryRun ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              {isRunningDryRun ? 'Memindai Threads...' : 'Simulasi Dry Run'}
            </button>
            <button
              onClick={() => copyToClipboard('python main.py --dry-run', 'quick_cmd')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-slate-700 transition"
              title="Salin perintah CLI dry run"
            >
              {copiedKey === 'quick_cmd' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Terminal className="w-3.5 h-3.5" />}
              <span>python main.py --dry-run</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto gap-1 border-t border-slate-800/60 pt-1 text-xs sm:text-sm">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'simulator'
                ? 'border-indigo-400 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageCircle className="w-4 h-4" />
            Simulator Notifikasi Threads & Draft AI
          </button>
          <button
            onClick={() => setActiveTab('threads_setup')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'threads_setup'
                ? 'border-indigo-400 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <KeyRound className="w-4 h-4" />
            Panduan Meta Threads API & Token
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'profile'
                ? 'border-indigo-400 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <User className="w-4 h-4" />
            Profil Developer (profile.md)
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'config'
                ? 'border-indigo-400 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" />
            Filter Kata Utuh & Keywords (config.yaml)
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Terminal Log Output if Run */}
        {dryRunOutput && (
          <div className="mb-6 p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
              <span className="flex items-center gap-1.5 text-indigo-400">
                <Terminal className="w-3.5 h-3.5" /> Log Simulasi CLI (Threads Mode)
              </span>
              <button
                onClick={() => setDryRunOutput(null)}
                className="hover:text-white transition text-[11px]"
              >
                Tutup [x]
              </button>
            </div>
            <pre className="whitespace-pre-wrap leading-relaxed text-slate-300">
              {dryRunOutput}
            </pre>
          </div>
        )}

        {/* TAB 1: SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Feed list */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white uppercase tracking-wider">
                    Postingan Meta Threads ({SAMPLE_THREADS_POSTS.length})
                  </span>
                </div>
                <span className="text-xs text-slate-400">Klik postingan untuk melihat preview</span>
              </div>

              <div className="space-y-2.5">
                {SAMPLE_THREADS_POSTS.map((post) => {
                  const isSelected = selectedPost.id === post.id;
                  return (
                    <div
                      key={post.id}
                      onClick={() => setSelectedPost(post)}
                      className={`p-3.5 rounded-xl border text-left cursor-pointer transition ${
                        isSelected
                          ? 'bg-slate-800/90 border-indigo-500 shadow-md shadow-indigo-500/10'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="text-[11px] font-medium text-indigo-300 flex items-center gap-1">
                          @{post.username} • {post.published}
                        </span>
                        {post.filterResult.passed ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Lolos Filter
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            Ditolak
                          </span>
                        )}
                      </div>

                      <h3 className="text-xs sm:text-sm font-semibold text-slate-100 line-clamp-2 mb-2">
                        {post.title}
                      </h3>

                      <div className="flex flex-wrap gap-1">
                        {post.tags.map((t, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Security Banner */}
              <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800 text-slate-400 text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-medium text-slate-300">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Keamanan & Kepatuhan Threads API Resmi
                </div>
                <p className="text-[11px] leading-relaxed">
                  Semua kueri dieksekusi melalui endpoint <code>https://graph.threads.net/v1.0/keyword_search</code>. Tidak ada auto-comment, tidak ada auto-DM. Anda mengontrol pesan dan mengirimkannya secara manual.
                </p>
              </div>
            </div>

            {/* Right: Telegram Card Preview */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-indigo-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
                    Format Pesan Telegram (Persis di HP)
                  </h2>
                </div>
                <span className="text-xs text-slate-400 font-mono">HTML Parse Mode</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl p-5 sm:p-6 space-y-5">
                {selectedPost.filterResult.passed && selectedPost.aiDraft ? (
                  <>
                    {/* Header */}
                    <div className="space-y-2 border-b border-slate-800/80 pb-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold text-sm border border-indigo-500/30">
                            🔔 [{selectedPost.aiDraft.relevance}/10]
                          </span>
                          <span className="text-sm font-semibold text-slate-100">
                            {selectedPost.title}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>📌 Threads: @{selectedPost.username}</span>
                        <span>•</span>
                        <span>{selectedPost.published}</span>
                      </div>
                    </div>

                    {/* Summary */}
                    <div className="space-y-1">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        Ringkasan Peluang (Gemini AI)
                      </div>
                      <p className="text-xs sm:text-sm text-slate-200 bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                        {selectedPost.aiDraft.summary}
                      </p>
                    </div>

                    {/* URL Link */}
                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/30 border border-slate-800 text-xs">
                      <span className="text-slate-400 truncate max-w-xs">
                        🔗 {selectedPost.url}
                      </span>
                      <a
                        href={selectedPost.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Buka Postingan <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    {/* Comment Draft */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                          💬 Draft Komentar di Threads (Maks 2 Kalimat)
                        </span>
                        <button
                          onClick={() => copyToClipboard(selectedPost.aiDraft?.commentDraft || '', 'comment')}
                          className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/60 px-2 py-0.5 rounded border border-indigo-800/60 transition"
                        >
                          {copiedKey === 'comment' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedKey === 'comment' ? 'Tersalin!' : 'Copy Komentar'}
                        </button>
                      </div>
                      <div
                        onClick={() => copyToClipboard(selectedPost.aiDraft?.commentDraft || '', 'comment')}
                        className="p-3 rounded-lg bg-slate-950 border border-indigo-900/40 text-indigo-200 font-mono text-xs cursor-pointer hover:border-indigo-500 transition select-all relative group"
                        title="Klik untuk menyalin"
                      >
                        <code>{selectedPost.aiDraft.commentDraft}</code>
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          Tap to copy
                        </div>
                      </div>
                    </div>

                    {/* DM Draft */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
                          ✉️ Draft DM Personal (Maks 5 Kalimat)
                        </span>
                        <button
                          onClick={() => copyToClipboard(selectedPost.aiDraft?.dmDraft || '', 'dm')}
                          className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-800/60 transition"
                        >
                          {copiedKey === 'dm' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedKey === 'dm' ? 'Tersalin!' : 'Copy DM'}
                        </button>
                      </div>
                      <div
                        onClick={() => copyToClipboard(selectedPost.aiDraft?.dmDraft || '', 'dm')}
                        className="p-3.5 rounded-lg bg-slate-950 border border-emerald-900/40 text-emerald-200 font-mono text-xs leading-relaxed cursor-pointer hover:border-emerald-500 transition select-all relative group"
                        title="Klik untuk menyalin"
                      >
                        <code>{selectedPost.aiDraft.dmDraft}</code>
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          Tap to copy
                        </div>
                      </div>
                    </div>

                    {/* Inline Button */}
                    <div className="pt-2">
                      <a
                        href={selectedPost.url}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full py-2.5 px-4 rounded-xl bg-indigo-600/80 hover:bg-indigo-600 text-white font-medium text-xs flex items-center justify-center gap-2 border border-indigo-500/50 transition shadow-lg shadow-indigo-600/20"
                      >
                        🧵 Buka di Threads (Tombol Inline Telegram)
                      </a>
                    </div>
                  </>
                ) : (
                  /* Rejection View */
                  <div className="py-12 px-4 text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
                      <AlertTriangle className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-white">
                      Postingan Ini Ditolak Filter Kata Utuh
                    </h3>
                    <p className="text-xs text-rose-300 max-w-md mx-auto bg-rose-950/40 p-3 rounded-lg border border-rose-900/50">
                      {selectedPost.filterResult.reason}
                    </p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Pencocokan regex <code>\b</code> memastikan kata seperti "exposure" tidak salah dianggap "expo", dan pencari kerja tidak akan memicu pemanggilan Gemini.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: META THREADS SETUP */}
        {activeTab === 'threads_setup' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-indigo-400" />
                Panduan Setup Meta Threads API & Token Generator
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Ikuti alur resmi Meta for Developers untuk mendapatkan User Access Token jangka panjang (~60 hari).
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Step 1 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                    1
                  </div>
                  <h3 className="text-sm font-bold text-white">Buat Meta App & Tambahkan Threads</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Buka <a href="https://developers.facebook.com" target="_blank" rel="noreferrer" className="text-indigo-400 underline">developers.facebook.com</a> &gt; <strong>Create App</strong> &gt; Pilih produk <strong>Threads</strong> &gt; Berikan permission <code>threads_basic</code> dan <code>threads_keyword_search</code>.
                </p>
              </div>

              {/* Step 2 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                    2
                  </div>
                  <h3 className="text-sm font-bold text-white">Daftarkan Akun sebagai Threads Tester</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Di App Dashboard, buka <strong>Roles</strong> &gt; <strong>Threads Testers</strong> &gt; masukkan username akun Threads Anda. Lalu buka aplikasi Threads di HP &gt; <em>Settings &gt; Account &gt; Website permissions &gt; Invites</em> untuk menerima undangan tester.
                </p>
              </div>

              {/* Step 3 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                    3
                  </div>
                  <h3 className="text-sm font-bold text-white">Generate Token & Isi .env</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Di menu <strong>Threads</strong> &gt; <strong>User Token Generator</strong>, klik <strong>Generate Token</strong>. Salin token berumur panjang (~60 hari) ke file <code>.env</code> Anda:
                </p>
                <div className="p-2.5 rounded bg-slate-950 font-mono text-[11px] text-indigo-200 border border-slate-800">
                  THREADS_ACCESS_TOKEN=THQW...token_anda
                </div>
              </div>

              {/* Step 4 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs border border-emerald-500/30">
                    4
                  </div>
                  <h3 className="text-sm font-bold text-white">Perbarui Token via Script Manual</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Sebelum 60 hari habis (atau saat menerima notifikasi pengingat &lt;10 hari di Telegram), perpanjang token dengan menjalankan skrip resmi:
                </p>
                <button
                  onClick={() => copyToClipboard('python scripts/refresh_token.py', 'ref_cmd')}
                  className="w-full py-1.5 px-3 rounded bg-slate-800 hover:bg-slate-700 font-mono text-xs text-slate-200 flex items-center justify-center gap-1.5 border border-slate-700"
                >
                  {copiedKey === 'ref_cmd' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>python scripts/refresh_token.py</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: PROFILE */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <User className="w-5 h-5 text-indigo-400" />
                Profil Pengembang Mobile (config/profile.md)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Pastikan mengganti semua placeholder contoh (seperti <code>yourusername</code>) dengan data nyata agar bot tidak menolak pengiriman notifikasi.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
                <span className="font-mono text-indigo-400">config/profile.md</span>
                <span className="text-[11px] text-amber-400">⚠️ Wajib diisi sebelum production</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 leading-relaxed max-h-[360px] overflow-y-auto">
                <pre>{`# Profil Pengembang Mobile
- Nama: [Ganti dengan Nama Lengkap Anda]
- Role: Senior / Mid Mobile Developer (Flutter, Android Kotlin, React Native)
- Lokasi: Indonesia (Siap Remote Global: UTC+7 s/d US/EU overlap)
- Pengalaman: 4+ tahun mobile engineering
- Ketersediaan: Freelance / Contract / Full-time Remote

## Keahlian Utama:
• Flutter & Dart (Bloc, Riverpod, Offline-first)
• Native Android (Kotlin, Jetpack Compose, Coroutines)
• React Native & Expo (TypeScript, Zustand, EAS)

## Portofolio & Proyek:
• GitHub: https://github.com/usernameaslianda
• LinkedIn: https://linkedin.com/in/usernameaslianda`}</pre>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CONFIG */}
        {activeTab === 'config' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" />
                Konfigurasi Kata Utuh & Keywords (config.yaml)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Pencocokan kata utuh dengan regex <code>\b</code> memastikan zero false-positive.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                    Mobile Keywords (\\b)
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Wajib Ada (1+)</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['flutter', 'kotlin', 'android developer', 'react native', 'mobile developer', 'dart', 'expo'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-800/60 text-indigo-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                    Sinyal Peluang Spesifik
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Wajib Ada (1+)</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['hiring', 'dicari', 'lowongan', 'butuh', 'need', 'looking for', 'freelance', 'kontrak', 'open position', 'kirim cv', 'dm'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-rose-300 uppercase tracking-wider">
                    Exclude Keywords
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Langsung Drop</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['open to work', 'available for hire', 'cari kerja', 'looking for a job', 'for hire', '[for hire]', 'unpaid', 'magang'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-rose-950/60 border border-rose-800/60 text-rose-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-950/80 py-4 px-4 text-center text-xs text-slate-500">
        Mobile Job Opportunity Bot (Meta Threads Source) • 100% Biaya Rp0 • Meta Graph API Resmi & Gemini AI
      </footer>
    </div>
  );
}
