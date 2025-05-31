// 日本語ワードクラウド設定ツール - メインJavaScript

class WordCloudApp {
    constructor() {
        this.currentConfig = {};
        this.fonts = {};
        this.sampleTexts = {};
        this.colormaps = [];
        this.presets = {};
        this.autoUpdateEnabled = true;
        this.generateTimeout = null;
        
        this.init();
    }
    
    async init() {
        await this.loadInitialData();
        this.setupEventListeners();
        this.setupRangeSliders();
        this.loadDefaultConfig();
        
        // 初期状態で歓迎メッセージを表示
        this.showWelcomeMessage();
        
        console.log('📊 ワードクラウドアプリ初期化完了');
    }
    
    async loadInitialData() {
        try {
            // 並列でデータ読み込み
            const [fontsData, textsData, colormapsData, presetsData] = await Promise.all([
                fetch('/api/fonts').then(r => r.json()),
                fetch('/api/sample-texts').then(r => r.json()),
                fetch('/api/colormaps').then(r => r.json()),
                fetch('/api/presets').then(r => r.json())
            ]);
            
            this.fonts = fontsData.fonts;
            this.sampleTexts = textsData.texts;
            this.colormaps = colormapsData.colormaps;
            this.presets = presetsData.presets;
            
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
        
        // カラーマップ選択肢
        const colormapSelect = document.getElementById('colormap');
        colormapSelect.innerHTML = '';
        
        this.colormaps.forEach(colormap => {
            const option = document.createElement('option');
            option.value = colormap;
            option.textContent = colormap;
            colormapSelect.appendChild(option);
        });
        
        // プリセット選択肢
        const presetSelect = document.getElementById('presetSelect');
        presetSelect.innerHTML = '<option value="">プリセット選択...</option>';
        
        Object.entries(this.presets).forEach(([key, preset]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = preset.name;
            presetSelect.appendChild(option);
        });
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
        
        // 全ての設定コントロールに変更イベント
        const controls = [
            'fontSelect', 'width', 'height', 'maxWords', 'backgroundColor', 
            'colormap', 'minFontSize', 'maxFontSize', 'relativeScaling', 
            'preferHorizontal', 'collocations'
        ];
        
        controls.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.scheduleGeneration());
                
                // 数値入力の場合は即座に反映
                if (element.type === 'number') {
                    element.addEventListener('input', () => this.scheduleGeneration());
                }
            }
        });
        
        // 背景色ピッカー
        document.getElementById('backgroundColorPicker').addEventListener('change', (e) => {
            document.getElementById('backgroundColor').value = e.target.value;
            this.scheduleGeneration();
        });
        
        // ボタンイベント
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateWordCloud();
        });
        
        document.getElementById('autoUpdate').addEventListener('click', () => {
            this.toggleAutoUpdate();
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
        
        // プリセット選択
        document.getElementById('presetSelect').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPreset(e.target.value);
            }
        });
    }
    
    setupRangeSliders() {
        const sliders = [
            'minFontSize', 'maxFontSize', 'maxWords', 
            'relativeScaling', 'preferHorizontal'
        ];
        
        sliders.forEach(id => {
            const slider = document.getElementById(id);
            const valueSpan = document.getElementById(id + 'Value');
            
            if (slider && valueSpan) {
                slider.addEventListener('input', (e) => {
                    valueSpan.textContent = e.target.value;
                    this.scheduleGeneration();
                });
            }
        });
    }
    
    handleTextSourceChange(source) {
        const customGroup = document.getElementById('customTextGroup');
        
        if (source === 'custom') {
            customGroup.style.display = 'block';
        } else {
            customGroup.style.display = 'none';
            this.scheduleGeneration();
        }
    }
    
    loadDefaultConfig() {
        // デフォルト設定をUIに反映
        const defaults = {
            text_source: 'science_education',
            font: Object.keys(this.fonts)[0] || 'default',
            width: 800,
            height: 400,
            max_words: 100,
            background_color: 'white',
            colormap: 'viridis',
            min_font_size: 10,
            max_font_size: 100,
            relative_scaling: 0.5,
            prefer_horizontal: 0.7,
            collocations: false
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
                
                // レンジスライダーの値も更新
                if (element.type === 'range') {
                    const valueSpan = document.getElementById(element.id + 'Value');
                    if (valueSpan) {
                        valueSpan.textContent = value;
                    }
                }
            }
        });
        
        // テキストソースに応じてカスタムテキストエリアの表示切り替え
        this.handleTextSourceChange(config.text_source || 'science_education');
    }
    
    toCamelCase(str) {
        return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    }
    
    toSnakeCase(str) {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    }
    
    getCurrentConfig() {
        const config = {};
        
        // すべての設定を収集
        const controls = {
            textSource: 'text_source',
            customText: 'custom_text',
            fontSelect: 'font',
            width: 'width',
            height: 'height',
            maxWords: 'max_words',
            backgroundColor: 'background_color',
            colormap: 'colormap',
            minFontSize: 'min_font_size',
            maxFontSize: 'max_font_size',
            relativeScaling: 'relative_scaling',
            preferHorizontal: 'prefer_horizontal',
            collocations: 'collocations'
        };
        
        Object.entries(controls).forEach(([elementId, configKey]) => {
            const element = document.getElementById(elementId);
            if (element) {
                if (element.type === 'checkbox') {
                    config[configKey] = element.checked;
                } else if (element.type === 'number' || element.type === 'range') {
                    config[configKey] = parseFloat(element.value);
                } else {
                    config[configKey] = element.value;
                }
            }
        });
        
        return config;
    }
    
    scheduleGeneration() {
        if (!this.autoUpdateEnabled) return;
        
        // デバウンス: 500ms後に生成
        clearTimeout(this.generateTimeout);
        this.generateTimeout = setTimeout(() => {
            this.generateWordCloud();
        }, 500);
    }
    
    async generateWordCloud() {
        const config = this.getCurrentConfig();
        this.currentConfig = config;
        
        this.showLoading();
        
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
            } else {
                this.showError(result.error);
                this.showToast(`エラー: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('生成エラー:', error);
            this.showError('ネットワークエラーが発生しました');
            this.showToast('ネットワークエラーが発生しました', 'error');
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
        
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('previewImage').style.display = 'block';
        document.getElementById('welcomeMessage').style.display = 'none';
        document.getElementById('metaInfo').style.display = 'block';
        document.getElementById('downloadImage').style.display = 'inline-flex';
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
        document.getElementById('metaWords').textContent = config.max_words;
        document.getElementById('metaColormap').textContent = config.colormap;
    }
    
    toggleAutoUpdate() {
        this.autoUpdateEnabled = !this.autoUpdateEnabled;
        const button = document.getElementById('autoUpdate');
        
        if (this.autoUpdateEnabled) {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-sync"></i> 自動更新';
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-pause"></i> 手動更新';
        }
        
        this.showToast(
            this.autoUpdateEnabled ? '自動更新を有効にしました' : '自動更新を無効にしました',
            'info'
        );
    }
    
    resetToDefaults() {
        if (confirm('設定をデフォルトに戻しますか？')) {
            this.loadDefaultConfig();
            this.showToast('設定をリセットしました', 'info');
            
            if (this.autoUpdateEnabled) {
                this.scheduleGeneration();
            }
        }
    }
    
    loadPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (preset) {
            this.applyConfigToUI(preset.config);
            this.showToast(`プリセット「${preset.name}」を適用しました`, 'info');
            
            if (this.autoUpdateEnabled) {
                this.scheduleGeneration();
            }
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
            link.download = 'wordcloud.png';
            link.href = img.src;
            link.click();
            
            this.showToast('画像をダウンロードしました', 'success');
        }
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
        
        // 表示
        toast.classList.add('show');
        
        // 3秒後に非表示
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// グローバル関数（HTMLから呼び出し可能）
function generateWordCloud() {
    if (window.wordCloudApp) {
        window.wordCloudApp.generateWordCloud();
    }
}

// DOM読み込み完了後にアプリ初期化
document.addEventListener('DOMContentLoaded', () => {
    window.wordCloudApp = new WordCloudApp();
});