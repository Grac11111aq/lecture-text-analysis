// 日本語ワードクラウド設定ツール Ver.2 - 単語除外テスト版JavaScript

class WordCloudAppV2 {
    constructor() {
        this.currentConfig = {};
        this.fonts = {};
        this.sampleTexts = {};
        this.fixedParams = {};
        this.accessibleColors = {};
        this.stopWordCategories = {};
        this.generateTimeout = null;
        
        this.init();
    }
    
    async init() {
        await this.loadInitialData();
        this.setupEventListeners();
        this.loadDefaultConfig();
        this.setupAccessibility();
        
        // 初期状態で歓迎メッセージを表示
        this.showWelcomeMessage();
        
        console.log('🎯 ワードクラウドアプリ Ver.2 初期化完了');
    }
    
    async loadInitialData() {
        try {
            // 並列でデータ読み込み
            const [fontsData, textsData, fixedParamsData, stopWordsData] = await Promise.all([
                fetch('/api/fonts').then(r => r.json()),
                fetch('/api/sample-texts').then(r => r.json()),
                fetch('/api/fixed-params').then(r => r.json()),
                fetch('/api/stop-words').then(r => r.json())
            ]);
            
            this.fonts = fontsData.fonts;
            this.sampleTexts = textsData.texts;
            this.fixedParams = fixedParamsData.fixed_params;
            this.accessibleColors = fixedParamsData.accessible_colors;
            this.stopWordCategories = stopWordsData.categories;
            
            this.populateSelects();
            
        } catch (error) {
            console.error('初期データ読み込みエラー:', error);
            this.showToast('初期データの読み込みに失敗しました', 'error');
        }
    }
    
    populateSelects() {
        // フォント選択肢
        const fontSelect = document.getElementById('fontSelect');
        fontSelect.innerHTML = '';
        
        Object.entries(this.fonts).forEach(([key, font]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `${font.name} - ${font.description}`;
            fontSelect.appendChild(option);
        });
        
        // デフォルトでIPAexGothicを選択（利用可能な場合）
        if (this.fonts['ipaexg']) {
            fontSelect.value = 'ipaexg';
        }
    }
    
    setupEventListeners() {
        // テキストソース変更
        document.getElementById('textSource').addEventListener('change', (e) => {
            this.handleTextSourceChange(e.target.value);
        });
        
        // カスタムテキスト変更
        document.getElementById('customText').addEventListener('input', () => {
            if (document.getElementById('textSource').value === 'custom') {
                this.scheduleGeneration();
            }
        });
        
        // フォント・サイズ設定変更
        ['fontSelect', 'width', 'height', 'colormap'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.scheduleGeneration());
            }
        });
        
        // 除外カテゴリーチェックボックス
        ['excludeGeneral', 'excludeThanks', 'excludeSchool', 'excludeExperiment'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    this.updateExcludedWordsDisplay();
                    this.scheduleGeneration();
                });
            }
        });
        
        // カスタム除外単語
        document.getElementById('customExcludeWords').addEventListener('input', () => {
            this.scheduleGeneration();
        });
        
        // ボタンイベント
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateWordCloud();
        });
        
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetToDefaults();
        });
        
        document.getElementById('exportConfig').addEventListener('click', () => {
            this.exportConfig();
        });
        
        document.getElementById('downloadImage').addEventListener('click', () => {
            this.downloadImage();
        });
    }
    
    setupAccessibility() {
        // キーボードナビゲーション改善
        const focusableElements = document.querySelectorAll(
            'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        // Escキーでフォーカスをリセット
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.activeElement.blur();
            }
        });
        
        // aria-label の動的更新
        this.updateAriaLabels();
    }
    
    updateAriaLabels() {
        // 除外カテゴリーの詳細説明を追加
        Object.entries(this.stopWordCategories).forEach(([categoryKey, categoryData]) => {
            const checkbox = document.querySelector(`input[value="${categoryKey}"]`);
            if (checkbox) {
                const words = categoryData.words.slice(0, 3).join(', ');
                checkbox.setAttribute('aria-label', 
                    `${categoryData.name}を除外 (例: ${words}など)`);
            }
        });
    }
    
    handleTextSourceChange(source) {
        const customGroup = document.getElementById('customTextGroup');
        
        if (source === 'custom') {
            customGroup.style.display = 'block';
            // フォーカスをカスタムテキストエリアに移動
            setTimeout(() => {
                document.getElementById('customText').focus();
            }, 100);
        } else {
            customGroup.style.display = 'none';
            this.scheduleGeneration();
        }
    }
    
    loadDefaultConfig() {
        // デフォルト設定をUIに反映
        const defaults = {
            text_source: 'all_responses',
            font: Object.keys(this.fonts)[0] || 'default',
            width: 1000,
            height: 600,
            colormap: 'accessible_three'
        };
        
        this.applyConfigToUI(defaults);
    }
    
    applyConfigToUI(config) {
        // 設定値をUIコントロールに適用
        Object.entries(config).forEach(([key, value]) => {
            const element = document.getElementById(this.toCamelCase(key));
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        });
        
        // テキストソースに応じてカスタムテキストエリアの表示切り替え
        this.handleTextSourceChange(config.text_source || 'all_responses');
    }
    
    toCamelCase(str) {
        return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    }
    
    getCurrentConfig() {
        const config = {};
        
        // 基本設定を収集
        const controls = {
            textSource: 'text_source',
            customText: 'custom_text',
            fontSelect: 'font',
            width: 'width',
            height: 'height',
            colormap: 'colormap',
            customExcludeWords: 'custom_exclude_words'
        };
        
        Object.entries(controls).forEach(([elementId, configKey]) => {
            const element = document.getElementById(elementId);
            if (element) {
                if (element.type === 'number') {
                    config[configKey] = parseInt(element.value);
                } else {
                    config[configKey] = element.value;
                }
            }
        });
        
        // 除外カテゴリーを収集
        const excludeCategories = [];
        ['excludeGeneral', 'excludeThanks', 'excludeSchool', 'excludeExperiment'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox && checkbox.checked) {
                excludeCategories.push(checkbox.value);
            }
        });
        config.exclude_categories = excludeCategories;
        
        // 固定パラメータを含める
        config.fixed_params = this.fixedParams;
        
        return config;
    }
    
    updateExcludedWordsDisplay() {
        // メタ情報の除外カテゴリー表示を更新
        const excludedCategories = [];
        ['excludeGeneral', 'excludeThanks', 'excludeSchool', 'excludeExperiment'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox && checkbox.checked) {
                const categoryData = this.stopWordCategories[checkbox.value];
                if (categoryData) {
                    excludedCategories.push(categoryData.name);
                }
            }
        });
        
        const metaExcluded = document.getElementById('metaExcluded');
        if (metaExcluded) {
            metaExcluded.textContent = excludedCategories.length > 0 
                ? excludedCategories.join(', ') 
                : 'なし';
        }
    }
    
    scheduleGeneration() {
        // デバウンス: 800ms後に生成（Ver.2では少し長めに）
        clearTimeout(this.generateTimeout);
        this.generateTimeout = setTimeout(() => {
            this.generateWordCloud();
        }, 800);
    }
    
    async generateWordCloud() {
        const config = this.getCurrentConfig();
        this.currentConfig = config;
        
        this.showLoading();
        this.announceToScreenReader('ワードクラウドを生成しています');
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showImage(result.image);
                this.updateMetaInfo(config);
                this.showToast('ワードクラウドを生成しました', 'success');
                this.announceToScreenReader('ワードクラウドの生成が完了しました');
            } else {
                this.showError(result.error);
                this.showToast(`エラー: ${result.error}`, 'error');
                this.announceToScreenReader(`エラーが発生しました: ${result.error}`);
            }
            
        } catch (error) {
            console.error('生成エラー:', error);
            this.showError('ネットワークエラーが発生しました');
            this.showToast('ネットワークエラーが発生しました', 'error');
            this.announceToScreenReader('ネットワークエラーが発生しました');
        }
    }
    
    showLoading() {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('previewImage').style.display = 'none';
        document.getElementById('welcomeMessage').style.display = 'none';
        document.getElementById('metaInfo').style.display = 'none';
    }
    
    showImage(imageBase64) {
        const img = document.getElementById('wordcloudImg');
        img.src = 'data:image/png;base64,' + imageBase64;
        img.alt = '生成されたワードクラウド - ' + this.getImageDescription();
        
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('previewImage').style.display = 'block';
        document.getElementById('welcomeMessage').style.display = 'none';
        document.getElementById('metaInfo').style.display = 'block';
        document.getElementById('downloadImage').style.display = 'inline-flex';
    }
    
    getImageDescription() {
        // アクセシビリティのための画像説明を生成
        const config = this.currentConfig;
        const source = this.sampleTexts[config.text_source]?.name || 'カスタム';
        const excludedCount = config.exclude_categories?.length || 0;
        
        return `${source}データから生成、${excludedCount}カテゴリーの単語を除外`;
    }
    
    showError(errorMessage) {
        document.getElementById('errorText').textContent = errorMessage;
        
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'block';
        document.getElementById('previewImage').style.display = 'none';
        document.getElementById('welcomeMessage').style.display = 'none';
        document.getElementById('metaInfo').style.display = 'none';
    }
    
    showWelcomeMessage() {
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('previewImage').style.display = 'none';
        document.getElementById('welcomeMessage').style.display = 'block';
        document.getElementById('metaInfo').style.display = 'none';
    }
    
    updateMetaInfo(config) {
        const fontInfo = this.fonts[config.font] || { name: 'Unknown' };
        
        document.getElementById('metaFont').textContent = fontInfo.name;
        document.getElementById('metaSize').textContent = `${config.width} × ${config.height}`;
        document.getElementById('metaColormap').textContent = config.colormap;
        
        this.updateExcludedWordsDisplay();
    }
    
    resetToDefaults() {
        if (confirm('設定をデフォルトに戻しますか？')) {
            // チェックボックスをすべてクリア
            ['excludeGeneral', 'excludeThanks', 'excludeSchool', 'excludeExperiment'].forEach(id => {
                const checkbox = document.getElementById(id);
                if (checkbox) checkbox.checked = false;
            });
            
            // テキストエリアをクリア
            document.getElementById('customExcludeWords').value = '';
            
            this.loadDefaultConfig();
            this.showToast('設定をリセットしました', 'info');
            this.scheduleGeneration();
        }
    }
    
    async exportConfig() {
        try {
            const config = this.getCurrentConfig();
            
            const response = await fetch('/api/export-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`設定をエクスポートしました: ${result.filename}`, 'success');
            } else {
                this.showToast(`エクスポートエラー: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('エクスポートエラー:', error);
            this.showToast('エクスポートに失敗しました', 'error');
        }
    }
    
    downloadImage() {
        const img = document.getElementById('wordcloudImg');
        if (img.src) {
            const link = document.createElement('a');
            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
            link.download = `wordcloud_v2_${timestamp}.png`;
            link.href = img.src;
            link.click();
            
            this.showToast('画像をダウンロードしました', 'success');
            this.announceToScreenReader('画像のダウンロードが完了しました');
        }
    }
    
    announceToScreenReader(message) {
        // スクリーンリーダー用のライブリージョンでメッセージを通知
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.style.width = '1px';
        announcement.style.height = '1px';
        announcement.style.overflow = 'hidden';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageElement = toast.querySelector('.toast-message');
        
        // アイコン設定
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        icon.className = `toast-icon ${icons[type] || icons.info}`;
        messageElement.textContent = message;
        
        // 既存のクラスをクリア
        toast.className = 'toast';
        toast.classList.add(type);
        
        // アクセシビリティ属性を設定
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // 表示
        toast.classList.add('show');
        
        // スクリーンリーダーにも通知
        this.announceToScreenReader(message);
        
        // 4秒後に非表示（エラーの場合は少し長め）
        const duration = type === 'error' ? 6000 : 4000;
        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }
}

// グローバル関数（HTMLから呼び出し可能）
function generateWordCloud() {
    if (window.wordCloudAppV2) {
        window.wordCloudAppV2.generateWordCloud();
    }
}

// DOM読み込み完了後にアプリ初期化
document.addEventListener('DOMContentLoaded', () => {
    window.wordCloudAppV2 = new WordCloudAppV2();
    
    // スキップリンクを追加（アクセシビリティ向上）
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'メインコンテンツにスキップ';
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // メインコンテンツにIDを追加
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.id = 'main-content';
    }
});