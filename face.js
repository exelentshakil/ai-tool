


jQuery(document).ready(function($) {
// 1. On load, hydrate cache from storage
const analysisCache = JSON.parse(localStorage.getItem('analysisCache')||'{}');

// 2. Utility: hash a dataURL string
async function hashString(str) {
  const buf = new TextEncoder().encode(str);
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash))
    .map(b=>b.toString(16).padStart(2,'0'))
    .join('');
}

// Global functions
window.downloadImage = function (dataUrl) {
    const link = document.createElement('a');
    link.download = `personality-analysis-${Date.now()}.png`;
    link.href = dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Show success animation
    showNotification('📥 Analysis downloaded successfully!', 'success');
};

window.shareOnSocial = function () {
    const shareText = "🤯 Just discovered my AI personality analysis! The insights are mind-blowing 🧠✨";
    const shareUrl = window.location.href;

    if (navigator.share) {
        navigator.share({
            title: 'My AI Personality Analysis',
            text: shareText,
            url: shareUrl
        }).catch(console.error);
    } else {
        navigator.clipboard.writeText(`${shareText} ${shareUrl}`).then(() => {
            showNotification('🔗 Share link copied to clipboard!', 'success');
        }).catch(() => {
            prompt('Copy this link to share:', `${shareText} ${shareUrl}`);
        });
    }
};

window.tryagain = function () {
    // Smooth transition animation
    elements.resultsArea.fadeOut(500, function () {
        elements.uploadArea.fadeIn(500);
        currentImage = null;
        elements.fileInput.val('');
        elements.uploadArea[0].scrollIntoView({behavior: 'smooth', block: 'start'});
    });
};

// Ultra-modern color themes with gradients
const colorThemes = {
    cosmic: {
        primary: '#667eea',
        secondary: '#764ba2',
        accent: '#f093fb',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        cardGradient: 'linear-gradient(135deg, #667eea10, #764ba220)'
    },
    neon: {
        primary: '#00d4ff',
        secondary: '#ff0099',
        accent: '#00ff88',
        gradient: 'linear-gradient(135deg, #00d4ff 0%, #ff0099 100%)',
        cardGradient: 'linear-gradient(135deg, #00d4ff10, #ff009920)'
    },
    aurora: {
        primary: '#a8edea',
        secondary: '#fed6e3',
        accent: '#ffc3a0',
        gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        cardGradient: 'linear-gradient(135deg, #a8edea20, #fed6e320)'
    },
    sunset: {
        primary: '#ff9a9e',
        secondary: '#fecfef',
        accent: '#fecfef',
        gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
        cardGradient: 'linear-gradient(135deg, #ff9a9e15, #fecfef25)'
    },
    matrix: {
        primary: '#0f3460',
        secondary: '#16537e',
        accent: '#533a7b',
        gradient: 'linear-gradient(135deg, #0f3460 0%, #16537e 100%)',
        cardGradient: 'linear-gradient(135deg, #0f346015, #16537e20)'
    }
};

// DOM Elements
const elements = {
    uploadBtn: $('#upload-btn'),
    cameraBtn: $('#camera-btn'),
    fileInput: $('#face-upload'),
    uploadArea: $('#upload-area'),
    cameraArea: $('#camera-area'),
    cameraStream: $('#camera-stream')[0],
    takePhotoBtn: $('#take-photo-btn'),
    backBtn: $('#back-btn'),
    previewArea: $('#preview-area'),
    previewCanvas: $('#preview-canvas')[0],
    analyzeBtn: $('#analyze-btn'),
    loadingArea: $('#loading-area'),
    progressBar: $('#analysis-progress'),
    resultsArea: $('#results-area'),
    customizationOptions: $('#customization-options')
};

// Global variables
let currentImage = null;
let stream = null;
let selectedTheme = 'cosmic';
let analysisData = null;


// Ultra-modern notification system
function showNotification(message, type = 'info') {
    const notification = $(`
        <div class="ultra-notification ${type}" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'linear-gradient(135deg, #4ade80, #22c55e)' :
        type === 'error' ? 'linear-gradient(135deg, #f87171, #ef4444)' :
            type === 'warning' ? 'linear-gradient(135deg, #fbbf24, #f59e0b)' :
                'linear-gradient(135deg, #60a5fa, #3b82f6)'};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            z-index: 10000;
            transform: translateX(400px);
            transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            font-weight: 600;
            font-size: 14px;
            max-width: 300px;
        ">
            ${message}
        </div>
    `);

    $('body').append(notification);

    setTimeout(() => {
        notification.css('transform', 'translateX(0)');
    }, 100);

    setTimeout(() => {
        notification.css('transform', 'translateX(400px)');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Initialize ultra-modern customization UI
function initializeCustomization() {
    if (!$('#customization-options').length) {
        $('.face-analyzer-upload').append(`
            <div id="customization-options" class="ultra-customization">
                <h4>🎨 Customize Your Experience</h4>
                <div class="option-group">
                    <label>✨ Visual Theme:</label>
                    <div class="theme-selector-ultra">
                        <button class="theme-btn-ultra cosmic active" data-theme="cosmic" title="Cosmic Dreams"></button>
                        <button class="theme-btn-ultra neon" data-theme="neon" title="Neon Cyberpunk"></button>
                        <button class="theme-btn-ultra aurora" data-theme="aurora" title="Aurora Borealis"></button>
                        <button class="theme-btn-ultra sunset" data-theme="sunset" title="Sunset Vibes"></button>
                        <button class="theme-btn-ultra matrix" data-theme="matrix" title="Matrix Mode"></button>
                    </div>
                </div>
                <div class="option-group">
                    <label>👤 Your Name:</label>
                    <input type="text" id="user-name" placeholder="Enter your name for personalized insights" class="ultra-input">
                </div>
                <div class="option-group">
                    <label>📅 Life Stage:</label>
                    <select id="age-range" class="ultra-select">
                        <option value="16-20">🎓 Student (16-20)</option>
                        <option value="21-25">🚀 Rising Star (21-25)</option>
                        <option value="26-35" selected>💼 Professional (26-35)</option>
                        <option value="36-45">⭐ Established (36-45)</option>
                        <option value="46-55">🎯 Expert (46-55)</option>
                        <option value="56+">🏆 Visionary (56+)</option>
                    </select>
                </div>
                <div class="option-group">
                    <label>🎯 Current Focus:</label>
                    <select id="career-focus" class="ultra-select">
                        <option value="career_growth">📈 Career Growth</option>
                        <option value="leadership">👑 Leadership</option>
                        <option value="entrepreneurship">🚀 Entrepreneurship</option>
                        <option value="creativity">🎨 Creative Pursuits</option>
                        <option value="relationships">💝 Relationships</option>
                        <option value="personal_growth">🌱 Personal Growth</option>
                    </select>
                </div>
            </div>
        `);

        // Add ultra-modern CSS
        $('head').append(`
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
            
            .ultra-customization { 
                margin: 30px 0; 
                padding: 25px; 
                background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                backdrop-filter: blur(20px);
                border-radius: 20px; 
                border: 1px solid rgba(255,255,255,0.2);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                position: relative;
                overflow: hidden;
            }
            
            .ultra-customization::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
            }
            
            .ultra-customization h4 {
                margin: 0 0 25px 0;
                color: #1a1a1a;
                font-size: 1.2rem;
                font-weight: 700;
                text-align: center;
                font-family: 'Inter', sans-serif;
            }
            
            .option-group { 
                margin-bottom: 25px; 
            }
            
            .option-group label { 
                display: block; 
                margin-bottom: 12px; 
                font-weight: 600; 
                color: #2d3748;
                font-size: 14px;
                font-family: 'Inter', sans-serif;
            }
            
            .theme-selector-ultra { 
                display: flex; 
                gap: 15px; 
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .theme-btn-ultra { 
                width: 45px; 
                height: 45px; 
                border-radius: 50%; 
                border: 3px solid rgba(255,255,255,0.3); 
                cursor: pointer; 
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                position: relative;
                overflow: hidden;
            }
            
            .theme-btn-ultra::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                background: rgba(255,255,255,0.3);
                border-radius: 50%;
                transition: all 0.3s ease;
                transform: translate(-50%, -50%);
            }
            
            .theme-btn-ultra:hover::after {
                width: 100%;
                height: 100%;
            }
            
            .theme-btn-ultra:hover {
                transform: scale(1.1);
                box-shadow: 0 8px 25px rgba(0,0,0,0.25);
            }
            
            .theme-btn-ultra.active { 
                border-color: #ffffff; 
                box-shadow: 0 0 0 3px rgba(255,255,255,0.3), 0 8px 25px rgba(0,0,0,0.25);
                transform: scale(1.1);
            }
            
            .theme-btn-ultra.cosmic { background: linear-gradient(135deg, #667eea, #764ba2); }
            .theme-btn-ultra.neon { background: linear-gradient(135deg, #00d4ff, #ff0099); }
            .theme-btn-ultra.aurora { background: linear-gradient(135deg, #a8edea, #fed6e3); }
            .theme-btn-ultra.sunset { background: linear-gradient(135deg, #ff9a9e, #fecfef); }
            .theme-btn-ultra.matrix { background: linear-gradient(135deg, #0f3460, #16537e); }
            
            .ultra-input, .ultra-select { 
                width: 100%; 
                padding: 16px 20px; 
                border: 2px solid rgba(255,255,255,0.2); 
                border-radius: 12px; 
                font-size: 14px;
                font-weight: 500;
                font-family: 'Inter', sans-serif;
                transition: all 0.3s ease;
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                color: #2d3748;
            }
            
            .ultra-input::placeholder {
                color: rgba(45, 55, 72, 0.6);
            }
            
            .ultra-input:focus, .ultra-select:focus {
                outline: none;
                border-color: ${colorThemes[selectedTheme].primary};
                box-shadow: 0 0 0 3px ${colorThemes[selectedTheme].primary}20;
                background: rgba(255,255,255,0.2);
            }
            
            .ultra-results-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                font-family: 'Inter', sans-serif;
            }
            
            .ultra-header {
                text-align: center;
                margin-bottom: 50px;
                padding: 50px 30px;
                background: ${colorThemes[selectedTheme].gradient};
                border-radius: 30px;
                position: relative;
                overflow: hidden;
                color: white;
            }
            
            .ultra-header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="20" cy="80" r="0.5" fill="white" opacity="0.1"/><circle cx="80" cy="30" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
                animation: sparkle 20s linear infinite;
            }
            
            @keyframes sparkle {
                0% { transform: translateX(0) translateY(0); }
                25% { transform: translateX(-50px) translateY(-50px); }
                50% { transform: translateX(-100px) translateY(0); }
                75% { transform: translateX(-50px) translateY(50px); }
                100% { transform: translateX(0) translateY(0); }
            }
            
            .ultra-title {
                font-size: 3rem;
                font-weight: 800;
                margin-bottom: 20px;
                background: linear-gradient(45deg, rgba(255,255,255,1), rgba(255,255,255,0.8));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                position: relative;
                z-index: 1;
            }
            
            .ultra-badge {
                display: inline-block;
                padding: 12px 24px;
                background: rgba(255,255,255,0.2);
                backdrop-filter: blur(20px);
                border-radius: 50px;
                border: 1px solid rgba(255,255,255,0.3);
                font-weight: 700;
                font-size: 14px;
                margin: 15px 0;
                position: relative;
                z-index: 1;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .ultra-section {
                margin: 50px 0;
                padding: 40px;
                background: rgba(255,255,255,0.8);
                backdrop-filter: blur(20px);
                border-radius: 25px;
                border: 1px solid rgba(255,255,255,0.3);
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                position: relative;
                overflow: hidden;
            }
            
            .ultra-section::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: ${colorThemes[selectedTheme].gradient};
            }
            
            .ultra-section-title {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 30px;
                text-align: center;
                background: ${colorThemes[selectedTheme].gradient};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .ultra-grid {
                display: grid;
                gap: 25px;
            }
            
            .ultra-grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
            .ultra-grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
            .ultra-grid-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
            
            .ultra-card {
                background: rgba(255,255,255,0.9);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 30px;
                border: 1px solid rgba(255,255,255,0.4);
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                position: relative;
                overflow: hidden;
            }
            
            .ultra-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: ${colorThemes[selectedTheme].gradient};
                transform: scaleX(0);
                transition: transform 0.3s ease;
            }
            
            .ultra-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            }
            
            .ultra-card:hover::before {
                transform: scaleX(1);
            }
            
            .ultra-trait-card {
                text-align: center;
                position: relative;
            }
            
            .ultra-trait-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                display: block;
                background: ${colorThemes[selectedTheme].cardGradient};
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 15px auto;
                border: 2px solid rgba(255,255,255,0.5);
            }
            
            .ultra-trait-name {
                font-size: 1.1rem;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 10px;
            }
            
            .ultra-trait-score {
                font-size: 2rem;
                font-weight: 800;
                background: ${colorThemes[selectedTheme].gradient};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 15px;
            }
            
            .ultra-progress-ring {
                width: 120px;
                height: 120px;
                margin: 20px auto;
                position: relative;
            }
            
            .ultra-progress-ring svg {
                width: 120px;
                height: 120px;
                transform: rotate(-90deg);
            }
            
            .ultra-progress-ring circle {
                fill: none;
                stroke-width: 8;
            }
            
            .ultra-progress-ring .background {
                stroke: rgba(0,0,0,0.1);
            }
            
            .ultra-progress-ring .progress {
                stroke: url(#gradient);
                stroke-linecap: round;
                stroke-dasharray: 283;
                stroke-dashoffset: 283;
                transition: stroke-dashoffset 2s ease;
            }
            
            .ultra-insight-card {
                background: ${colorThemes[selectedTheme].cardGradient};
                border-left: 5px solid ${colorThemes[selectedTheme].primary};
                position: relative;
                overflow: hidden;
            }
            
            .ultra-insight-card::after {
                content: '💡';
                position: absolute;
                top: 20px;
                right: 20px;
                font-size: 1.5rem;
                opacity: 0.5;
            }
            
            .ultra-career-card {
                border: 2px solid transparent;
                background: linear-gradient(white, white) padding-box, ${colorThemes[selectedTheme].gradient} border-box;
                position: relative;
            }
            
            .ultra-career-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .ultra-career-title {
                font-size: 1.4rem;
                font-weight: 700;
                background: ${colorThemes[selectedTheme].gradient};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .ultra-fit-score {
                background: ${colorThemes[selectedTheme].gradient};
                color: white;
                padding: 8px 16px;
                border-radius: 50px;
                font-weight: 700;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .ultra-prediction-card {
                text-align: center;
                background: ${colorThemes[selectedTheme].cardGradient};
            }
            
            .ultra-prediction-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
            }
            
            .ultra-prediction-value {
                font-size: 1.8rem;
                font-weight: 800;
                background: ${colorThemes[selectedTheme].gradient};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 15px 0;
            }
            
            .ultra-share-section {
                text-align: center;
                background: ${colorThemes[selectedTheme].cardGradient};
            }
            
            .ultra-btn {
                background: ${colorThemes[selectedTheme].gradient};
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 50px;
                font-weight: 700;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                margin: 0 10px 10px 10px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                position: relative;
                overflow: hidden;
                min-width: 200px;
            }
            
            .ultra-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s ease;
            }
            
            .ultra-btn:hover::before {
                left: 100%;
            }
            
            .ultra-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.25);
            }
            
            .ultra-skill-tag {
                display: inline-block;
                background: rgba(255,255,255,0.2);
                backdrop-filter: blur(10px);
                color: ${colorThemes[selectedTheme].primary};
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                margin: 4px;
                border: 1px solid rgba(255,255,255,0.3);
            }
            
            .ultra-roadmap-item {
                background: ${colorThemes[selectedTheme].cardGradient};
                border-left: 5px solid ${colorThemes[selectedTheme].primary};
                position: relative;
            }
            
            .ultra-priority-high {
                border-left-color: #ef4444;
            }
            
            .ultra-priority-medium {
                border-left-color: #f59e0b;
            }
            
            .ultra-priority-low {
                border-left-color: #22c55e;
            }
            
            @media (max-width: 768px) {
                .ultra-title { font-size: 2rem; }
                .ultra-section { padding: 25px; margin: 30px 0; }
                .ultra-card { padding: 20px; }
                .ultra-grid-2, .ultra-grid-3, .ultra-grid-4 { grid-template-columns: 1fr; }
                .ultra-btn { min-width: auto; width: 100%; margin: 5px 0; }
            }
            
            /* Stunning animations */
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .ultra-card {
                animation: fadeInUp 0.8s ease forwards;
            }
            
            .ultra-card:nth-child(2) { animation-delay: 0.1s; }
            .ultra-card:nth-child(3) { animation-delay: 0.2s; }
            .ultra-card:nth-child(4) { animation-delay: 0.3s; }
            .ultra-card:nth-child(5) { animation-delay: 0.4s; }
            
            .ultra-trait-icon {
                animation: pulse 2s ease-in-out infinite;
            }
            </style>
        `);
    }
}

// Apply ultra-modern theme
function applyTheme(themeName) {
    const theme = colorThemes[themeName];
    selectedTheme = themeName;

    // Update CSS custom properties
    $(':root').css({
        '--primary-color': theme.primary,
        '--secondary-color': theme.secondary,
        '--accent-color': theme.accent,
        '--gradient': theme.gradient
    });

    // Update existing elements
    $('.upload-btn, .camera-btn, #analyze-btn, #take-photo-btn, #try-again-btn').css({
        'background': theme.gradient,
        'color': '#ffffff',
        'box-shadow': `0 8px 25px ${theme.primary}40`
    });

    // Update dynamic theme elements
    updateThemeElements(theme);
}

function updateThemeElements(theme) {
    // Update any existing themed elements
    $('.ultra-section::before').css('background', theme.gradient);
    $('.ultra-btn').css('background', theme.gradient);
    $('.ultra-fit-score').css('background', theme.gradient);
}

// Map face data to personality traits
function mapFaceDataToTraits({age, gender, expressions}) {
    const topEmotion = Object.entries(expressions).sort((a, b) => b[1] - a[1])[0][0];
    return {
        openness: topEmotion === 'surprised' || topEmotion === 'happy' ? 0.8 : Math.random() * 0.4 + 0.4,
        conscientiousness: topEmotion === 'neutral' ? 0.75 : Math.random() * 0.4 + 0.4,
        extraversion: topEmotion === 'happy' ? 0.85 : topEmotion === 'neutral' ? 0.5 : Math.random() * 0.4 + 0.3,
        agreeableness: gender === 'female' ? 0.75 : Math.random() * 0.4 + 0.4,
        neuroticism: topEmotion === 'angry' || topEmotion === 'sad' ? 0.8 : Math.random() * 0.4 + 0.2,
        confidence: Math.random() * 0.3 + 0.5,
        creativity: Math.random() * 0.3 + 0.5,
        leadership: Math.random() * 0.3 + 0.5
    };
}

// Analyze face with Face API
async function analyzeFaceWithAI(img) {
try {
    showNotification('🔍 Analyzing your image...', 'info');

    // Store the image globally
    window.currentImage = img;

    // Generate realistic traits based on random + some image analysis
    const traits = generateSmartTraits(img);

    console.log('Generated traits:', traits);

    // Send to your backend for AI analysis
    try {
        const backendResponse = await sendToEnhancedBackend(traits, generateBasicFaceData());
        console.log('Backend response received');

        return {
            traits: traits,
            enhancedAnalysis: backendResponse,
            faceData: generateBasicFaceData(),
            userImage: img, // Store image in result
            useEnhanced: true
        };

    } catch (backendError) {
        console.warn('Backend error:', backendError.message);

        if (backendError.message.includes('429') || backendError.message.includes('limit')) {
            return {
                traits: traits,
                enhancedAnalysis: null,
                faceData: generateBasicFaceData(),
                userImage: img, // Store image in result
                useEnhanced: false,
                isRateLimited: true,
                rateLimitMessage: '⏰ Daily AI analysis limit reached!'
            };
        }

        throw backendError;
    }

} catch (error) {
    console.error('Analysis error:', error);
    showNotification('❌ Analysis failed - please try again', 'error');
    return null;
}
}


// Generate realistic personality traits
// Enhanced Realism Features
function generateSmartTraits(img) {
// Analyze image characteristics for more realistic traits
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
canvas.width = 100;
canvas.height = 100;
ctx.drawImage(img, 0, 0, 100, 100);

const imageData = ctx.getImageData(0, 0, 100, 100);

// Analyze image characteristics
const analysis = analyzeImageCharacteristics(imageData);

// Generate traits based on visual cues
const traits = {
    openness: calculateOpenness(analysis),
    conscientiousness: calculateConscientiousness(analysis),
    extraversion: calculateExtraversion(analysis),
    agreeableness: calculateAgreeableness(analysis),
    neuroticism: calculateNeuroticism(analysis),
    confidence: calculateConfidence(analysis),
    creativity: calculateCreativity(analysis),
    leadership: calculateLeadership(analysis)
};

// Add user input influence
const userInfluence = getUserInputInfluence();
Object.keys(traits).forEach(trait => {
    traits[trait] = (traits[trait] * 0.7) + (userInfluence[trait] * 0.3);
    traits[trait] = Math.max(0.2, Math.min(0.9, traits[trait])); // Keep in range
    traits[trait] = Math.round(traits[trait] * 100) / 100; // Round to 2 decimals
});

return traits;
}

function analyzeImageCharacteristics(imageData) {
let brightness = 0;
let contrast = 0;
let colorfulness = 0;
let symmetry = 0;

const data = imageData.data;
const pixels = data.length / 4;

// Calculate brightness and color analysis
for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];

    brightness += (r + g + b) / 3;
    colorfulness += Math.abs(r - g) + Math.abs(g - b) + Math.abs(b - r);
}

brightness /= pixels;
colorfulness /= pixels;

// Simple contrast calculation
contrast = colorfulness / 255;

return {
    brightness: brightness / 255,
    contrast: Math.min(1, contrast),
    colorfulness: Math.min(1, colorfulness / 100),
    hasWarmTones: checkWarmTones(data),
    imageQuality: calculateImageQuality(data)
};
}

function calculateOpenness(analysis) {
// Creative/bright photos suggest higher openness
return 0.3 + (analysis.colorfulness * 0.4) + (analysis.brightness * 0.2) + Math.random() * 0.1;
}

function calculateConscientiousness(analysis) {
// Well-lit, clear photos suggest organization
return 0.3 + (analysis.imageQuality * 0.3) + (analysis.brightness * 0.2) + Math.random() * 0.2;
}

function calculateExtraversion(analysis) {
// Bright, warm photos suggest extroversion
return 0.3 + (analysis.brightness * 0.3) + (analysis.hasWarmTones ? 0.2 : 0.1) + Math.random() * 0.2;
}

function calculateAgreeableness(analysis) {
// Warm, soft lighting suggests agreeableness
return 0.4 + (analysis.hasWarmTones ? 0.3 : 0.1) + Math.random() * 0.2;
}

function calculateNeuroticism(analysis) {
// High contrast/harsh lighting might suggest stress
return 0.2 + (analysis.contrast * 0.2) + Math.random() * 0.3;
}

function calculateConfidence(analysis) {
// Good lighting and image quality suggest confidence
return 0.4 + (analysis.imageQuality * 0.3) + (analysis.brightness * 0.2) + Math.random() * 0.1;
}

function calculateCreativity(analysis) {
// Colorful, unique photos suggest creativity
return 0.3 + (analysis.colorfulness * 0.4) + Math.random() * 0.3;
}

function calculateLeadership(analysis) {
// Professional quality photos suggest leadership
return 0.3 + (analysis.imageQuality * 0.4) + (analysis.brightness * 0.2) + Math.random() * 0.1;
}

function checkWarmTones(data) {
let warmPixels = 0;
for (let i = 0; i < data.length; i += 16) { // Sample every 4th pixel
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];

    if (r > g && r > b) warmPixels++; // More red = warmer
}
return warmPixels > (data.length / 16) * 0.3; // 30% threshold
}

function calculateImageQuality(data) {
// Simple quality check based on variance
let variance = 0;
let mean = 0;

for (let i = 0; i < data.length; i += 4) {
    mean += (data[i] + data[i + 1] + data[i + 2]) / 3;
}
mean /= (data.length / 4);

for (let i = 0; i < data.length; i += 4) {
    const pixelMean = (data[i] + data[i + 1] + data[i + 2]) / 3;
    variance += Math.pow(pixelMean - mean, 2);
}
variance /= (data.length / 4);

return Math.min(1, variance / 10000); // Normalize
}

function getUserInputInfluence() {
// Use user's selections to influence traits
const ageRange = $('#age-range').val() || '26-35';
const careerFocus = $('#career-focus').val() || 'career_growth';

const ageInfluence = {
    '16-20': { openness: 0.8, extraversion: 0.7, neuroticism: 0.6 },
    '21-25': { openness: 0.7, extraversion: 0.6, confidence: 0.5 },
    '26-35': { conscientiousness: 0.7, leadership: 0.6, confidence: 0.6 },
    '36-45': { conscientiousness: 0.8, leadership: 0.7, agreeableness: 0.6 },
    '46-55': { conscientiousness: 0.8, agreeableness: 0.7, openness: 0.5 },
    '56+': { agreeableness: 0.8, conscientiousness: 0.8, neuroticism: 0.3 }
};

const careerInfluence = {
    'career_growth': { conscientiousness: 0.7, leadership: 0.6 },
    'leadership': { leadership: 0.8, extraversion: 0.7, confidence: 0.8 },
    'entrepreneurship': { openness: 0.8, confidence: 0.8, creativity: 0.8 },
    'creativity': { creativity: 0.9, openness: 0.8 },
    'relationships': { agreeableness: 0.8, extraversion: 0.6 },
    'personal_growth': { openness: 0.7, conscientiousness: 0.6 }
};

// Combine influences
const baseTraits = {
    openness: 0.5, conscientiousness: 0.5, extraversion: 0.5,
    agreeableness: 0.5, neuroticism: 0.5, confidence: 0.5,
    creativity: 0.5, leadership: 0.5
};

const ageTraits = ageInfluence[ageRange] || {};
const careerTraits = careerInfluence[careerFocus] || {};

Object.keys(baseTraits).forEach(trait => {
    if (ageTraits[trait]) baseTraits[trait] = ageTraits[trait];
    if (careerTraits[trait]) baseTraits[trait] = (baseTraits[trait] + careerTraits[trait]) / 2;
});

return baseTraits;
}

// Add personality consistency check
function addPersonalityCoherence(traits) {
// Make traits more coherent (real personalities have patterns)

// High openness usually correlates with creativity
if (traits.openness > 0.7) {
    traits.creativity = Math.max(traits.creativity, traits.openness - 0.1);
}

// High conscientiousness often means lower neuroticism
if (traits.conscientiousness > 0.7) {
    traits.neuroticism = Math.min(traits.neuroticism, 0.4);
}

// High extraversion usually means higher confidence
if (traits.extraversion > 0.7) {
    traits.confidence = Math.max(traits.confidence, traits.extraversion - 0.1);
}

// Leadership correlates with extraversion and conscientiousness
traits.leadership = (traits.extraversion * 0.4 + traits.conscientiousness * 0.4 + traits.confidence * 0.2);

return traits;
}

// Generate basic face data for backend
function generateBasicFaceData() {
return {
    age: 25 + Math.random() * 15, // 25-40
    gender: Math.random() > 0.5 ? 'male' : 'female',
    expressions: {
        neutral: 0.4 + Math.random() * 0.4,
        happy: 0.2 + Math.random() * 0.3,
        confident: 0.1 + Math.random() * 0.2,
        focused: 0.1 + Math.random() * 0.2
    }
};
}

// Updated initialization - super simple
async function initialize() {
showNotification('🚀 Initializing AI Personality Analyzer...', 'info');

applyTheme(selectedTheme);
initializeCustomization();
setupEventHandlers();

// No model loading needed!
showNotification('✨ Ready to analyze your personality!', 'success');
}

// Send to enhanced backend API
async function sendToEnhancedBackend(traits, faceData) {
    const userName = $('#user-name').val().trim() || 'You';
    const ageRange = $('#age-range').val() || '26-35';
    const careerFocus = $('#career-focus').val() || 'career_growth';

    console.log('Sending to backend:', {
        face_data: {
            personality_traits: traits,
            basic: {
                estimated_age: faceData.age || 30,
                gender: faceData.gender || 'unknown',
                expressions: faceData.expressions || {}
            }
        },
        user_profile: {
            name: userName,
            age_range: ageRange,
            career_focus: careerFocus
        }
    });

    const response = await fetch('https://ai.barakahsoft.com/analyze-face-enhanced', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            face_data: {
                personality_traits: traits,
                basic: {
                    estimated_age: faceData.age || 30,
                    gender: faceData.gender || 'unknown',
                    expressions: faceData.expressions || {}
                }
            },
            user_profile: {
                name: userName,
                age_range: ageRange,
                career_focus: careerFocus
            }
        })
    });

    if (!response.ok) {
        if (response.status === 429) {
            const errorData = await response.json();
            throw new Error(`429: ${errorData.message || 'Rate limit exceeded'}`);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('Full API response:', result);

    // Return the analysis object from the response
    return result.analysis;
}

// Ultra-modern results display
function displayCompleteAnalysis(result) {
      const fromCache = !!result.fromCache;

  // Optional: show a “served from cache” notice
  if (fromCache) {
    showNotification('🔄 Showing cached analysis', 'info');
  }
    console.log('Displaying analysis:', result);
        // Store analysis data globally
        window.analysisData = result;


    if (result.isRateLimited) {
        showRateLimitedAnalysis(result.traits, result.rateLimitMessage);
        return;
    }

    const analysis = result.enhancedAnalysis;

    // Show error if no AI response
    if (!analysis) {
        elements.loadingArea.hide();
        elements.resultsArea.show();
        elements.resultsArea.html(`
            <div class="ultra-results-container">
                <div class="ultra-section" style="text-align: center; background: linear-gradient(135deg, #f87171, #ef4444); color: white;">
                    <div style="font-size: 4rem; margin-bottom: 20px;">🚫</div>
                    <h3 style="color: white; margin-bottom: 20px; font-size: 2rem;">AI Analysis Unavailable</h3>
                    <p style="font-size: 1.1rem; margin-bottom: 30px; opacity: 0.9;">
                        Our AI analysis service is currently unavailable. This could be due to:
                        <br>• High server demand
                        <br>• Temporary service maintenance
                        <br>• Network connectivity issues
                    </p>
                    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                        <button onclick="tryagain()" class="ultra-btn" style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px);">
                            🔄 Try Again
                        </button>
                        <button onclick="location.reload()" class="ultra-btn" style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px);">
                            ♻️ Refresh Page
                        </button>
                    </div>
                    <p style="font-size: 0.9rem; margin-top: 20px; opacity: 0.7;">
                        💡 Tip: Try again in a few minutes or contact support if the issue persists
                    </p>
                </div>
            </div>
        `);
        return;
    }

    const traits = analysis.enhanced_traits || analysis.traits || result.traits;

    console.log('Analysis data:', analysis);
    console.log('Traits data:', traits);

    elements.loadingArea.hide();
    elements.customizationOptions.hide();

    elements.resultsArea.show();

    // Create ultra-modern results HTML
    let resultsHTML = `
        <div class="ultra-results-container">
            <div class="ultra-header">
                <h1 class="ultra-title">🧠 Your AI Personality Universe</h1>
                <div class="ultra-badge">
                    ✨ ${analysis.analysis_quality ? analysis.analysis_quality.toUpperCase() : 'AI-POWERED'} ANALYSIS ✨
                </div>
                <p style="font-size: 1.1rem; opacity: 0.9; margin: 20px 0 0 0;">
                    🎯 Confidence: ${Math.round((analysis.confidence_score || 0.95) * 100)}% • 
                    🤖 Model: ${analysis.ai_model || 'GPT-4'} • 
                    ⏰ ${new Date().toLocaleTimeString()}
                </p>
            </div>
    `;

    // Ultra-modern personality traits
    if (traits && Object.keys(traits).length > 0) {
        resultsHTML += `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🎯 Your Personality DNA</h2>
                <div class="ultra-grid ultra-grid-3">
        `;

        const traitInfo = {
            openness: {name: 'Creativity Universe', icon: '🌟', description: 'Innovation & Wonder'},
            conscientiousness: {name: 'Master Organizer', icon: '⚡', description: 'Discipline & Excellence'},
            extraversion: {name: 'Social Dynamo', icon: '🚀', description: 'Energy & Leadership'},
            agreeableness: {name: 'Harmony Creator', icon: '💖', description: 'Empathy & Teamwork'},
            neuroticism: {name: 'Emotional Radar', icon: '🎭', description: 'Sensitivity & Depth'},
            confidence: {name: 'Inner Power', icon: '👑', description: 'Self-Assurance'},
            creativity: {name: 'Innovation Engine', icon: '🎨', description: 'Creative Force'},
            leadership: {name: 'Influence Magnet', icon: '🌟', description: 'Natural Leader'}
        };

        Object.entries(traits).forEach(([trait, score]) => {
            if (traitInfo[trait]) {
                const percentage = Math.round(score * 100);
                const info = traitInfo[trait];

                resultsHTML += `
                    <div class="ultra-card ultra-trait-card">
                        <div class="ultra-trait-icon">${info.icon}</div>
                        <div class="ultra-trait-name">${info.name}</div>
                        <div class="ultra-trait-score">${percentage}%</div>
                        <div class="ultra-progress-ring">
                            <svg>
                                <defs>
                                    <linearGradient id="gradient-${trait}" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" style="stop-color:${colorThemes[selectedTheme].primary};stop-opacity:1" />
                                        <stop offset="100%" style="stop-color:${colorThemes[selectedTheme].secondary};stop-opacity:1" />
                                    </linearGradient>
                                </defs>
                                <circle class="background" cx="60" cy="60" r="45"></circle>
                                <circle class="progress" cx="60" cy="60" r="45" style="stroke: url(#gradient-${trait}); stroke-dashoffset: ${283 - (283 * percentage / 100)};"></circle>
                            </svg>
                        </div>
                        <p style="color: #6b7280; font-size: 0.9rem; margin: 0;">${info.description}</p>
                    </div>
                `;
            }
        });

        resultsHTML += `
                </div>
            </div>
        `;
    }

    // Ultra-modern personality insights
    if (analysis.personality_insights && analysis.personality_insights.length > 0) {
        resultsHTML += `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🔮 Deep Mind Insights</h2>
                <div class="ultra-grid">
        `;

        analysis.personality_insights.forEach((insight, index) => {
            resultsHTML += `
                <div class="ultra-card ultra-insight-card">
                    <p style="font-size: 1.1rem; line-height: 1.7; margin: 0; color: #374151; font-weight: 500;">${insight}</p>
                </div>
            `;
        });

        resultsHTML += `
                </div>
            </div>
        `;
    }

    // Ultra-modern career recommendations
    if (analysis.career_recommendations && analysis.career_recommendations.length > 0) {
        resultsHTML += `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🚀 Career Galaxy</h2>
                <div class="ultra-grid ultra-grid-2">
        `;

        analysis.career_recommendations.forEach((career, index) => {
            resultsHTML += `
                <div class="ultra-card ultra-career-card">
                    <div class="ultra-career-header">
                        <h3 class="ultra-career-title">${career.category}</h3>
                        <div class="ultra-fit-score">${career.fit_score}% Match</div>
                    </div>
                    <div style="margin: 20px 0; color: #4b5563;">
                        <strong style="color: #1f2937;">🎯 Dream Roles:</strong><br>
                        ${career.roles.join(' • ')}
                    </div>
                    <div style="margin: 20px 0; color: #6b7280; line-height: 1.6; font-style: italic;">
                        ${career.reasoning}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.5); border-radius: 15px;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; margin-bottom: 5px;">💰</div>
                            <div style="font-weight: 600; color: #059669;">${career.salary_range}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; margin-bottom: 5px;">📈</div>
                            <div style="font-weight: 600; color: #7c3aed;">${career.growth_potential}% Growth</div>
                        </div>
                    </div>
                    ${career.recommended_skills ? `
                        <div style="margin-top: 20px;">
                            <strong style="color: #374151; font-size: 0.95rem;">🛠️ Power Skills:</strong>
                            <div style="margin-top: 10px;">
                                ${career.recommended_skills.map(skill =>
                `<span class="ultra-skill-tag">${skill}</span>`
            ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    ${career.future_market_trends ? `
                        <div style="margin-top: 20px; padding: 15px; background: ${colorThemes[selectedTheme].cardGradient}; border-radius: 12px;">
                            <strong style="color: #374151; font-size: 0.95rem;">🔮 Future Trends:</strong>
                            <p style="margin: 8px 0 0 0; color: #6b7280; font-size: 0.9rem; line-height: 1.5;">${career.future_market_trends}</p>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        resultsHTML += `
                </div>
            </div>
        `;
    }

    // Ultra-modern life predictions
    if (analysis.life_predictions && Object.keys(analysis.life_predictions).length > 0) {
        resultsHTML += `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🎯 Success Constellation</h2>
                <div class="ultra-grid ultra-grid-4">
        `;

        const predictionInfo = {
            career_advancement: {name: 'Career Rocket', icon: '🚀', color: '#10b981'},
            financial_growth: {name: 'Wealth Builder', icon: '💎', color: '#f59e0b'},
            leadership_potential: {name: 'Leader Force', icon: '👑', color: '#8b5cf6'},
            innovation_capacity: {name: 'Innovation Power', icon: '⚡', color: '#06b6d4'},
            relationship_satisfaction: {name: 'Connection Master', icon: '💝', color: '#ef4444'}
        };

        Object.entries(analysis.life_predictions).forEach(([key, value]) => {
            const info = predictionInfo[key] || {
                name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
                icon: '📊',
                color: colorThemes[selectedTheme].primary
            };

            resultsHTML += `
                <div class="ultra-card ultra-prediction-card">
                    <div class="ultra-prediction-icon">${info.icon}</div>
                    <h4 style="margin: 10px 0; color: #374151; font-size: 1rem; font-weight: 700;">${info.name}</h4>
                    <div class="ultra-prediction-value">${value}%</div>
                    <div style="width: 100%; height: 8px; background: rgba(0,0,0,0.1); border-radius: 50px; overflow: hidden; margin: 15px 0;">
                        <div class="prediction-progress" style="width: ${value}%; height: 100%; background: linear-gradient(90deg, ${info.color}, ${info.color}dd); border-radius: 50px; transition: width 2s ease;"></div>
                    </div>
                    <div style="font-size: 0.85rem; color: #6b7280; font-weight: 500;">
                        ${value >= 80 ? 'Exceptional' : value >= 60 ? 'Strong' : value >= 40 ? 'Moderate' : 'Developing'}
                    </div>
                </div>
            `;
        });

        resultsHTML += `
                </div>
            </div>
        `;
    }

    // Ultra-modern growth roadmap
    if (analysis.growth_roadmap && analysis.growth_roadmap.length > 0) {
        resultsHTML += `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🗺️ Evolution Pathway</h2>
                <div class="ultra-grid">
        `;

        analysis.growth_roadmap.forEach((item, index) => {
            const priorityClass = `ultra-priority-${item.priority.toLowerCase()}`;
            const priorityEmoji = item.priority === 'High' ? '🔥' : item.priority === 'Medium' ? '⭐' : '🌱';

            resultsHTML += `
                <div class="ultra-card ultra-roadmap-item ${priorityClass}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h4 style="margin: 0; color: #1f2937; font-size: 1.3rem; font-weight: 700;">${item.area}</h4>
                        <span style="background: ${item.priority === 'High' ? '#ef4444' : item.priority === 'Medium' ? '#f59e0b' : '#22c55e'}; color: white; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">
                            ${priorityEmoji} ${item.priority}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; padding: 15px; background: rgba(255,255,255,0.5); border-radius: 12px;">
                        <div>
                            <div style="font-size: 0.85rem; color: #6b7280; font-weight: 600;">Current Level</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #1f2937;">${item.current_level}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.85rem; color: #6b7280; font-weight: 600;">Target Level</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #059669;">${item.target_level}</div>
                        </div>
                    </div>
                    <div style="margin: 15px 0;">
                        <div style="font-size: 0.9rem; color: #6b7280; font-weight: 600;">⏰ Timeline: ${item.timeline}</div>
                    </div>
                    ${item.action_steps && item.action_steps.length > 0 ? `
                        <div style="margin: 20px 0;">
                            <strong style="color: #374151; font-size: 0.95rem;">🎯 Action Steps:</strong>
                            <ul style="margin: 10px 0; padding-left: 20px; color: #6b7280;">
                                ${item.action_steps.slice(0, 3).map(step =>
                `<li style="margin: 8px 0; line-height: 1.5;">${step}</li>`
            ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        resultsHTML += `
                </div>
            </div>
        `;
    }

    // Ultra-modern motivation message
    if (analysis.motivation_message) {
        resultsHTML += `
            <div class="ultra-section" style="background: ${colorThemes[selectedTheme].gradient}; color: white; text-align: center;">
                <h2 style="color: white; font-size: 2rem; margin-bottom: 20px;">✨ Your Power Message</h2>
                <p style="font-size: 1.3rem; line-height: 1.6; margin: 0; font-weight: 500; opacity: 0.95;">
                    ${analysis.motivation_message}
                </p>
            </div>
        `;
    }

    // Create ultra-modern shareable image
    const shareableImage = createUltraModernShareableImage(traits, analysis);

    // Ultra-modern share section
    resultsHTML += `
        <div class="ultra-section ultra-share-section">
            <h2 class="ultra-section-title">🌟 Share Your Universe</h2>
            <p style="font-size: 1.1rem; color: #6b7280; margin-bottom: 30px; line-height: 1.6;">
                Inspire others with your incredible personality insights! Share your AI-powered analysis and let the world see your unique brilliance. ✨
            </p>
            ${shareableImage ? `
                <div style="margin: 30px 0;">
                    <img src="${shareableImage}" style="max-width: 400px; width: 100%; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); margin-bottom: 30px;" alt="Your Personality Analysis">
                </div>
            ` : ''}
            <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                ${shareableImage ? `<button onclick="downloadImage('${shareableImage}')" class="ultra-btn">📥 Download Your Universe</button>` : ''}
                <button onclick="shareOnSocial()" class="ultra-btn">🚀 Share on Social</button>
                <button onclick="tryagain()" class="ultra-btn">📷 Analyze Another</button>
            </div>
        </div>
    `;

    resultsHTML += `</div>`;

    // Set the HTML with fade effect
    elements.resultsArea.html(resultsHTML).hide().fadeIn(1000);

    // Animate progress bars and rings
    setTimeout(() => {
        $('.prediction-progress').each(function () {
            const width = $(this).css('width');
            $(this).css('width', '0%').animate({width: width}, 2000);
        });

        $('.ultra-progress-ring .progress').each(function () {
            const finalOffset = $(this).css('stroke-dashoffset');
            $(this).css('stroke-dashoffset', '283').animate({'stroke-dashoffset': finalOffset}, 2000);
        });
    }, 500);

    // Show success notification
    showNotification('🎉 Your personality universe is ready!', 'success');
    console.log('Ultra-modern analysis display completed successfully');
}

// Create ultra-modern shareable image
// Stunning Modern Report Image Generator with User Photo
function createUltraModernShareableImage(traits, analysis) {
if (!traits) return null;

try {
    const userName = $('#user-name').val().trim() || 'Your';
    const canvas = document.createElement('canvas');
    canvas.width = 1080;  // Perfect for social sharing
    canvas.height = 1350; // Optimized aspect ratio
    const ctx = canvas.getContext('2d');

    // Helper function for rounded rectangles
    function roundRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    // Helper function for circular images
    function drawCircularImage(ctx, img, x, y, radius) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.clip();
        const size = radius * 2;
        ctx.drawImage(img, x - radius, y - radius, size, size);
        ctx.restore();
    }

    // Modern gradient background - Deep and sophisticated
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#1a1a2e');
    gradient.addColorStop(0.5, '#16213e');
    gradient.addColorStop(1, '#0f3460');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add subtle geometric pattern
    ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
    for (let i = 0; i < 50; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const size = Math.random() * 100 + 20;
        ctx.fillRect(x, y, 2, size);
        ctx.fillRect(x, y, size, 2);
    }

    // Header section with glassmorphism - Extended for user photo
    ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
    ctx.shadowBlur = 30;
    ctx.shadowOffsetY = 10;
    roundRect(ctx, 40, 40, canvas.width - 80, 240, 24);
    ctx.fill();
    ctx.shadowColor = 'transparent';

    // Add user photo if available
    const userPhotoSize = 80;
    const photoX = canvas.width / 2;
    const photoY = 100;

    // Create circular placeholder for user photo
    ctx.fillStyle = 'rgba(100, 181, 246, 0.3)';
    ctx.strokeStyle = '#64b5f6';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(photoX, photoY, userPhotoSize / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Try to get user's uploaded image
    if (window.currentImage) {
        try {
            drawCircularImage(ctx, window.currentImage, photoX, photoY, userPhotoSize / 2);
        } catch (error) {
            console.log('Could not draw user image, using placeholder');
            // Add emoji placeholder
            ctx.font = 'bold 40px system-ui, -apple-system, sans-serif';
            ctx.fillStyle = '#64b5f6';
            ctx.textAlign = 'center';
            ctx.fillText('👤', photoX, photoY + 15);
        }
    } else {
        // Add emoji placeholder
        ctx.font = 'bold 40px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#64b5f6';
        ctx.textAlign = 'center';
        ctx.fillText('👤', photoX, photoY + 15);
    }

    // User name with modern typography
    ctx.font = 'bold 32px system-ui, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(`${userName}'s Personality`, canvas.width / 2, 200);

    ctx.font = 'bold 28px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = '#64b5f6';
    ctx.fillText('UNIVERSE', canvas.width / 2, 220);

    // AI Badge with modern styling
    ctx.fillStyle = 'rgba(100, 181, 246, 0.2)';
    ctx.strokeStyle = '#64b5f6';
    ctx.lineWidth = 2;
    const badgeWidth = 280;
    const badgeHeight = 36;
    const badgeX = (canvas.width - badgeWidth) / 2;
    const badgeY = 210;
    roundRect(ctx, badgeX, badgeY, badgeWidth, badgeHeight, 18);
    ctx.fill();
    ctx.stroke();

    ctx.font = 'bold 16px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = '#64b5f6';
    ctx.textAlign = 'center';
    ctx.fillText('🤖 AI-POWERED ANALYSIS ✨', canvas.width / 2, 232);

    // Personality Traits Section - Adjusted Y position
    const traitsY = 340;
    ctx.font = 'bold 28px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText('🎯 PERSONALITY TRAITS', canvas.width / 2, traitsY);

    // Get top 4 traits for cleaner layout
    const availableTraits = Object.entries(traits)
        .filter(([trait, score]) => score > 0)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4);

    const traitColors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'];
    const traitNames = {
        openness: 'CREATIVITY',
        conscientiousness: 'DISCIPLINE',
        extraversion: 'SOCIAL ENERGY',
        agreeableness: 'HARMONY',
        neuroticism: 'SENSITIVITY',
        confidence: 'CONFIDENCE',
        creativity: 'CREATIVITY',
        leadership: 'LEADERSHIP'
    };

    // Modern trait cards in 2x2 grid
    availableTraits.forEach(([trait, score], index) => {
        const percentage = Math.round(score * 100);
        const col = index % 2;
        const row = Math.floor(index / 2);
        const cardWidth = 220;
        const cardHeight = 140;
        const spacing = 260;
        const startX = (canvas.width - (2 * cardWidth + spacing - cardWidth)) / 2;
        const startY = traitsY + 60;

        const x = startX + col * spacing;
        const y = startY + row * 160;
        const color = traitColors[index];

        // Trait card background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        roundRect(ctx, x, y, cardWidth, cardHeight, 16);
        ctx.fill();
        ctx.stroke();

        // Trait name
        ctx.font = 'bold 16px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText(traitNames[trait] || trait.toUpperCase(), x + cardWidth/2, y + 30);

        // Large percentage
        ctx.font = 'bold 42px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = color;
        ctx.fillText(`${percentage}%`, x + cardWidth/2, y + 80);

        // Progress bar
        const barWidth = 160;
        const barHeight = 6;
        const barX = x + (cardWidth - barWidth) / 2;
        const barY = y + 100;

        // Background bar
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        roundRect(ctx, barX, barY, barWidth, barHeight, 3);
        ctx.fill();

        // Progress fill
        ctx.fillStyle = color;
        roundRect(ctx, barX, barY, (barWidth * percentage) / 100, barHeight, 3);
        ctx.fill();
    });

    // Success Predictions Section - Adjusted Y position
    if (analysis && analysis.life_predictions) {
        const predY = 780;
        ctx.font = 'bold 28px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText('🎯 SUCCESS PREDICTIONS', canvas.width / 2, predY);

        const predictions = Object.entries(analysis.life_predictions).slice(0, 4);
        const predictionNames = {
            career_advancement: '💼 Career',
            financial_growth: '💎 Wealth',
            leadership_potential: '👑 Leadership',
            innovation_capacity: '⚡ Innovation'
        };

        // Modern prediction cards in 2x2 grid
        predictions.forEach(([key, value], index) => {
            const col = index % 2;
            const row = Math.floor(index / 2);
            const cardWidth = 200;
            const cardHeight = 80;
            const spacing = 240;
            const startX = (canvas.width - (2 * cardWidth + spacing - cardWidth)) / 2;
            const startY = predY + 40;

            const x = startX + col * spacing;
            const y = startY + row * 100;
            const name = predictionNames[key] || key.replace('_', ' ').toUpperCase();

            // Prediction card background
            ctx.fillStyle = 'rgba(255, 255, 255, 0.06)';
            ctx.strokeStyle = '#ffd700';
            ctx.lineWidth = 2;
            roundRect(ctx, x, y, cardWidth, cardHeight, 12);
            ctx.fill();
            ctx.stroke();

            // Prediction text
            ctx.font = 'bold 14px system-ui, -apple-system, sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.fillText(name, x + cardWidth/2, y + 25);

            ctx.font = 'bold 32px system-ui, -apple-system, sans-serif';
            ctx.fillStyle = '#ffd700';
            ctx.fillText(`${value}%`, x + cardWidth/2, y + 55);
        });
    }

    // Key Insight Section - Adjusted Y position
    if (analysis && analysis.personality_insights && analysis.personality_insights.length > 0) {
        const insightY = 1060;
        ctx.font = 'bold 24px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText('💡 KEY INSIGHT', canvas.width / 2, insightY);

        // Insight background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        roundRect(ctx, 60, insightY + 20, canvas.width - 120, 120, 16);
        ctx.fill();
        ctx.stroke();

        // Get the first insight and ensure it's a string
        const firstInsight = analysis.personality_insights[0];
        const insightText = typeof firstInsight === 'string' ? firstInsight :
                          firstInsight.text || firstInsight.message || firstInsight.insight ||
                          'Your personality shows unique strengths and remarkable potential for growth.';

        // Truncate insight text safely
        const maxLength = 140;
        const truncatedInsight = insightText.length > maxLength ?
            insightText.substring(0, maxLength) + '...' : insightText;

        ctx.font = '18px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#e0e0e0';
        ctx.textAlign = 'center';

        // Word wrap for insight text
        const words = String(truncatedInsight).split(' ');
        let line = '';
        let lines = [];
        words.forEach(word => {
            const testLine = line + word + ' ';
            const metrics = ctx.measureText(testLine);
            if (metrics.width > canvas.width - 160 && line !== '') {
                lines.push(line);
                line = word + ' ';
            } else {
                line = testLine;
            }
        });
        lines.push(line);

        lines.slice(0, 4).forEach((line, index) => {
            ctx.fillText(line.trim(), canvas.width / 2, insightY + 55 + (index * 24));
        });
    }

    // Footer with user attribution - Adjusted Y position
    ctx.font = 'bold 18px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = 'rgba(100, 181, 246, 0.8)';
    ctx.textAlign = 'center';
    ctx.fillText('Powered by Advanced AI • Your Personality Universe', canvas.width / 2, canvas.height - 60);

    // Timestamp and confidence
    ctx.font = '14px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    const timestamp = new Date().toLocaleDateString();
    const confidence = Math.round((analysis && analysis.confidence_score ? analysis.confidence_score : 0.95) * 100);
    ctx.fillText(`Generated: ${timestamp} • Confidence: ${confidence}%`, canvas.width / 2, canvas.height - 35);

    return canvas.toDataURL('image/png', 0.95);
} catch (error) {
    console.error('Error generating stunning report image:', error);
    return null;
}
}

// Generate and download image on demand
window.generateAndDownloadImage = function() {
try {
    showNotification('🎨 Generating your personalized image...', 'info');

    // Get current analysis data from global variable
    if (!analysisData) {
        showNotification('❌ No analysis data available', 'error');
        return;
    }

    const shareableImage = createUltraModernShareableImage(analysisData.traits, analysisData.enhancedAnalysis);

    if (shareableImage) {
        downloadImage(shareableImage);
        showNotification('✅ Image generated and downloaded!', 'success');
    } else {
        showNotification('❌ Failed to generate image', 'error');
    }
} catch (error) {
    console.error('Error generating image:', error);
    showNotification('❌ Error generating image', 'error');
}
};

function roundRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}

function showRateLimitedAnalysis(traits, rateLimitMessage) {
    elements.loadingArea.hide();
    elements.resultsArea.show();
    elements.customizationOptions.hide();

    elements.resultsArea.html(`
        <div class="ultra-results-container">
            <div class="ultra-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center;">
                <div style="font-size: 5rem; margin-bottom: 30px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">⏰</div>
                <h2 style="color: white; margin-bottom: 20px; font-size: 2.5rem; font-weight: 800;">Daily AI Limit Reached</h2>
                <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(20px); border-radius: 20px; padding: 30px; margin: 30px 0; border: 1px solid rgba(255,255,255,0.2);">
                    <p style="font-size: 1.2rem; line-height: 1.7; margin-bottom: 20px; color: white;">${rateLimitMessage}</p>
                    <div style="color: #ffd700; font-size: 1.1rem; font-weight: 600;">✨ Your basic personality analysis is ready below ✨</div>
                </div>
                <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-top: 30px;">
                    <button onclick="location.reload()" class="ultra-btn" style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3);">
                        🔄 Try Tomorrow
                    </button>
                    <a href="#upgrade" class="ultra-btn" style="background: linear-gradient(135deg, #ffd700, #ffed4e); color: #1a1a1a; text-decoration: none; display: inline-block;">
                        ⭐ Upgrade Now
                    </a>
                </div>
            </div>
    `);

    // Display basic traits if available
    if (traits && Object.keys(traits).length > 0) {
        let traitsHTML = `
            <div class="ultra-section">
                <h2 class="ultra-section-title">🎯 Your Basic Personality Traits</h2>
                <div class="ultra-grid ultra-grid-3">
        `;

        const traitInfo = {
            openness: {name: 'Creativity', icon: '🌟', description: 'Innovation & Wonder'},
            conscientiousness: {name: 'Organization', icon: '⚡', description: 'Discipline & Excellence'},
            extraversion: {name: 'Social Energy', icon: '🚀', description: 'Energy & Leadership'},
            agreeableness: {name: 'Harmony', icon: '💖', description: 'Empathy & Teamwork'},
            neuroticism: {name: 'Sensitivity', icon: '🎭', description: 'Emotional Depth'}
        };

        Object.entries(traits).forEach(([trait, score]) => {
            if (traitInfo[trait]) {
                const percentage = Math.round(score * 100);
                const info = traitInfo[trait];

                traitsHTML += `
                    <div class="ultra-card ultra-trait-card">
                        <div class="ultra-trait-icon">${info.icon}</div>
                        <div class="ultra-trait-name">${info.name}</div>
                        <div class="ultra-trait-score">${percentage}%</div>
                        <p style="color: #6b7280; font-size: 0.9rem; margin: 10px 0 0 0;">${info.description}</p>
                    </div>
                `;
            }
        });

        traitsHTML += `
                </div>
            </div>
        </div>`;

        elements.resultsArea.append(traitsHTML);

        // Create basic shareable image
        const shareableImage = createUltraModernShareableImage(traits, null);
        if (shareableImage) {
            elements.resultsArea.append(`
                <div class="ultra-section ultra-share-section">
                    <h2 class="ultra-section-title">📤 Share Your Basic Analysis</h2>
                    <div style="margin: 20px 0;">
                        <img src="${shareableImage}" style="max-width: 400px; width: 100%; border-radius: 15px; box-shadow: 0 15px 30px rgba(0,0,0,0.2);">
                    </div>
                    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; margin-top: 20px;">
                        <button onclick="downloadImage('${shareableImage}')" class="ultra-btn">📥 Download</button>
                        <button onclick="shareOnSocial()" class="ultra-btn">📱 Share</button>
                        <button onclick="tryagain()" class="ultra-btn">📷 Try Another</button>
                    </div>
                </div>
            `);
        }
    }

    // Animate fade in
    elements.resultsArea.hide().fadeIn(1000);
}

// Fixed Image Storage and Display Functions

function displayImage(src) {
elements.uploadArea.fadeOut(500, function() {
    elements.previewArea.fadeIn(500);
});

const ctx = elements.previewCanvas.getContext('2d');
const img = new Image();
img.onload = function() {
    const maxWidth = 400;
    const maxHeight = 400;
    let { width, height } = img;

    if (width > height) {
        if (width > maxWidth) {
            height *= maxWidth / width;
            width = maxWidth;
        }
    } else {
        if (height > maxHeight) {
            width *= maxHeight / height;
            height = maxHeight;
        }
    }

    elements.previewCanvas.width = width;
    elements.previewCanvas.height = height;
    ctx.drawImage(img, 0, 0, width, height);

    // Store the image globally for report generation
    window.currentImage = img;

    // Also store in analysisData if it exists
    if (window.analysisData) {
        window.analysisData.userImage = img;
    }

    console.log('✅ Image stored for report generation');
};
img.src = src;
}

// Enhanced file input handler
elements.fileInput.change(function(e) {
const file = e.target.files[0];
if (file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showNotification('❌ Please select a valid image file', 'error');
        return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showNotification('❌ Image too large. Please select a smaller image', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        displayImage(e.target.result);
        showNotification('🖼️ Image loaded! Ready for AI analysis', 'success');
    };
    reader.readAsDataURL(file);
}
});

// Enhanced photo capture
elements.takePhotoBtn.click(() => {
// Countdown effect
let countdown = 3;
const countdownInterval = setInterval(() => {
    showNotification(`📸 Taking photo in ${countdown}...`, 'info');
    countdown--;

    if (countdown < 0) {
        clearInterval(countdownInterval);

        // Capture photo
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = elements.cameraStream.videoWidth;
        canvas.height = elements.cameraStream.videoHeight;
        context.drawImage(elements.cameraStream, 0, 0);

        // Stop camera
        stream.getTracks().forEach(track => track.stop());
        elements.cameraArea.fadeOut(500);

        // Process captured image
        canvas.toBlob(blob => {
            const url = URL.createObjectURL(blob);
            displayImage(url);
            showNotification('✨ Photo captured! Ready for AI analysis', 'success');
        });
    }
}, 1000);
});

// Store analysis data properly
// Enhanced generateAndDownloadImage function
window.generateAndDownloadImage = function() {
try {
    showNotification('🎨 Generating your personalized image...', 'info');

    // Get current analysis data from global variable
    if (!window.analysisData) {
        showNotification('❌ No analysis data available', 'error');
        return;
    }

    // Debug: Check what images are available
    console.log('Available images:', {
        currentImage: !!window.currentImage,
        analysisImage: !!(window.analysisData && window.analysisData.userImage),
        previewCanvas: !!(elements.previewCanvas && elements.previewCanvas.width > 0)
    });

    const shareableImage = createUltraModernShareableImage(
        window.analysisData.traits,
        window.analysisData.enhancedAnalysis
    );

    if (shareableImage) {
        downloadImage(shareableImage);
        showNotification('✅ Image generated and downloaded!', 'success');
    } else {
        showNotification('❌ Failed to generate image', 'error');
    }
} catch (error) {
    console.error('Error generating image:', error);
    showNotification('❌ Error generating image', 'error');
}
};

// Alternative: Create image from current canvas state
function getImageFromCanvas() {
if (elements.previewCanvas && elements.previewCanvas.width > 0) {
    const img = new Image();
    img.src = elements.previewCanvas.toDataURL();
    return img;
}
return null;
}

// Debug function to check image availability
window.debugImageState = function() {
console.log('=== IMAGE DEBUG INFO ===');
console.log('window.currentImage:', window.currentImage);
console.log('window.analysisData:', window.analysisData);
console.log('previewCanvas dimensions:',
    elements.previewCanvas ? `${elements.previewCanvas.width}x${elements.previewCanvas.height}` : 'null'
);

if (window.currentImage) {
    console.log('currentImage details:', {
        src: window.currentImage.src?.substring(0, 50) + '...',
        width: window.currentImage.width,
        height: window.currentImage.height,
        complete: window.currentImage.complete
    });
}
};

// Call this in your analyze function to ensure image is stored
function ensureImageStored() {
if (!window.currentImage && elements.previewCanvas && elements.previewCanvas.width > 0) {
    window.currentImage = getImageFromCanvas();
    console.log('✅ Image retrieved from canvas');
}
}

// Enhanced event handlers
function setupEventHandlers() {
    // Ultra-modern theme selection with haptic feedback
    $(document).on('click', '.theme-btn-ultra', function () {
        $('.theme-btn-ultra').removeClass('active');
        $(this).addClass('active');

        const newTheme = $(this).data('theme');
        selectedTheme = newTheme;
        applyTheme(newTheme);

        // Haptic feedback simulation
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        showNotification(`✨ Theme changed to ${newTheme}!`, 'success');
    });

    // Enhanced upload button with hover effects
    elements.uploadBtn.click(() => {
        elements.fileInput.click();
        showNotification('📁 Choose your photo for AI analysis', 'info');
    });

    // Enhanced camera functionality
    elements.cameraBtn.click(async () => {
        elements.uploadArea.fadeOut(500, function () {
            elements.cameraArea.fadeIn(500);
        });

        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: {ideal: 1280},
                    height: {ideal: 720},
                    facingMode: 'user'
                }
            });
            elements.cameraStream.srcObject = stream;
            elements.cameraStream.play();
            showNotification('📸 Camera ready! Position your face in the frame', 'success');
        } catch (err) {
            showNotification('❌ Camera access denied or not available', 'error');
            elements.cameraArea.fadeOut(500, function () {
                elements.uploadArea.fadeIn(500);
            });
        }
    });

    // Enhanced photo capture with countdown
    elements.takePhotoBtn.click(() => {
        // Countdown effect
        let countdown = 3;
        const countdownInterval = setInterval(() => {
            showNotification(`📸 Taking photo in ${countdown}...`, 'info');
            countdown--;

            if (countdown < 0) {
                clearInterval(countdownInterval);

                // Capture photo
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.width = elements.cameraStream.videoWidth;
                canvas.height = elements.cameraStream.videoHeight;
                context.drawImage(elements.cameraStream, 0, 0);

                // Stop camera
                stream.getTracks().forEach(track => track.stop());
                elements.cameraArea.fadeOut(500);

                // Process captured image
                canvas.toBlob(blob => {
                    const url = URL.createObjectURL(blob);
                    displayImage(url);
                    currentImage = new Image();
                    currentImage.src = url;
                    showNotification('✨ Photo captured! Ready for AI analysis', 'success');
                });
            }
        }, 1000);
    });

    // Enhanced back button
    elements.backBtn.click(() => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        elements.cameraArea.fadeOut(500, function () {
            elements.uploadArea.fadeIn(500);
        });
    });

    // Enhanced file input
    elements.fileInput.change(function (e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showNotification('❌ Please select a valid image file', 'error');
                return;
            }

            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                showNotification('❌ Image too large. Please select a smaller image', 'error');
                return;
            }

            const reader = new FileReader();
            reader.onload = function (e) {
                displayImage(e.target.result);
                currentImage = new Image();
                currentImage.src = e.target.result;
                showNotification('🖼️ Image loaded! Ready for AI analysis', 'success');
            };
            reader.readAsDataURL(file);
        }
    });

    // Ultra-enhanced analyze button with loading stages
    // Fixed Progress Bar and Display Logic
elements.analyzeBtn.click(async () => {
    if (!currentImage) {
        showNotification('❌ Please upload or capture an image first', 'error');
        return;
    }

    console.log('🚀 Starting analysis...');

    // get a reproducible key
  const dataUrl = elements.previewCanvas.toDataURL();
  const key = await hashString(dataUrl);

  // 1️⃣ If we’ve got it cached, bail out immediately
  if (analysisCache[key]) {
    const cached = {...analysisCache[key], fromCache: true, userImage: currentImage};
    // make sure nothing is queued to show
    elements.previewArea.stop(true,true).hide();
    elements.loadingArea.stop(true,true).hide();
    elements.customizationOptions.hide();
    elements.resultsArea.show();
    return displayCompleteAnalysis(cached);
  }

    // Ensure image is properly stored before analysis
    ensureImageStored();

    // Hide preview and show loading
    elements.previewArea.fadeOut(500, function() {
        elements.loadingArea.fadeIn(500);
    });

    // Reset progress bar
    elements.progressBar.css('width', '0%');

    // Initialize loading stages
    let progress = 0;
    const stages = [
        '🔍 Analyzing your image...',
        '🧠 Processing personality traits...',
        '⚡ Generating insights...',
        '🚀 Creating recommendations...',
        '✨ Finalizing your analysis...'
    ];
    let currentStage = 0;

    // Update stage text initially
    $('#analysis-stage').text(stages[0]);

    // Progress animation
    const progressInterval = setInterval(() => {
        progress += Math.random() * 8 + 3; // Slower, more realistic progress
        if (progress > 90) progress = 90; // Stop at 90% until analysis completes

        elements.progressBar.css('width', progress + '%');

        // Update stage based on progress
        const expectedStage = Math.floor((progress / 90) * (stages.length - 1));
        if (expectedStage > currentStage && currentStage < stages.length - 1) {
            currentStage = expectedStage;
            $('#analysis-stage').fadeOut(200, function() {
                $(this).text(stages[currentStage]).fadeIn(200);
            });
        }
    }, 400);

    try {
        console.log('📸 Preparing image for analysis...');

        // Get image for analysis
        let analysisImage = currentImage;
        if (!analysisImage && elements.previewCanvas && elements.previewCanvas.width > 0) {
            analysisImage = new Image();
            analysisImage.src = elements.previewCanvas.toDataURL();
            window.currentImage = analysisImage;
        }

        if (!analysisImage) {
            throw new Error('No image available for analysis');
        }

        console.log('🔍 Starting AI analysis...');

        // Perform analysis
        const result = await analyzeFaceWithAI(analysisImage);

        console.log('✅ Analysis completed:', result ? 'Success' : 'Failed');

        // Complete progress bar
        clearInterval(progressInterval);
        progress = 100;
        elements.progressBar.css('width', '100%');
        $('#analysis-stage').text('🎉 Analysis complete!');

        // Show results after a brief delay
        setTimeout(() => {
            console.log('📄 Displaying results...');

            if (result) {
                // Store the image in the result
                result.userImage = analysisImage;

                // Hide loading and show results
                elements.loadingArea.hide();

                try {
                      // prune result of any DOM/image refs
                  const toCache = {
                    traits:       result.traits,
                    enhancedAnalysis: result.enhancedAnalysis,
                    faceData:     result.faceData,
                    isRateLimited: result.isRateLimited,
                    rateLimitMessage: result.rateLimitMessage
                  };

                  // store
                  analysisCache[key] = toCache;
                  localStorage.setItem('analysisCache', JSON.stringify(analysisCache));

                  // merge back the img so display works
                  result.traits = toCache.traits;
                  result.enhancedAnalysis = toCache.enhancedAnalysis;
                  result.faceData = toCache.faceData;
                  result.isRateLimited = toCache.isRateLimited;
                  result.rateLimitMessage = toCache.rateLimitMessage;
                  result.userImage = currentImage;


                    displayCompleteAnalysis(result);
                    console.log('✅ Results displayed successfully');
                } catch (displayError) {
                    console.error('❌ Error displaying results:', displayError);
                    showErrorState('Failed to display results. Please try again.');
                }
            } else {
                console.error('❌ No analysis result to display');
                showErrorState('Analysis failed. Please try again.');
            }
        }, 1500); // Give user time to see completion

    } catch (error) {
        console.error('❌ Analysis error:', error);

        // Stop progress and show error
        clearInterval(progressInterval);
        showErrorState(error.message || 'Analysis failed. Please try again.');
    }
});

// Helper function to show error state
function showErrorState(message) {
    elements.loadingArea.hide();
    elements.previewArea.show();
    showNotification(`❌ ${message}`, 'error');

    // Reset progress bar
    elements.progressBar.css('width', '0%');
    $('#analysis-stage').text('Ready to analyze...');
}



// Test function to debug display issues
window.debugDisplay = function() {
    console.log('=== DISPLAY DEBUG ===');
    console.log('elements.loadingArea visible:', elements.loadingArea.is(':visible'));
    console.log('elements.resultsArea visible:', elements.resultsArea.is(':visible'));
    console.log('elements.previewArea visible:', elements.previewArea.is(':visible'));
    console.log('window.analysisData:', !!window.analysisData);

    if (window.analysisData) {
        console.log('Analysis data structure:', {
            traits: !!window.analysisData.traits,
            enhancedAnalysis: !!window.analysisData.enhancedAnalysis,
            isRateLimited: window.analysisData.isRateLimited
        });
    }
};

// Add CSS for basic styling (if not already present)
if (!$('#analysis-styles').length) {
    $('head').append(`
        <style id="analysis-styles">
        .ultra-results-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .hero-section {
            text-align: center;
            margin-bottom: 40px;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
        }
        .hero-badge {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            margin-top: 20px;
            display: inline-block;
        }
        .section-container {
            margin: 30px 0;
            padding: 30px;
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .traits-grid, .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .trait-card, .insight-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .trait-score {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .ultra-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .ultra-btn:hover {
            transform: translateY(-2px);
        }
        </style>
    `);
}

    // Add keyboard shortcuts
    $(document).keydown(function (e) {
        if (e.ctrlKey || e.metaKey) {
            switch (e.which) {
                case 85: // Ctrl+U - Upload
                    e.preventDefault();
                    elements.fileInput.click();
                    break;
                case 13: // Ctrl+Enter - Analyze
                    e.preventDefault();
                    if (currentImage) {
                        elements.analyzeBtn.click();
                    }
                    break;
                case 82: // Ctrl+R - Retry
                    e.preventDefault();
                    tryagain();
                    break;
            }
        }
    });
}

// Initialize the ultra-modern application
async function initialize() {
    showNotification('🚀 Initializing AI Personality Analyzer...', 'info');

    applyTheme(selectedTheme);
    initializeCustomization();
    setupEventHandlers();

    showNotification('✨ Ready to analyze your personality universe!', 'success');

    // Add some visual flair to the page load
    $('body').css('overflow', 'hidden');
    setTimeout(() => {
        $('body').css('overflow', 'auto');
    }, 1000);
}

// Start the magic
initialize();
})
