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
        
        // 差分機能関連
        this.currentMode = 'standard'; // 'standard', 'difference', 'wordtree', 'cooccurrence'
        this.differenceColormaps = {};
        this.scienceTerms = {};
        this.lastStatistics = {};
        
        // Word Tree関連
        this.recommendedRoots = {};
        this.wordTreeData = null;
        
        // 共起ネットワーク関連
        this.cooccurrenceData = null;
        this.networkInstance = null;
        
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
            // 並列でデータ読み込み（差分機能データも含む）
            const [fontsData, textsData, fixedParamsData, stopWordsData, diffColormapsData, scienceTermsData, recommendedRootsData] = await Promise.all([
                fetch('/api/fonts').then(r => r.json()),
                fetch('/api/sample-texts').then(r => r.json()),
                fetch('/api/fixed-params').then(r => r.json()),
                fetch('/api/stop-words').then(r => r.json()),
                fetch('/api/difference-colormaps').then(r => r.json()),
                fetch('/api/science-terms').then(r => r.json()),
                fetch('/api/recommended-roots').then(r => r.json())
            ]);
            
            this.fonts = fontsData.fonts;
            this.sampleTexts = textsData.texts;
            this.fixedParams = fixedParamsData.fixed_params;
            this.accessibleColors = fixedParamsData.accessible_colors;
            this.stopWordCategories = stopWordsData.categories;
            this.differenceColormaps = diffColormapsData.colormaps;
            this.scienceTerms = scienceTermsData.science_terms;
            this.recommendedRoots = recommendedRootsData.recommended_roots;
            
            this.populateSelects();
            this.populateDifferenceSelects();
            this.populateWordTreeSelects();
            this.populateCooccurrenceSelects();
            
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
        
        // === 差分機能のイベントリスナー ===
        
        // 差分生成ボタン
        const diffGenerateBtn = document.getElementById('diffGenerateBtn');
        if (diffGenerateBtn) {
            diffGenerateBtn.addEventListener('click', () => {
                this.generateDifferenceWordCloud();
            });
        }
        
        // 差分設定変更時の自動更新（オプション）
        ['baseDataset', 'compareDataset', 'calculationMethod', 'differenceColormap'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    // 設定変更をログに記録
                    console.log(`差分設定変更: ${id} = ${element.value}`);
                });
            }
        });
        
        // 差分除外カテゴリーチェックボックス
        ['diffExcludeGeneral', 'diffExcludeThanks', 'diffExcludeSchool', 'diffExcludeExperiment'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    console.log(`差分除外カテゴリー変更: ${id} = ${checkbox.checked}`);
                });
            }
        });
        
        // 差分設定ボタン
        const diffExportBtn = document.getElementById('diffExportConfig');
        if (diffExportBtn) {
            diffExportBtn.addEventListener('click', () => {
                this.exportDifferenceConfig();
            });
        }
        
        const diffResetBtn = document.getElementById('diffResetBtn');
        if (diffResetBtn) {
            diffResetBtn.addEventListener('click', () => {
                this.resetDifferenceDefaults();
            });
        }
        
        // Word Tree関連イベント
        document.getElementById('wordtreeTextSource')?.addEventListener('change', (e) => {
            document.getElementById('wordtreeCustomTextGroup').style.display = 
                e.target.value === 'custom' ? 'block' : 'none';
        });
        
        document.getElementById('wordtreeGenerateBtn')?.addEventListener('click', () => {
            this.generateWordTree();
        });
        
        document.getElementById('wordtreeResetBtn')?.addEventListener('click', () => {
            this.resetWordTreeDefaults();
        });
        
        // 共起ネットワーク関連イベント
        document.getElementById('coocTextSource')?.addEventListener('change', (e) => {
            document.getElementById('coocCustomTextGroup').style.display = 
                e.target.value === 'custom' ? 'block' : 'none';
        });
        
        document.getElementById('coocGenerateBtn')?.addEventListener('click', () => {
            this.generateCooccurrenceNetwork();
        });
        
        document.getElementById('coocResetBtn')?.addEventListener('click', () => {
            this.resetCooccurrenceDefaults();
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
    
    // ===== 差分ワードクラウド機能 =====
    
    populateDifferenceSelects() {
        // 差分用フォント選択肢
        const diffFontSelect = document.getElementById('diffFontSelect');
        if (diffFontSelect) {
            diffFontSelect.innerHTML = '<option value="">デフォルト</option>';
            Object.entries(this.fonts).forEach(([key, font]) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = font.name;
                diffFontSelect.appendChild(option);
            });
        }
    }
    
    switchMode(mode) {
        this.currentMode = mode;
        
        // タブの状態更新
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        });
        
        const activeTab = document.getElementById(`${mode}-tab`);
        if (activeTab) {
            activeTab.classList.add('active');
            activeTab.setAttribute('aria-selected', 'true');
        }
        
        // パネルの表示切り替え
        document.querySelectorAll('.mode-panel').forEach(panel => {
            panel.style.display = 'none';
        });
        
        const activePanel = document.getElementById(`${mode}-panel`);
        if (activePanel) {
            activePanel.style.display = 'block';
        }
        
        // 統計情報の表示制御
        const statsInfo = document.getElementById('statisticsInfo');
        const metaInfo = document.getElementById('metaInfo');
        
        if (mode === 'difference') {
            if (statsInfo) statsInfo.style.display = 'none';
            if (metaInfo) metaInfo.style.display = 'none';
        } else {
            if (statsInfo) statsInfo.style.display = 'none';
            if (metaInfo) metaInfo.style.display = 'none';
        }
        
        // 歓迎メッセージの更新
        this.updateWelcomeMessage(mode);
        
        console.log(`モード切り替え: ${mode}`);
    }
    
    updateWelcomeMessage(mode) {
        const welcomeMessage = document.getElementById('welcomeMessage');
        if (!welcomeMessage) return;
        
        const icon = welcomeMessage.querySelector('i');
        const title = welcomeMessage.querySelector('h3');
        const description = welcomeMessage.querySelector('p');
        const button = welcomeMessage.querySelector('button');
        
        if (mode === 'difference') {
            icon.className = 'fas fa-balance-scale fa-3x';
            title.textContent = '差分ワードクラウド分析';
            description.textContent = '授業前後の語彙変化を可視化し、教育効果を定量的に分析します';
            button.innerHTML = '<i class="fas fa-balance-scale"></i> 差分分析を開始';
            button.onclick = () => this.generateDifferenceWordCloud();
        } else {
            icon.className = 'fas fa-filter fa-3x';
            title.textContent = '単語除外テスト版';
            description.textContent = '除外したい単語を選択して、より意味のあるワードクラウドを生成します';
            button.innerHTML = '<i class="fas fa-magic"></i> 分析を開始';
            button.onclick = () => this.generateWordCloud();
        }
    }
    
    async generateDifferenceWordCloud() {
        try {
            const generateBtn = document.getElementById('diffGenerateBtn');
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 差分分析中...';
            }
            
            // 差分設定の収集
            const config = this.collectDifferenceConfig();
            
            // 歓迎メッセージを非表示
            const welcomeMessage = document.getElementById('welcomeMessage');
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }
            
            // API呼び出し
            const response = await fetch('/api/difference-generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // ワードクラウド表示
                this.displayDifferenceResult(result.image, result.statistics);
                this.showToast('差分ワードクラウド生成完了', 'success');
            } else {
                this.showToast(result.error || '差分生成に失敗しました', 'error');
                if (welcomeMessage) {
                    welcomeMessage.style.display = 'block';
                }
            }
            
        } catch (error) {
            console.error('差分ワードクラウド生成エラー:', error);
            this.showToast('生成処理でエラーが発生しました', 'error');
        } finally {
            const generateBtn = document.getElementById('diffGenerateBtn');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-balance-scale"></i> 差分分析実行';
            }
        }
    }
    
    collectDifferenceConfig() {
        return {
            base_dataset: document.getElementById('baseDataset')?.value || 'q2_before',
            compare_dataset: document.getElementById('compareDataset')?.value || 'q2_after',
            calculation_method: document.getElementById('calculationMethod')?.value || 'frequency_difference',
            min_occurrence: parseInt(document.getElementById('minOccurrence')?.value || '1'),
            min_difference: parseFloat(document.getElementById('minDifference')?.value || '0.1'),
            science_highlight: document.getElementById('scienceHighlight')?.checked || false,
            
            // 除外カテゴリー
            exclude_categories: Array.from(document.querySelectorAll('#difference-panel input[type="checkbox"]:checked'))
                .map(cb => cb.value).filter(v => v !== 'on'),
            custom_exclude_words: document.getElementById('diffCustomExcludeWords')?.value || '',
            
            // 表示設定
            font: document.getElementById('diffFontSelect')?.value || '',
            width: parseInt(document.getElementById('diffWidth')?.value || '1200'),
            height: parseInt(document.getElementById('diffHeight')?.value || '800'),
            difference_colormap: document.getElementById('differenceColormap')?.value || 'difference_standard',
            background_color: '#f8f8f8'
        };
    }
    
    displayDifferenceResult(imageBase64, statistics) {
        // ワードクラウド画像表示
        const imgElement = document.getElementById('wordcloudImg');
        if (imgElement) {
            imgElement.src = `data:image/png;base64,${imageBase64}`;
            imgElement.style.display = 'block';
        }
        
        // 統計情報の保存と表示
        this.lastStatistics = statistics;
        this.displayStatistics(statistics);
        
        // 統計情報パネルを表示
        const statisticsInfo = document.getElementById('statisticsInfo');
        if (statisticsInfo) {
            statisticsInfo.style.display = 'block';
        }
    }
    
    displayStatistics(stats) {
        // 基本統計
        this.updateElement('statsTotalWords', 
            `${stats.total_words_base || 0} → ${stats.total_words_compare || 0}`);
        this.updateElement('statsUniqueWords', 
            `${stats.unique_words_base || 0} → ${stats.unique_words_compare || 0}`);
        
        // 語彙変化
        this.updateElement('statsNewWords', (stats.new_words || []).length);
        this.updateElement('statsLostWords', (stats.lost_words || []).length);
        this.updateElement('statsIncreasedWords', (stats.increased_words || []).length);
        this.updateElement('statsDecreasedWords', (stats.decreased_words || []).length);
        
        // 科学用語変化
        this.displayScienceTermChanges(stats.science_term_changes || {});
        
        // TOP変化語
        this.displayTopWords('topNewWords', stats.new_words || [], 'new');
        this.displayTopWords('topLostWords', stats.lost_words || [], 'lost');
    }
    
    displayScienceTermChanges(changes) {
        const container = document.getElementById('scienceTermsStats');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (Object.keys(changes).length === 0) {
            container.innerHTML = '<p class="no-data">科学用語の変化はありませんでした</p>';
            return;
        }
        
        Object.entries(changes).forEach(([term, data]) => {
            const termDiv = document.createElement('div');
            termDiv.className = 'science-term-stat';
            
            const change = data.change > 0 ? `+${data.change}` : `${data.change}`;
            const levelClass = data.level || 'basic';
            
            termDiv.innerHTML = `
                <span class="science-term-name">${term}</span>
                <div class="science-term-change">
                    <span class="change-before">${data.base}</span>
                    <span class="change-after">${data.compare}</span>
                    <span class="change-diff ${data.change > 0 ? 'increase' : 'decrease'}">${change}</span>
                </div>
            `;
            
            container.appendChild(termDiv);
        });
    }
    
    displayTopWords(containerId, words, type) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        const topWords = words.slice(0, 5);
        if (topWords.length === 0) {
            container.innerHTML = '<p class="no-data">データなし</p>';
            return;
        }
        
        topWords.forEach(([word, count]) => {
            const wordDiv = document.createElement('div');
            wordDiv.className = `word-item ${type}`;
            wordDiv.innerHTML = `
                <span class="word-name">${word}</span>
                <span class="word-count">${count}回</span>
            `;
            container.appendChild(wordDiv);
        });
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    exportDifferenceConfig() {
        const config = this.collectDifferenceConfig();
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '_').split('.')[0];
        const filename = `difference_config_${timestamp}.json`;
        
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showToast('差分設定をエクスポートしました', 'success');
    }
    
    resetDifferenceDefaults() {
        // 基準・比較データをデフォルトに戻す
        const baseDataset = document.getElementById('baseDataset');
        const compareDataset = document.getElementById('compareDataset');
        if (baseDataset) baseDataset.value = 'q2_before';
        if (compareDataset) compareDataset.value = 'q2_after';
        
        // 計算方法をデフォルトに戻す
        const calculationMethod = document.getElementById('calculationMethod');
        if (calculationMethod) calculationMethod.value = 'frequency_difference';
        
        // 閾値をデフォルトに戻す
        const minOccurrence = document.getElementById('minOccurrence');
        const minDifference = document.getElementById('minDifference');
        if (minOccurrence) minOccurrence.value = '1';
        if (minDifference) minDifference.value = '0.1';
        
        // 科学用語ハイライトをON
        const scienceHighlight = document.getElementById('scienceHighlight');
        if (scienceHighlight) scienceHighlight.checked = true;
        
        // 除外カテゴリーをデフォルトに戻す
        const diffExcludeGeneral = document.getElementById('diffExcludeGeneral');
        const diffExcludeThanks = document.getElementById('diffExcludeThanks');
        const diffExcludeSchool = document.getElementById('diffExcludeSchool');
        const diffExcludeExperiment = document.getElementById('diffExcludeExperiment');
        
        if (diffExcludeGeneral) diffExcludeGeneral.checked = true;
        if (diffExcludeThanks) diffExcludeThanks.checked = true;
        if (diffExcludeSchool) diffExcludeSchool.checked = false;
        if (diffExcludeExperiment) diffExcludeExperiment.checked = false;
        
        // カスタム除外単語をクリア
        const diffCustomExcludeWords = document.getElementById('diffCustomExcludeWords');
        if (diffCustomExcludeWords) diffCustomExcludeWords.value = '';
        
        // サイズをデフォルトに戻す
        const diffWidth = document.getElementById('diffWidth');
        const diffHeight = document.getElementById('diffHeight');
        if (diffWidth) diffWidth.value = '1200';
        if (diffHeight) diffHeight.value = '800';
        
        // カラーマップをデフォルトに戻す
        const differenceColormap = document.getElementById('differenceColormap');
        if (differenceColormap) differenceColormap.value = 'difference_standard';
        
        // フォントをデフォルトに戻す
        const diffFontSelect = document.getElementById('diffFontSelect');
        if (diffFontSelect) diffFontSelect.value = '';
        
        this.showToast('差分設定をリセットしました', 'success');
    }
    
    // モード切り替え
    switchMode(mode) {
        this.currentMode = mode;
        
        // すべてのタブボタンとパネルを取得
        const tabs = document.querySelectorAll('.tab-button');
        const panels = document.querySelectorAll('.mode-panel');
        
        // タブとパネルの表示を更新
        tabs.forEach(tab => {
            const tabMode = tab.id.replace('-tab', '');
            if (tabMode === mode) {
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');
            } else {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            }
        });
        
        panels.forEach(panel => {
            const panelMode = panel.id.replace('-panel', '');
            if (panelMode === mode) {
                panel.style.display = 'block';
            } else {
                panel.style.display = 'none';
            }
        });
        
        // プレビューコンテナの表示切り替え
        const previewImage = document.getElementById('previewImage');
        const wordTreeContainer = document.getElementById('wordTreeContainer');
        const cooccurrenceContainer = document.getElementById('cooccurrenceContainer');
        const statisticsInfo = document.getElementById('statisticsInfo');
        
        // すべて非表示にしてから、必要なものだけ表示
        [previewImage, wordTreeContainer, cooccurrenceContainer, statisticsInfo].forEach(el => {
            if (el) el.style.display = 'none';
        });
        
        // モードに応じた初期表示
        if (mode === 'wordtree' && this.wordTreeData) {
            wordTreeContainer.style.display = 'block';
        } else if (mode === 'cooccurrence' && this.cooccurrenceData) {
            cooccurrenceContainer.style.display = 'block';
        } else if ((mode === 'standard' || mode === 'difference') && previewImage.querySelector('img').src) {
            previewImage.style.display = 'block';
        }
    }
    
    // Word Tree関連メソッド
    populateWordTreeSelects() {
        // 除外カテゴリーチェックボックスを生成
        this.populateExcludeCategories('wordtreeExcludeCategories');
        
        // チェックボックス変更イベント
        const autoRootsCheckbox = document.getElementById('wordtreeAutoRoots');
        if (autoRootsCheckbox) {
            autoRootsCheckbox.addEventListener('change', (e) => {
                const customRootsGroup = document.getElementById('customRootsGroup');
                const recommendedRootsInfo = document.getElementById('recommendedRootsInfo');
                if (e.target.checked) {
                    customRootsGroup.style.display = 'none';
                    recommendedRootsInfo.style.display = 'block';
                } else {
                    customRootsGroup.style.display = 'block';
                    recommendedRootsInfo.style.display = 'none';
                }
            });
        }
    }
    
    async generateWordTree() {
        const config = this.collectWordTreeConfig();
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/word-tree-generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayWordTree(data.trees, data.statistics);
                this.showToast('Word Treeを生成しました', 'success');
            } else {
                this.showError(data.error || 'Word Tree生成に失敗しました');
            }
        } catch (error) {
            console.error('Word Tree生成エラー:', error);
            this.showError('Word Tree生成中にエラーが発生しました');
        } finally {
            this.hideLoading();
        }
    }
    
    collectWordTreeConfig() {
        const config = {
            text_source: document.getElementById('wordtreeTextSource').value,
            custom_text: document.getElementById('wordtreeCustomText').value,
            auto_select_roots: document.getElementById('wordtreeAutoRoots').checked,
            custom_roots: document.getElementById('wordtreeCustomRoots').value,
            max_roots: parseInt(document.getElementById('wordtreeMaxRoots').value),
            tree_depth: parseInt(document.getElementById('wordtreeDepth').value),
            custom_exclude_words: document.getElementById('wordtreeCustomExclude').value
        };
        
        // 除外カテゴリー収集
        const excludeCategories = [];
        document.querySelectorAll('#wordtreeExcludeCategories input[type="checkbox"]:checked').forEach(checkbox => {
            excludeCategories.push(checkbox.value);
        });
        config.exclude_categories = excludeCategories;
        
        return config;
    }
    
    displayWordTree(trees, statistics) {
        const container = document.getElementById('wordTreeContainer');
        container.innerHTML = '';
        container.style.display = 'block';
        
        // 統計情報表示
        const statsDiv = document.createElement('div');
        statsDiv.className = 'network-stats';
        statsDiv.innerHTML = `
            <div class="network-stat-item">
                <span class="network-stat-value">${trees.length}</span>
                <span class="network-stat-label">ツリー数</span>
            </div>
            <div class="network-stat-item">
                <span class="network-stat-value">${statistics.total_contexts}</span>
                <span class="network-stat-label">総文脈数</span>
            </div>
        `;
        container.appendChild(statsDiv);
        
        // 各Word Treeを描画
        trees.forEach((treeData, index) => {
            const treeContainer = document.createElement('div');
            treeContainer.className = 'word-tree-container';
            treeContainer.id = `wordTree${index}`;
            
            const title = document.createElement('div');
            title.className = 'word-tree-title';
            title.textContent = `「${treeData.word}」の文脈 (${treeData.count}回出現)`;
            treeContainer.appendChild(title);
            
            const svgContainer = document.createElement('div');
            svgContainer.style.width = '100%';
            svgContainer.style.height = '400px';
            treeContainer.appendChild(svgContainer);
            
            container.appendChild(treeContainer);
            
            // D3.jsでWord Treeを描画
            this.drawWordTree(svgContainer, treeData);
        });
        
        this.wordTreeData = trees;
    }
    
    drawWordTree(container, treeData) {
        // コンテナのサイズを取得
        const width = container.offsetWidth;
        const height = 400;
        
        // SVG作成
        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        const g = svg.append('g')
            .attr('transform', 'translate(100, 200)');
        
        // 階層レイアウト
        const tree = d3.tree()
            .size([height - 100, width - 200]);
        
        // 階層データに変換
        const root = d3.hierarchy(treeData);
        const treeLayout = tree(root);
        
        // リンク描画
        g.selectAll('.word-tree-link')
            .data(treeLayout.links())
            .enter()
            .append('path')
            .attr('class', 'word-tree-link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));
        
        // ノード描画
        const nodes = g.selectAll('.word-tree-node')
            .data(treeLayout.descendants())
            .enter()
            .append('g')
            .attr('class', d => `word-tree-node ${d.depth === 0 ? 'root' : d.children ? 'internal' : 'leaf'}`)
            .attr('transform', d => `translate(${d.y}, ${d.x})`);
        
        // ノードの円
        nodes.append('circle')
            .attr('r', 4)
            .style('fill', d => d.depth === 0 ? this.accessibleColors.orange : this.accessibleColors.blue);
        
        // テキストラベル
        nodes.append('text')
            .attr('dx', d => d.children ? -10 : 10)
            .attr('dy', 3)
            .style('text-anchor', d => d.children ? 'end' : 'start')
            .text(d => d.data.word || d.data.name)
            .style('font-size', d => d.depth === 0 ? '16px' : '14px')
            .style('font-weight', d => d.depth === 0 ? 'bold' : 'normal');
        
        // ツールチップ
        nodes.append('title')
            .text(d => `${d.data.word}: ${d.data.count}回`);
    }
    
    // 共起ネットワーク関連メソッド
    populateCooccurrenceSelects() {
        // 除外カテゴリーチェックボックスを生成
        this.populateExcludeCategories('coocExcludeCategories');
        
        // スライダーイベント
        const windowSizeSlider = document.getElementById('coocWindowSize');
        const windowSizeValue = document.getElementById('coocWindowSizeValue');
        if (windowSizeSlider && windowSizeValue) {
            windowSizeSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                windowSizeValue.textContent = value === 0 ? '文内共起' : `前後${value}語`;
            });
        }
        
        const maxNodesSlider = document.getElementById('coocMaxNodes');
        const maxNodesValue = document.getElementById('coocMaxNodesValue');
        if (maxNodesSlider && maxNodesValue) {
            maxNodesSlider.addEventListener('input', (e) => {
                maxNodesValue.textContent = e.target.value;
            });
        }
    }
    
    async generateCooccurrenceNetwork() {
        const config = this.collectCooccurrenceConfig();
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/cooccurrence-generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayCooccurrenceNetwork(data.network, data.statistics);
                this.showToast('共起ネットワークを生成しました', 'success');
            } else {
                this.showError(data.error || '共起ネットワーク生成に失敗しました');
            }
        } catch (error) {
            console.error('共起ネットワーク生成エラー:', error);
            this.showError('共起ネットワーク生成中にエラーが発生しました');
        } finally {
            this.hideLoading();
        }
    }
    
    collectCooccurrenceConfig() {
        const windowSize = parseInt(document.getElementById('coocWindowSize').value);
        const config = {
            text_source: document.getElementById('coocTextSource').value,
            custom_text: document.getElementById('coocCustomText').value,
            window_size: windowSize === 0 ? null : windowSize,
            association_method: document.getElementById('coocAssociationMethod').value,
            min_edge_weight: parseInt(document.getElementById('coocMinEdgeWeight').value),
            min_node_freq: parseInt(document.getElementById('coocMinNodeFreq').value),
            max_nodes: parseInt(document.getElementById('coocMaxNodes').value),
            custom_exclude_words: document.getElementById('coocCustomExclude').value
        };
        
        // 除外カテゴリー収集
        const excludeCategories = [];
        document.querySelectorAll('#coocExcludeCategories input[type="checkbox"]:checked').forEach(checkbox => {
            excludeCategories.push(checkbox.value);
        });
        config.exclude_categories = excludeCategories;
        
        return config;
    }
    
    displayCooccurrenceNetwork(networkData, statistics) {
        const container = document.getElementById('cooccurrenceContainer');
        container.innerHTML = '';
        container.style.display = 'block';
        
        // 統計情報表示
        const statsDiv = document.createElement('div');
        statsDiv.className = 'network-stats';
        statsDiv.innerHTML = `
            <div class="network-stat-item">
                <span class="network-stat-value">${statistics.total_nodes}</span>
                <span class="network-stat-label">ノード数</span>
            </div>
            <div class="network-stat-item">
                <span class="network-stat-value">${statistics.total_edges}</span>
                <span class="network-stat-label">エッジ数</span>
            </div>
            <div class="network-stat-item">
                <span class="network-stat-value">${(statistics.density * 100).toFixed(1)}%</span>
                <span class="network-stat-label">密度</span>
            </div>
            <div class="network-stat-item">
                <span class="network-stat-value">${statistics.average_degree.toFixed(1)}</span>
                <span class="network-stat-label">平均次数</span>
            </div>
        `;
        container.appendChild(statsDiv);
        
        // ネットワーク描画エリア
        const networkDiv = document.createElement('div');
        networkDiv.id = 'network-visualization';
        networkDiv.style.height = '500px';
        networkDiv.style.border = '1px solid #ddd';
        networkDiv.style.borderRadius = '8px';
        networkDiv.style.marginTop = '20px';
        container.appendChild(networkDiv);
        
        // vis.jsでネットワークを描画
        this.drawCooccurrenceNetwork(networkDiv, networkData);
        
        this.cooccurrenceData = networkData;
    }
    
    drawCooccurrenceNetwork(container, data) {
        // vis.js用のデータセット
        const nodes = new vis.DataSet(data.nodes);
        const edges = new vis.DataSet(data.edges);
        
        // ネットワークオプション
        const options = {
            nodes: {
                shape: 'dot',
                scaling: {
                    min: 10,
                    max: 50,
                    label: {
                        min: 12,
                        max: 24,
                        drawThreshold: 8,
                        maxVisible: 30
                    }
                },
                font: {
                    face: 'Yu Gothic UI, Meiryo UI, sans-serif',
                    color: '#333'
                }
            },
            edges: {
                smooth: {
                    type: 'continuous'
                },
                scaling: {
                    min: 1,
                    max: 5
                }
            },
            physics: {
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08
                },
                maxVelocity: 50,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {
                    iterations: 150
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true
            }
        };
        
        // ネットワーク作成
        this.networkInstance = new vis.Network(container, { nodes, edges }, options);
        
        // クリックイベント
        this.networkInstance.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                console.log('選択ノード:', node);
            }
        });
    }
    
    // 共通メソッド
    populateExcludeCategories(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '<h4>除外する単語カテゴリー:</h4>';
        const checkboxContainer = document.createElement('div');
        checkboxContainer.className = 'category-checkboxes';
        
        Object.entries(this.stopWordCategories).forEach(([key, data]) => {
            const label = document.createElement('label');
            label.className = 'checkbox-label';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = key;
            checkbox.checked = key === 'general' || key === 'thanks';
            
            const text = document.createElement('span');
            text.innerHTML = `<strong>${data.name}</strong><br><small>例: ${data.words.slice(0, 3).join(', ')}...</small>`;
            
            label.appendChild(checkbox);
            label.appendChild(text);
            checkboxContainer.appendChild(label);
        });
        
        container.appendChild(checkboxContainer);
    }
    
    // リセットメソッド
    resetWordTreeDefaults() {
        document.getElementById('wordtreeTextSource').value = 'all_responses';
        document.getElementById('wordtreeCustomText').value = '';
        document.getElementById('wordtreeAutoRoots').checked = true;
        document.getElementById('wordtreeCustomRoots').value = '';
        document.getElementById('wordtreeMaxRoots').value = '3';
        document.getElementById('wordtreeDepth').value = '3';
        document.getElementById('wordtreeCustomExclude').value = '';
        
        // 除外カテゴリーをデフォルトに
        document.querySelectorAll('#wordtreeExcludeCategories input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = checkbox.value === 'general' || checkbox.value === 'thanks';
        });
        
        // カスタムルート語グループの表示制御
        document.getElementById('customRootsGroup').style.display = 'none';
        document.getElementById('recommendedRootsInfo').style.display = 'block';
        
        this.showToast('Word Tree設定をリセットしました', 'success');
    }
    
    resetCooccurrenceDefaults() {
        document.getElementById('coocTextSource').value = 'all_responses';
        document.getElementById('coocCustomText').value = '';
        document.getElementById('coocWindowSize').value = '0';
        document.getElementById('coocWindowSizeValue').textContent = '文内共起';
        document.getElementById('coocAssociationMethod').value = 'pmi';
        document.getElementById('coocMinEdgeWeight').value = '2';
        document.getElementById('coocMinNodeFreq').value = '3';
        document.getElementById('coocMaxNodes').value = '50';
        document.getElementById('coocMaxNodesValue').textContent = '50';
        document.getElementById('coocCustomExclude').value = '';
        
        // 除外カテゴリーをデフォルトに
        document.querySelectorAll('#coocExcludeCategories input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = checkbox.value === 'general' || checkbox.value === 'thanks';
        });
        
        this.showToast('共起ネットワーク設定をリセットしました', 'success');
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

// 差分機能のグローバル関数
function switchMode(mode) {
    if (window.wordCloudAppV2) {
        window.wordCloudAppV2.switchMode(mode);
    }
}