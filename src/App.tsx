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
  Clock,
  Smartphone,
  Layers,
  Search,
  ChevronRight,
  ShieldCheck,
  Code2,
  Bell,
  Github,
  CheckCheck,
} from 'lucide-react';

interface SimulatedJob {
  id: string;
  title: string;
  source: string;
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
    usedFallback: boolean;
  };
}

const INITIAL_JOBS: SimulatedJob[] = [
  {
    id: "rss_remoteok_102",
    title: "Senior Flutter Developer (Cross-Platform Mobile Apps) - Remote",
    source: "RSS: RemoteOK",
    url: "https://remoteok.com/remote-mobile-jobs",
    published: "Baru saja (25 menit lalu)",
    text: "We are hiring an experienced Senior Flutter developer to build our next-generation consumer mobile application. Must have deep experience with Dart, Bloc or Riverpod state management, REST API integration, and clean architecture. Contract position with potential for full-time. Rate: $30 - $45 / hour.",
    tags: ["flutter", "remote", "contract", "bloc"],
    filterResult: {
      passed: true,
      reason: "Passed: Contains mobile keyword ('flutter') & hiring keyword ('hiring', 'contract')",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 9,
      summary: "Perusahaan mencari Senior Flutter Developer untuk membangun aplikasi consumer mobile dengan arsitektur bersih dan Bloc/Riverpod ($30-$45/jam).",
      commentDraft: "Hi! I have 4+ years building high-performance Flutter apps with Bloc and clean architecture. Would love to help you scale this out—mind if I send you a DM with my portfolio?",
      dmDraft: "Hi there! I saw your post looking for a Senior Flutter Developer. I've built and deployed multiple production Flutter apps with Bloc, robust REST APIs, and 60fps animations. You can view my live work and GitHub here: https://github.com/yourusername. When would be a good time for a quick 10-minute chat to discuss your milestones? Thanks!",
      usedFallback: false,
    },
  },
  {
    id: "reddit_forhire_881",
    title: "Need Android Kotlin Developer for Fintech App (Jetpack Compose)",
    source: "Reddit: r/forhire",
    url: "https://www.reddit.com/r/forhire",
    published: "1 jam lalu",
    text: "We are an early stage fintech startup looking for a skilled Android developer fluent in Kotlin and Jetpack Compose. Need someone who can build secure biometric authentication, offline Room caching, and integrate Stripe/Plaid SDKs. Remote, $35/hr.",
    tags: ["kotlin", "android", "fintech", "jetpack compose"],
    filterResult: {
      passed: true,
      reason: "Passed: Contains mobile keyword ('android', 'kotlin') & hiring keyword ('looking for', 'remote')",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 9,
      summary: "Startup fintech mencari Android Kotlin Developer (Jetpack Compose) untuk fitur autentikasi biometrik & integrasi payment ($35/jam).",
      commentDraft: "Halo! Saya Android developer berpengalaman dengan Jetpack Compose, Coroutines, dan integrasi security payment. Tertarik berdiskusi lebih lanjut via DM?",
      dmDraft: "Halo! Saya membaca postingan Anda tentang kebutuhan Android Kotlin Developer untuk aplikasi fintech. Saya berpengalaman membangun arsitektur MVVM/MVI dengan Compose, Room DB, dan integrasi payment gateway yang aman. Portofolio & proyek saya: https://github.com/yourusername. Kapan waktu yang pas untuk mendiskusikan kebutuhan teknisnya? Terima kasih!",
      usedFallback: false,
    },
  },
  {
    id: "hn_algolia_5024",
    title: "Ask HN: Who is hiring? Lead React Native / Expo Engineer (Comment #5025)",
    source: "Hacker News (Who is hiring)",
    url: "https://news.ycombinator.com/item?id=50254477",
    published: "3 jam lalu",
    text: "Acme Labs (YC W24) is hiring our first mobile engineer to lead our React Native & Expo app development. We are building a collaboration tool used by 10k daily active users. 100% remote, full-time or long-term contract.",
    tags: ["react native", "expo", "remote", "whoishiring"],
    filterResult: {
      passed: true,
      reason: "Passed: Contains mobile keyword ('react native', 'expo') & hiring keyword ('hiring')",
    },
    aiDraft: {
      isOpportunity: true,
      relevance: 8,
      summary: "Acme Labs (YC W24) mencari Lead React Native / Expo Engineer untuk aplikasi kolaborasi dengan 10k DAU secara 100% remote.",
      commentDraft: "Hi! I specialize in React Native & modern Expo SDKs with smooth UI and native bridging. Would love to learn more about Acme Labs—can I shoot you a quick DM?",
      dmDraft: "Hi there! I saw your hiring post for a Lead React Native / Expo Engineer at Acme Labs. I've led cross-platform mobile apps using Expo, TypeScript, and state synchronization with proven reliability. Check out my GitHub & previous projects: https://github.com/yourusername. Would welcome the chance to discuss how I can contribute to Acme Labs!",
      usedFallback: false,
    },
  },
  {
    id: "reddit_rejected_forhire_01",
    title: "[FOR HIRE] Junior Flutter Developer ready to build your mobile app for cheap",
    source: "Reddit: r/forhire",
    url: "https://www.reddit.com/r/forhire",
    published: "4 jam lalu",
    text: "Hello everyone, I am available for hire. I know Flutter and Dart. Please contact me if you need help.",
    tags: ["[for hire]", "job seeker"],
    filterResult: {
      passed: false,
      reason: "REJECTED by Pre-Filter: Matched exclude keyword '[for hire]' (Pencari kerja, bukan lowongan)",
    },
  },
  {
    id: "rss_rejected_unpaid_02",
    title: "Unpaid Mobile App Developer Internship for University Students",
    source: "RSS: Job Board",
    url: "https://example.com/unpaid-intern",
    published: "5 jam lalu",
    text: "Join our summer unpaid internship program to gain experience building Android applications.",
    tags: ["unpaid", "internship"],
    filterResult: {
      passed: false,
      reason: "REJECTED by Pre-Filter: Matched exclude keyword 'unpaid' / 'internship'",
    },
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'profile' | 'config' | 'guide'>('simulator');
  const [selectedJob, setSelectedJob] = useState<SimulatedJob>(INITIAL_JOBS[0]);
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
    setDryRunOutput("Menjalankan pipeline bot: Memindai RSS, Reddit, & Hacker News...");

    setTimeout(() => {
      setDryRunOutput(
        `[INFO] JobBot: Total raw items collected from all sources: 115\n` +
        `[INFO] core.filters: 112 items filtered out (job seekers, unpaid, unrelated stack)\n` +
        `[INFO] core.filters: 3 items qualified for AI review\n` +
        `[INFO] Gemini AI (gemini-3.8-flash): Evaluated 3 items -> 3 opportunities qualified (Scores: 9/10, 9/10, 8/10)\n` +
        `[INFO] TelegramNotifier: Formatted Telegram alerts generated with 1-tap copyable draft comment & DM.\n` +
        `[SUCCESS] Dry-run completed cleanly without API errors. State seen.json unchanged.`
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
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  Mobile Job Opportunity Bot
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Rp0 / Free Tier
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Flutter • Android Kotlin • React Native | Telegram + Gemini AI Drafts
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleSimulateRun}
              disabled={isRunningDryRun}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-sm disabled:opacity-50"
            >
              {isRunningDryRun ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              {isRunningDryRun ? 'Memindai...' : 'Simulasi Dry Run'}
            </button>
            <button
              onClick={() => copyToClipboard('python main.py --dry-run', 'quick_cmd')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-slate-700 transition"
              title="Salin perintah dry run"
            >
              {copiedKey === 'quick_cmd' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Terminal className="w-3.5 h-3.5" />}
              <span>python main.py</span>
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto gap-1 border-t border-slate-800/60 pt-1 text-xs sm:text-sm">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'simulator'
                ? 'border-cyan-400 text-cyan-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            Live Opportunity & Draft Simulator
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'profile'
                ? 'border-cyan-400 text-cyan-400 font-semibold'
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
                ? 'border-cyan-400 text-cyan-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" />
            Pengaturan & Filter (config.yaml)
          </button>
          <button
            onClick={() => setActiveTab('guide')}
            className={`px-4 py-2 font-medium border-b-2 flex items-center gap-2 transition ${
              activeTab === 'guide'
                ? 'border-cyan-400 text-cyan-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            Panduan Setup Lengkap (Langkah demi Langkah)
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Terminal output banner if run */}
        {dryRunOutput && (
          <div className="mb-6 p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Terminal className="w-3.5 h-3.5" /> Hasil Simulasi Python CLI (--dry-run)
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
            {/* Left Column: Job Feed List */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
                    Postingan Masuk ({INITIAL_JOBS.length})
                  </h2>
                </div>
                <span className="text-xs text-slate-400">Klik untuk melihat evaluasi AI</span>
              </div>

              <div className="space-y-2.5">
                {INITIAL_JOBS.map((job) => {
                  const isSelected = selectedJob.id === job.id;
                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-3.5 rounded-xl border text-left cursor-pointer transition ${
                        isSelected
                          ? 'bg-slate-800/90 border-cyan-500 shadow-md shadow-cyan-500/10'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
                          {job.source} • {job.published}
                        </span>
                        {job.filterResult.passed ? (
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
                        {job.title}
                      </h3>

                      <div className="flex flex-wrap gap-1">
                        {job.tags.map((t, idx) => (
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

              {/* Anti-spam rule note */}
              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/80 text-slate-400 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-medium text-slate-300">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                  Prinsip Aman: Zero Spam & Zero Scraping Ilegal
                </div>
                <p className="text-[11px] leading-relaxed">
                  Bot hanya membaca RSS & API publik resmi. Tidak ada bot auto-comment atau auto-DM. Anda selalu memegang kendali penuh untuk mereview dan mengirim balasan secara manual.
                </p>
              </div>
            </div>

            {/* Right Column: Telegram Live Card Preview & AI Draft */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
                    Format Notifikasi Telegram (Persis di HP)
                  </h2>
                </div>
                <span className="text-xs text-slate-400 font-mono">HTML Parse Mode</span>
              </div>

              {/* Mobile Phone Simulation Card */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl p-5 sm:p-6 space-y-5">
                {selectedJob.filterResult.passed && selectedJob.aiDraft ? (
                  <>
                    {/* Telegram Post Header */}
                    <div className="space-y-2 border-b border-slate-800/80 pb-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold text-sm border border-cyan-500/30">
                            🔔 [{selectedJob.aiDraft.relevance}/10]
                          </span>
                          <span className="text-sm font-semibold text-slate-100">
                            {selectedJob.title}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>📌 {selectedJob.source}</span>
                        <span>•</span>
                        <span>{selectedJob.published}</span>
                      </div>
                    </div>

                    {/* AI 1-Sentence Summary */}
                    <div className="space-y-1">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        Ringkasan 1 Kalimat
                      </div>
                      <p className="text-xs sm:text-sm text-slate-200 bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                        {selectedJob.aiDraft.summary}
                      </p>
                    </div>

                    {/* URL Link */}
                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/30 border border-slate-800 text-xs">
                      <span className="text-slate-400 truncate max-w-xs">
                        🔗 {selectedJob.url}
                      </span>
                      <a
                        href={selectedJob.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-medium"
                      >
                        Buka Postingan <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    {/* Draft Comment (Single-tap copy) */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
                          💬 Draft Komentar Publik (Maks 2 Kalimat)
                        </span>
                        <button
                          onClick={() => copyToClipboard(selectedJob.aiDraft?.commentDraft || '', 'comment')}
                          className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/60 px-2 py-0.5 rounded border border-cyan-800/60 transition"
                        >
                          {copiedKey === 'comment' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedKey === 'comment' ? 'Tersalin!' : 'Copy Komentar'}
                        </button>
                      </div>
                      <div
                        onClick={() => copyToClipboard(selectedJob.aiDraft?.commentDraft || '', 'comment')}
                        className="p-3 rounded-lg bg-slate-950 border border-cyan-900/40 text-cyan-200 font-mono text-xs cursor-pointer hover:border-cyan-500 transition select-all relative group"
                        title="Klik untuk menyalin"
                      >
                        <code>{selectedJob.aiDraft.commentDraft}</code>
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          Tap to copy
                        </div>
                      </div>
                    </div>

                    {/* Draft DM (Single-tap copy) */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-emerald-300 flex items-center gap-1.5">
                          ✉️ Draft Pesan Pribadi / DM (Maks 5 Kalimat)
                        </span>
                        <button
                          onClick={() => copyToClipboard(selectedJob.aiDraft?.dmDraft || '', 'dm')}
                          className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-800/60 transition"
                        >
                          {copiedKey === 'dm' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedKey === 'dm' ? 'Tersalin!' : 'Copy DM'}
                        </button>
                      </div>
                      <div
                        onClick={() => copyToClipboard(selectedJob.aiDraft?.dmDraft || '', 'dm')}
                        className="p-3.5 rounded-lg bg-slate-950 border border-emerald-900/40 text-emerald-200 font-mono text-xs leading-relaxed cursor-pointer hover:border-emerald-500 transition select-all relative group"
                        title="Klik untuk menyalin"
                      >
                        <code>{selectedJob.aiDraft.dmDraft}</code>
                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          Tap to copy
                        </div>
                      </div>
                    </div>

                    {/* Inline Telegram Keyboard Button Simulation */}
                    <div className="pt-2">
                      <a
                        href={selectedJob.url}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 font-medium text-xs flex items-center justify-center gap-1.5 border border-slate-700 transition"
                      >
                        🔗 Buka Postingan (Inline Button Telegram)
                      </a>
                    </div>
                  </>
                ) : (
                  /* Rejection Card */
                  <div className="py-12 px-4 text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
                      <AlertTriangle className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-white">
                      Postingan Ini Ditolak Oleh Filter Bertahap
                    </h3>
                    <p className="text-xs text-rose-300 max-w-md mx-auto bg-rose-950/40 p-3 rounded-lg border border-rose-900/50">
                      {selectedJob.filterResult.reason}
                    </p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Filter pre-check menghentikan proses sebelum memanggil Gemini API, sehingga <strong>kuota token harian Anda tetap hemat 100%</strong> dan Telegram Anda bebas dari spam!
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: PROFILE EDITOR */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <User className="w-5 h-5 text-cyan-400" />
                  Profil Mobile Developer (config/profile.md)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  File ini dibaca secara otomatis oleh bot dan di-inject ke dalam prompt Gemini AI agar draft balasan akurat dengan pengalaman Anda.
                </p>
              </div>
              <button
                onClick={() => copyToClipboard(`cat config/profile.md`, 'copy_profile_cmd')}
                className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700 flex items-center gap-1.5"
              >
                {copiedKey === 'copy_profile_cmd' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                Salin Perintah Baca
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Highlight Cards */}
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Smartphone className="w-4 h-4" /> Keahlian Utama (Core Tech Stack)
                  </h3>
                  <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside">
                    <li><strong className="text-white">Flutter & Dart:</strong> Bloc, Riverpod, Clean Architecture, CI/CD Fastlane.</li>
                    <li><strong className="text-white">Native Android (Kotlin):</strong> Jetpack Compose, Coroutines, Room DB, Retrofit.</li>
                    <li><strong className="text-white">React Native & Expo:</strong> TypeScript, Zustand, Reanimated, EAS updates.</li>
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCheck className="w-4 h-4" /> Proyek Unggulan yang Di-highlight AI
                  </h3>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <p className="font-semibold text-white">1. E-Commerce & Checkout Mobile App</p>
                      <p className="text-slate-400 text-[11px]">Flutter + Bloc + Supabase | 50.000+ pengguna aktif, rating 4.8</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <p className="font-semibold text-white">2. B2B Inventory & Barcode Scanner</p>
                      <p className="text-slate-400 text-[11px]">Android Kotlin + Jetpack Compose + Room DB</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <p className="font-semibold text-white">3. Social Booking Mobile Platform</p>
                      <p className="text-slate-400 text-[11px]">React Native + Expo SDK 52 + TypeScript</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Raw File Preview */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 flex flex-col">
                <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
                  <span className="font-mono text-cyan-400">config/profile.md</span>
                  <span className="text-[11px]">Otomatis diisi ke prompt `{'{PROFILE}'}`</span>
                </div>
                <div className="flex-1 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 overflow-y-auto max-h-[360px] leading-relaxed">
                  <pre>{`# Profil Pengembang Mobile
- Nama: [Nama Lengkap Anda]
- Role: Senior / Mid Mobile Developer (Flutter, Android Kotlin, React Native)
- Lokasi: Indonesia (Siap Remote Global: UTC+7 s/d US/EU overlap)
- Pengalaman: 4+ tahun mobile engineering
- Ketersediaan: Freelance / Contract / Full-time Remote

## Keahlian:
• Flutter & Dart (Bloc, Riverpod, Offline-first)
• Android Kotlin (Jetpack Compose, Coroutines)
• React Native & Expo (TypeScript, Zustand)

## Portofolio:
• GitHub: https://github.com/yourusername
• LinkedIn: https://linkedin.com/in/yourusername`}</pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: CONFIG.YAML */}
        {activeTab === 'config' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-cyan-400" />
                Konfigurasi Filter & Sumber Data (config.yaml)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Pengaturan ini mengatur kata kunci, threshold relevansi AI, dan sumber data aktif.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Box 1: Include Keywords */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
                    Include Keywords
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Wajib Ada (1+)</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['flutter', 'kotlin', 'android', 'react native', 'mobile developer', 'dart', 'expo', 'ios/android'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-cyan-950/60 border border-cyan-800/60 text-cyan-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              {/* Box 2: Hiring Keywords */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                    Hiring Intent Keywords
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Penawaran Kerja</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['hiring', 'looking for', 'need developer', 'freelance', 'contract', 'remote', 'lowongan', 'dicari'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              {/* Box 3: Exclude Keywords */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-rose-300 uppercase tracking-wider">
                    Exclude Keywords
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">Langsung Drop</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {['unpaid', 'internship', '[for hire]', 'for hire', 'looking for a job', 'magang', 'volunteer'].map((k) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-rose-950/60 border border-rose-800/60 text-rose-200 text-xs font-mono">
                      {k}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Threshold & Settings */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">
                  Relevance Threshold (Skor Min. 1-10)
                </label>
                <div className="text-xl font-bold text-white flex items-center gap-2">
                  <span>6 / 10</span>
                  <span className="text-xs font-normal text-slate-400">(Abaikan skor &lt; 6)</span>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">
                  Maksimal Panggilan Gemini per Run
                </label>
                <div className="text-xl font-bold text-cyan-400 flex items-center gap-2">
                  <span>10 panggilan</span>
                  <span className="text-xs font-normal text-slate-400">(Hemat kuota harian)</span>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">
                  Batas Umur Postingan
                </label>
                <div className="text-xl font-bold text-emerald-400 flex items-center gap-2">
                  <span>24 Jam</span>
                  <span className="text-xs font-normal text-slate-400">(Hanya yang terbaru)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: STEP-BY-STEP SETUP GUIDE */}
        {activeTab === 'guide' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                Panduan Setup Proyek Lengkap (Dari Nol Sampai Siap Jalan)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Ikuti 4 langkah mudah berikut untuk menjalankan bot di GitHub Actions dengan biaya Rp0.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Step 1 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs border border-cyan-500/30">
                    1
                  </div>
                  <h3 className="text-sm font-bold text-white">Dapatkan Gemini API Key Gratis</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Buka <strong>Google AI Studio</strong> di <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" className="text-cyan-400 underline">aistudio.google.com</a>, login dengan akun Google, klik <em>Get API key</em>, lalu <em>Create API key</em>. Free tier Gemini Flash memberikan kuota melimpah tanpa biaya.
                </p>
                <div className="p-2.5 rounded bg-slate-950 font-mono text-[11px] text-cyan-200 border border-slate-800 flex justify-between items-center">
                  <span>GEMINI_API_KEY="AIzaSy..."</span>
                  <span className="text-[10px] text-slate-500">Free Tier</span>
                </div>
              </div>

              {/* Step 2 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs border border-cyan-500/30">
                    2
                  </div>
                  <h3 className="text-sm font-bold text-white">Buat Bot Telegram & Ambil Chat ID</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  1. Cari <code>@BotFather</code> di Telegram, kirim <code>/newbot</code>, simpan <strong>HTTP API Token</strong>.<br />
                  2. Buka bot baru Anda, tekan <strong>Start</strong> (wajib agar bot bisa kirim pesan ke Anda).<br />
                  3. Buka <code>@userinfobot</code> untuk melihat ID angka Anda (simpan sebagai <code>TELEGRAM_CHAT_ID</code>).
                </p>
                <button
                  onClick={() => copyToClipboard('python main.py --test-telegram', 'test_tg')}
                  className="w-full py-1.5 px-3 rounded bg-slate-800 hover:bg-slate-700 font-mono text-xs text-slate-200 flex items-center justify-center gap-1.5 border border-slate-700"
                >
                  {copiedKey === 'test_tg' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>python main.py --test-telegram</span>
                </button>
              </div>

              {/* Step 3 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs border border-cyan-500/30">
                    3
                  </div>
                  <h3 className="text-sm font-bold text-white">Isi Secrets di GitHub Repository</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Buka repo Anda di GitHub &gt; <strong>Settings</strong> &gt; <strong>Secrets and variables</strong> &gt; <strong>Actions</strong>. Buat 4 secrets:
                </p>
                <div className="space-y-1 font-mono text-[11px] text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-cyan-300">• GEMINI_API_KEY</div>
                  <div className="text-cyan-300">• GEMINI_MODEL="gemini-3.8-flash"</div>
                  <div className="text-cyan-300">• TELEGRAM_BOT_TOKEN</div>
                  <div className="text-cyan-300">• TELEGRAM_CHAT_ID</div>
                </div>
                <p className="text-[11px] text-amber-300/80">
                  ⚠️ Di <em>Settings &gt; Actions &gt; General &gt; Workflow permissions</em>, aktifkan <strong>Read and write permissions</strong> agar `seen.json` bisa auto-commit.
                </p>
              </div>

              {/* Step 4 */}
              <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs border border-emerald-500/30">
                    4
                  </div>
                  <h3 className="text-sm font-bold text-white">Bot Berjalan Otomatis Tiap 20 Menit</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  File <code>.github/workflows/bot.yml</code> sudah terkonfigurasi. Begitu di-push ke GitHub, bot otomatis jalan tiap 20 menit via cron gratis GitHub Actions. Anda juga bisa klik <strong>Run workflow</strong> manual di tab Actions kapan saja!
                </p>
                <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-900/60 text-emerald-200 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Selesai! Tinggal pantau notifikasi lowongan masuk di Telegram HP Anda.</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 py-4 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
        <p>
          Mobile Job Opportunity Bot • 100% Free Tier Architecture (GitHub Actions + Gemini Flash + Telegram Bot API)
        </p>
      </footer>
    </div>
  );
}
