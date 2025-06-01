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
            'fontSelect', 'width', 'height', 'maxWords', 'backgroundBrightness', 
            'colormap', 'minFontSize', 'maxFontSize', 'relativeScaling', 
            'preferHorizontal', 'collocations', 'useCustomColors'
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
        
        // 背景色明度スライダー
        document.getElementById('backgroundBrightness').addEventListener('input', (e) => {
            this.updateBackgroundPreview(e.target.value);
            this.scheduleGeneration();
        });
        
        // カスタムカラーマップのチェックボックス
        document.getElementById('useCustomColors').addEventListener('change', (e) => {
            this.handleCustomColorsToggle(e.target.checked);
        });
        
        // 3色系統の選択イベント
        ['orangeColor', 'grayColor', 'blueColor'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                if (document.getElementById('useCustomColors').checked) {
                    this.scheduleGeneration();
                }
            });
        });
        
        // カスタムカラープレビューボタン
        document.getElementById('previewCustomColors').addEventListener('click', () => {
            this.previewCustomColors();
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
        
        document.getElementById('copyToClipboard').addEventListener('click', () => {
            this.copyConfigToClipboard();
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
            'relativeScaling', 'preferHorizontal', 'backgroundBrightness'
        ];
        
        sliders.forEach(id => {
            const slider = document.getElementById(id);
            const valueSpan = document.getElementById(id + 'Value');
            
            if (slider && valueSpan) {
                slider.addEventListener('input', (e) => {
                    if (id === 'backgroundBrightness') {
                        valueSpan.textContent = e.target.value + '%';
                        this.updateBackgroundPreview(e.target.value);
                    } else {
                        valueSpan.textContent = e.target.value;
                    }
                    this.scheduleGeneration();
                });
            }
        });
        
        // 初期背景色プレビューを設定（スライダー値50 = 95%明度）
        this.updateBackgroundPreview(50);
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
            text_source: 'all_responses',
            font: Object.keys(this.fonts)[0] || 'default',
            width: 1000,
            height: 600,
            max_words: 60,
            background_brightness: 50,  // スライダー値50 = 実際の95%明度
            colormap: 'orange_blue',
            min_font_size: 16,
            max_font_size: 90,
            relative_scaling: 0.6,
            prefer_horizontal: 0.8,
            collocations: false,
            use_custom_colors: false
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
        this.handleTextSourceChange(config.text_source || 'all_responses');
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
            backgroundBrightness: 'background_brightness',
            colormap: 'colormap',
            minFontSize: 'min_font_size',
            maxFontSize: 'max_font_size',
            relativeScaling: 'relative_scaling',
            preferHorizontal: 'prefer_horizontal',
            collocations: 'collocations',
            useCustomColors: 'use_custom_colors'
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
        
        // 背景色を明度から生成（スライダー値を実際の明度に変換）
        const sliderValue = config.background_brightness || 50;
        config.background_color = this.brightnessToHex(sliderValue);
        
        // カスタムカラーが有効な場合、3色系統からカスタムカラーを収集
        if (config.use_custom_colors) {
            config.custom_colors = [
                document.getElementById('orangeColor').value,
                document.getElementById('grayColor').value,
                document.getElementById('blueColor').value
            ];
            config.colormap = 'custom';
        }
        
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
    
    handleCustomColorsToggle(enabled) {
        const customColorGroup = document.getElementById('customColorGroup');
        if (enabled) {
            customColorGroup.style.display = 'block';
            customColorGroup.classList.add('show');
            this.showToast('カスタムカラーマップを有効にしました', 'info');
        } else {
            customColorGroup.classList.remove('show');
            setTimeout(() => {
                customColorGroup.style.display = 'none';
            }, 400);
            this.showToast('カスタムカラーマップを無効にしました', 'info');
        }
        
        if (this.autoUpdateEnabled) {
            this.scheduleGeneration();
        }
    }
    
    brightnessToHex(brightness) {
        // スライダー値（0-100）を明るいグレー範囲（90-100%）にマッピング
        const actualBrightness = 90 + (brightness / 100) * 10;  // 90% - 100%の範囲
        const value = Math.round((actualBrightness / 100) * 255);
        const hex = value.toString(16).padStart(2, '0');
        return `#${hex}${hex}${hex}`;
    }
    
    updateBackgroundPreview(brightness) {
        const preview = document.getElementById('backgroundPreview');
        const hexColor = this.brightnessToHex(brightness);
        
        if (preview) {
            preview.style.backgroundColor = hexColor;
        }
        
        // 実際の明度値を表示（90-100%の範囲）
        const valueSpan = document.getElementById('backgroundBrightnessValue');
        if (valueSpan) {
            const actualBrightness = 90 + (brightness / 100) * 10;
            valueSpan.textContent = actualBrightness.toFixed(1) + '%';
        }
    }
    
    previewCustomColors() {
        const orangeColor = document.getElementById('orangeColor').value;
        const grayColor = document.getElementById('grayColor').value;  
        const blueColor = document.getElementById('blueColor').value;
        
        const colors = [orangeColor, grayColor, blueColor];
        
        this.showToast(`カスタムカラー: オレンジ系(${orangeColor}) グレー系(${grayColor}) ブルー系(${blueColor})`, 'info');
        
        // カスタムカラーマップを使用するようにチェック
        document.getElementById('useCustomColors').checked = true;
        this.handleCustomColorsToggle(true);
        
        if (this.autoUpdateEnabled) {
            this.scheduleGeneration();
        }
    }
    
    async copyConfigToClipboard() {
        try {
            const config = this.getCurrentConfig();
            
            // JSON形式で設定をフォーマット
            const configJson = JSON.stringify(config, null, 2);
            
            // クリップボード API を使用
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(configJson);
                this.showToast('設定をクリップボードにコピーしました', 'success');
            } else {
                // フォールバック: テキストエリアを使用
                const textArea = document.createElement('textarea');
                textArea.value = configJson;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    this.showToast('設定をクリップボードにコピーしました', 'success');
                } catch (err) {
                    this.showToast('クリップボードへのコピーに失敗しました', 'error');
                }
                
                document.body.removeChild(textArea);
            }
            
        } catch (error) {
            console.error('クリップボードコピーエラー:', error);
            this.showToast('クリップボードへのコピーに失敗しました', 'error');
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
        
        // アクセシビリティ向上のためaria-live属性を追加
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');
        
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