// 多語言系統
const i18n = {
    // 預設語言
    defaultLang: 'zh',
    currentLang: 'zh',
    
    // 語言包
    messages: {
        zh: {
            // 頂部導航
            'nav.language': '語言',
            'nav.logout': '登出',
            
            // Landing Page
            'landing.title': '你的 AI 教練夥伴，陪你從學習走向專業',
            'landing.subtitle': '從教練小白到執業認證，Coachly 幫你記錄、成長與實踐。',
            'landing.login_btn': '登入使用系統',
            'landing.dashboard_btn': '進入儀表板',
            'landing.welcome_back': '歡迎回來',
            
            // Dashboard
            'dashboard.title': '歡迎使用 Coachly',
            'dashboard.subtitle': 'AI 驅動的工具，提升您的教練實踐',
            'dashboard.stats.total_hours': '總教練時數',
            'dashboard.stats.monthly_hours': '本月教練時數',
            'dashboard.stats.transcripts': '轉換的逐字稿',
            'dashboard.stats.icf_competency': 'ICF 核心能力達成',
            'dashboard.getting_started': '開始使用',
            'dashboard.step1.title': '1. 上傳逐字稿',
            'dashboard.step1.desc': '上傳您教練會話的 VTT 或 SRT 逐字稿檔案。',
            'dashboard.step2.title': '2. 設定選項',
            'dashboard.step2.desc': '設定教練和客戶名稱以進行匿名化處理及其他偏好設定。',
            'dashboard.step3.title': '3. 下載 Excel',
            'dashboard.step3.desc': '獲得結構化的 Excel 檔案，準備進行分析和檢視。',
            
            // Sidebar Menu
            'menu.dashboard': '儀表板',
            'menu.converter': '逐字稿轉換',
            'menu.analysis': '標記分析',
            'menu.insights': 'AI 洞見',
            'menu.profile': '個人檔案',
            'menu.feedback': '意見回饋',
            'menu.coming_soon': '即將推出',
            'menu.account': '帳戶設定',
            'menu.theme': '主題',
            'menu.language': '語言',
            
            // Help Menu
            'help.systems_operational': '所有系統正常運作',
            'help.get_help': '取得協助',
            'help.community_hub': '社群中心',
            'help.view_updates': '查看更新',
            'help.read_docs': '閱讀文檔',
            
            // Transcript Converter
            'converter.title': '上傳逐字稿產生 Excel',
            'converter.subtitle': '支援 .vtt 或 .srt 格式檔案',
            'converter.upload_text': '將你的逐字稿檔案拖曳到此處',
            'converter.upload_subtext': '或點擊以瀏覽檔案',
            'converter.file_info': '支援格式: .vtt, .srt (檔案上限: 10MB)',
            'converter.coach_name': '教練名稱 (選填):',
            'converter.coach_placeholder': '輸入教練在逐字稿中的名稱',
            'converter.client_name': '客戶名稱 (選填):',
            'converter.client_placeholder': '輸入客戶在逐字稿中的名稱',
            'converter.convert_chinese': '將內容簡體轉繁體',
            'converter.start_btn': '開始轉換',
            'converter.processing': '正在處理您的逐字稿...',
            'converter.processing_desc': '請稍候，我們正在轉換您的檔案...',
            'converter.success': '轉換成功！',
            'converter.download_btn': '下載 Excel',
            
            // Feature Cards
            'feature.converter.title': '逐字稿轉換器',
            'feature.converter.desc': '將您的教練會話逐字稿從 VTT 或 SRT 格式轉換為結構化的 Excel 檔案進行分析。',
            'feature.converter.btn': '上傳逐字稿',
            'feature.analysis.title': 'ICF 標記分析',
            'feature.analysis.desc': '自動識別和分析您會話中的 ICF 教練能力和標記。',
            'feature.insights.title': 'AI 洞見',
            'feature.insights.desc': '獲得 AI 驅動的洞見和建議，提升您的教練效能。',
            
            // Coming Soon
            'coming_soon.message': '🚧 此功能即將推出，敬請期待！',
            
            // Landing Page Sections
            'landing.who_its_for': '適用對象',
            'landing.learner.title': '教練學習者',
            'landing.learner.desc': '正在接受教練培訓，需要工具來分析和反思自己的教練對話，以滿足認證時數要求。',
            'landing.professional.title': '專業執業教練',
            'landing.professional.desc': '希望提高效率，將逐字稿整理工作自動化，並從客戶對話中獲得更深層次的洞見。',
            'landing.supervisor.title': '教練督導與培訓師',
            'landing.supervisor.desc': '需要一個統一的平台來審閱學員的教練稿件，提供基於數據的回饋。',
            'landing.features': '主要功能',
            'landing.transcript.title': '逐字稿轉換器',
            'landing.transcript.desc': '快速將 VTT/SRT 格式的錄音逐字稿轉換為結構化的 Excel 表格，自動標記發言者和時間戳。',
            'landing.analysis.title': 'ICF 核心能力分析',
            'landing.analysis.desc': '（即將推出）自動分析對話中的 ICF 核心能力指標，幫助你準備 ACC/PCC 認證。',
            'landing.insights.title': 'AI 教練洞見',
            'landing.insights.desc': '（即將推出）利用 AI 分析你的提問模式、語言習慣和客戶反應，提供個人化的成長建議。',
            'landing.pricing': '收費與方案',
            'landing.free.title': 'Free',
            'landing.pro.title': 'Pro',
            'landing.pro.month': '/月',
            'landing.coming_soon_desc': '我們正努力開發更多強大功能，包括團隊協作、客戶管理和進階報告，敬請期待！',
            'landing.pricing.free': 'Free',
            'landing.pricing.pro': 'Pro',
            'landing.pricing.free.feature1': '每月 3 次逐字稿轉換',
            'landing.pricing.free.feature2': '基本分析功能',
            'landing.pricing.free.feature3': '社群支援',
            'landing.pricing.pro.feature1': '無限次逐字稿轉換',
            'landing.pricing.pro.feature2': '完整 ICF 核心能力分析',
            'landing.pricing.pro.feature3': 'AI 教練洞見報告',
            'landing.pricing.pro.feature4': '優先 Email 支援',
            'landing.coming_soon': '即將推出',
            'landing.coming_soon.desc': '我們正努力開發更多強大功能，包括團隊協作、客戶管理和進階報告，敬請期待！'
        },
        
        en: {
            // 頂部導航
            'nav.language': 'Language',
            'nav.logout': 'Logout',
            
            // Landing Page
            'landing.title': 'Your AI-powered coaching companion',
            'landing.subtitle': 'From student to certified coach, Coachly helps you track, grow, and thrive.',
            'landing.login_btn': 'Login to System',
            'landing.dashboard_btn': 'Go to Dashboard',
            'landing.welcome_back': 'Welcome back',
            
            // Dashboard
            'dashboard.title': 'Welcome to Coachly',
            'dashboard.subtitle': 'AI-powered tools to enhance your coaching practice',
            'dashboard.stats.total_hours': 'Total Coaching Hours',
            'dashboard.stats.monthly_hours': 'Monthly Hours',
            'dashboard.stats.transcripts': 'Converted Transcripts',
            'dashboard.stats.icf_competency': 'ICF Competency Achievement',
            'dashboard.getting_started': 'Getting Started',
            'dashboard.step1.title': '1. Upload Transcript',
            'dashboard.step1.desc': 'Upload your VTT or SRT transcript file from your coaching session.',
            'dashboard.step2.title': '2. Configure Options',
            'dashboard.step2.desc': 'Set coach and client names for anonymization and other preferences.',
            'dashboard.step3.title': '3. Download Excel',
            'dashboard.step3.desc': 'Get your structured Excel file ready for analysis and review.',
            
            // Sidebar Menu
            'menu.dashboard': 'Dashboard',
            'menu.converter': 'Converter',
            'menu.analysis': 'Analysis',
            'menu.insights': 'Insights',
            'menu.profile': 'Profile',
            'menu.feedback': 'Feedback',
            'menu.coming_soon': 'Coming Soon',
            'menu.account': 'Account',
            'menu.theme': 'Theme',
            'menu.language': 'Language',
            
            // Help Menu
            'help.systems_operational': 'All systems operational',
            'help.get_help': 'Get help',
            'help.community_hub': 'Community Hub',
            'help.view_updates': 'View updates',
            'help.read_docs': 'Read the docs',
            
            // Transcript Converter
            'converter.title': 'Upload Transcript to Generate Excel',
            'converter.subtitle': 'Supports .vtt or .srt format files',
            'converter.upload_text': 'Drag your transcript file here',
            'converter.upload_subtext': 'or click to browse files',
            'converter.file_info': 'Supported formats: .vtt, .srt (File limit: 10MB)',
            'converter.coach_name': 'Coach Name (Optional):',
            'converter.coach_placeholder': 'Enter coach name in transcript',
            'converter.client_name': 'Client Name (Optional):',
            'converter.client_placeholder': 'Enter client name in transcript',
            'converter.convert_chinese': 'Convert Simplified to Traditional Chinese',
            'converter.start_btn': 'Start Conversion',
            'converter.processing': 'Processing your transcript...',
            'converter.processing_desc': 'Please wait, we are converting your file...',
            'converter.success': 'Conversion successful!',
            'converter.download_btn': 'Download Excel',
            
            // Feature Cards
            'feature.converter.title': 'Transcript Converter',
            'feature.converter.desc': 'Convert your coaching session transcripts from VTT or SRT format to structured Excel files for analysis.',
            'feature.converter.btn': 'Upload Transcript',
            'feature.analysis.title': 'ICF Marker Analysis',
            'feature.analysis.desc': 'Automatically identify and analyze ICF coaching competencies and markers in your sessions.',
            'feature.insights.title': 'AI Insights',
            'feature.insights.desc': 'Get AI-powered insights and suggestions to improve your coaching effectiveness.',
            
            // Coming Soon
            'coming_soon.message': '🚧 This feature is coming soon. Stay tuned!',
            
            // Landing Page Sections
            'landing.who_its_for': 'Who It\'s For',
            'landing.learner.title': 'Coach Learners',
            'landing.learner.desc': 'Currently undergoing coach training, needing tools to analyze and reflect on coaching conversations to meet certification hour requirements.',
            'landing.professional.title': 'Professional Coaches',
            'landing.professional.desc': 'Looking to improve efficiency by automating transcript organization and gaining deeper insights from client conversations.',
            'landing.supervisor.title': 'Coach Supervisors & Trainers',
            'landing.supervisor.desc': 'Needing a unified platform to review student coaching transcripts and provide data-driven feedback.',
            'landing.features': 'Key Features',
            'landing.transcript.title': 'Transcript Converter',
            'landing.transcript.desc': 'Quickly convert VTT/SRT format audio transcripts into structured Excel tables, automatically marking speakers and timestamps.',
            'landing.analysis.title': 'ICF Core Competency Analysis',
            'landing.analysis.desc': '(Coming Soon) Automatically analyze ICF core competency indicators in conversations to help you prepare for ACC/PCC certification.',
            'landing.insights.title': 'AI Coach Insights',
            'landing.insights.desc': '(Coming Soon) Use AI to analyze your questioning patterns, language habits, and client responses, providing personalized growth recommendations.',
            'landing.pricing': 'Pricing & Plans',
            'landing.free.title': 'Free',
            'landing.pro.title': 'Pro',
            'landing.pro.month': '/month',
            'landing.coming_soon_desc': 'We are working hard to develop more powerful features, including team collaboration, client management, and advanced reporting. Stay tuned!',
            'landing.pricing.free': 'Free',
            'landing.pricing.pro': 'Pro',
            'landing.pricing.free.feature1': '3 transcript conversions per month',
            'landing.pricing.free.feature2': 'Basic analysis features',
            'landing.pricing.free.feature3': 'Community support',
            'landing.pricing.pro.feature1': 'Unlimited transcript conversions',
            'landing.pricing.pro.feature2': 'Complete ICF core competency analysis',
            'landing.pricing.pro.feature3': 'AI coach insight reports',
            'landing.pricing.pro.feature4': 'Priority email support',
            'landing.coming_soon': 'Coming Soon',
            'landing.coming_soon.desc': 'We are working hard to develop more powerful features, including team collaboration, client management, and advanced reporting. Stay tuned!'
        }
    },
    
    // 初始化
    init() {
        const savedLang = localStorage.getItem('language') || this.defaultLang;
        this.setLanguage(savedLang);
        this.attachEventListeners();
    },
    
    // 設定語言
    setLanguage(lang) {
        if (!this.messages[lang]) {
            lang = this.defaultLang;
        }
        
        this.currentLang = lang;
        localStorage.setItem('language', lang);
        this.updateUI();
        this.updateLanguageSwitcher();
    },
    
    // 獲取翻譯文字
    t(key) {
        return this.messages[this.currentLang][key] || this.messages[this.defaultLang][key] || key;
    },
    
    // 更新UI文字
    updateUI() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
    },
    
    // 更新語言切換器
    updateLanguageSwitcher() {
        const zhBtn = document.getElementById('lang-zh');
        const enBtn = document.getElementById('lang-en');
        
        if (zhBtn && enBtn) {
            zhBtn.classList.toggle('active', this.currentLang === 'zh');
            enBtn.classList.toggle('active', this.currentLang === 'en');
        }
    },
    
    // 綁定事件監聽器
    attachEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.id === 'lang-zh') {
                this.setLanguage('zh');
            } else if (e.target.id === 'lang-en') {
                this.setLanguage('en');
            }
        });
    }
};

// 頁面載入後初始化
document.addEventListener('DOMContentLoaded', () => {
    i18n.init();
});

// 全域暴露
window.i18n = i18n;
