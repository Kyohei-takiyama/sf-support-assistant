import { LightningElement, api, track } from 'lwc';
import analyzeCaseAndGetSupport from '@salesforce/apex/SupportAssistantController.analyzeCaseAndGetSupport';
import getCaseDetails from '@salesforce/apex/SupportAssistantController.getCaseDetails';
import saveChatMessage from '@salesforce/apex/SupportChatHistoryController.saveChatMessage';
import getChatHistory from '@salesforce/apex/SupportChatHistoryController.getChatHistory';

export default class SupportAssistant extends LightningElement {
    @api recordId;
    @track caseRecord;
    @track similarCases = [];
    @track externalInfo = [];
    @track externalImages = [];
    @track chatHistory = [];
    @track currentMessage = '';
    @track isLoading = true;
    @track isSending = false;
    @track error;

    async connectedCallback() {
        console.log('Support Assistant connected with recordId:', this.recordId);
        // レコードページではrecordIdが自動的に設定される
        if (this.recordId) {
            // チャット履歴を読み込み
            await this.loadChatHistory();
            // ケースを分析
            this.loadCaseAndAnalyze();
        }
    }

    async loadCaseAndAnalyze() {
        try {
            this.isLoading = true;
            this.error = null;

            console.log('Loading case details for recordId:', this.recordId);

            // ケース詳細を取得
            this.caseRecord = await getCaseDetails({ caseId: this.recordId });
            console.log('Case Record:', JSON.stringify(this.caseRecord));

            const firstQuestion = `次のケースについて、問題を解決するにはどうすればよいですか？。ケースの内容: ${this.caseRecord.Description || '説明がありません。'}`;

            // 初回分析を実行
            const response = await analyzeCaseAndGetSupport({
                caseId: this.recordId,
                question: firstQuestion
            });

            console.log('API Response:', response);

            // JSON文字列をパースして処理
            const parsedResponse = JSON.parse(response);
            this.processApiResponse(parsedResponse);

            // 初回のみAI応答をチャット履歴に追加（履歴が空の場合）
            if (this.chatHistory.length === 0) {
                if (parsedResponse.ai_response) {
                    await this.addToChatHistory('assistant', parsedResponse.ai_response);
                } else {
                    await this.addToChatHistory('system', 'ケースの分析が完了しました。質問がある場合は入力してください。');
                }
            }

        } catch (error) {
            this.error = 'ケースの分析中にエラーが発生しました: ' + error.body?.message || error.message;
        } finally {
            this.isLoading = false;
        }
    }

    processApiResponse(apiResponse) {
        // ケース分析情報から類似ケースを処理
        console.log('Processing API Response - case_analysis:', JSON.stringify(apiResponse.case_analysis));

        if (apiResponse.case_analysis && apiResponse.case_analysis.similar_cases) {
            const similarCases = apiResponse.case_analysis.similar_cases;
            console.log('Similar Cases from API:', JSON.stringify(similarCases));
            console.log('Current recordId:', this.recordId);

            if (Array.isArray(similarCases) && similarCases.length > 0) {
                // 現在のレコードIDと一致するケースを除外
                const filteredSimilarCases = similarCases.filter(sc => sc.Id !== this.recordId);
                console.log('Filtered Similar Cases:', JSON.stringify(filteredSimilarCases));

                this.similarCases = filteredSimilarCases.map(sc => ({
                    ...sc,
                    url: `/lightning/r/Case/${sc.Id}/view`,
                    similarity: sc.similarity ? Math.round(sc.similarity * 100) : 0
                }));
                console.log('Final similarCases:', JSON.stringify(this.similarCases));
            } else {
                console.log('No similar cases found or empty array');
                this.similarCases = [];
            }
        } else {
            console.log('No case_analysis or similar_cases in API response');
            this.similarCases = [];
        }

        // 外部情報
        if (apiResponse.external_info && apiResponse.external_info.results && apiResponse.external_info.results.results) {
            const externalResults = apiResponse.external_info.results.results;
            if (Array.isArray(externalResults)) {
                this.externalInfo = externalResults.map(info => ({
                    title: info.title || '無題',
                    url: info.url || '#',
                    similarity: info.score ? Math.floor(info.score * 100) : 0
                }));
            }
        } else {
            this.externalInfo = [];
        }

        // 外部情報の画像
        if (apiResponse.external_info && apiResponse.external_info.results && apiResponse.external_info.results.images) {
            const images = apiResponse.external_info.results.images;
            if (Array.isArray(images)) {
                this.externalImages = images.map((image, index) => ({
                    id: index.toString(),
                    src: image.url,
                    header: `画像 ${index + 1}`,
                    description: this.truncateText(image.description || '関連する画像です', 50),
                    alternativeText: image.description || `関連画像 ${index + 1}`
                }));
            }
        } else {
            this.externalImages = [];
        }
    }

    async loadChatHistory() {
        try {
            const chatHistory = await getChatHistory({ caseId: this.recordId });
            this.chatHistory = chatHistory || [];
        } catch (error) {
            console.error('Error loading chat history:', error);
            this.chatHistory = [];
        }
    }

    async saveChatToHistory(messageText, messageType) {
        try {
            await saveChatMessage({
                caseId: this.recordId,
                messageText: messageText,
                messageType: messageType
            });
        } catch (error) {
            console.error('Error saving chat message:', error);
        }
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }

    handleMessageChange(event) {
        this.currentMessage = event.detail.value;
    }

    async handleSendMessage() {
        if (!this.currentMessage.trim()) {
            return;
        }

        const userMessage = this.currentMessage;
        this.currentMessage = '';
        this.isSending = true;
        this.error = null;

        // ユーザーメッセージを追加
        this.addToChatHistory('user', userMessage);

        try {
            // APIを呼び出し
            const response = await analyzeCaseAndGetSupport({
                caseId: this.recordId,
                question: userMessage
            });

            // JSON文字列をパースして処理
            const parsedResponse = JSON.parse(response);
            this.processApiResponse(parsedResponse);

            // AIレスポンスを追加
            if (parsedResponse.ai_response) {
                this.addToChatHistory('assistant', parsedResponse.ai_response);
            }

        } catch (error) {
            this.error = 'メッセージの送信中にエラーが発生しました: ' + error.body?.message || error.message;
            this.addToChatHistory('error', 'エラーが発生しました。もう一度お試しください。');
        } finally {
            this.isSending = false;
        }
    }

    async addToChatHistory(type, text) {
        const timestamp = new Date().toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const message = {
            id: Date.now().toString(),
            type: type,
            text: text,
            timestamp: timestamp,
            isUser: type === 'user',
            containerClass: this.getContainerClass(type),
            messageClass: this.getMessageClass(type)
        };

        this.chatHistory = [...this.chatHistory, message];

        // Salesforceにチャット履歴を保存
        await this.saveChatToHistory(text, type);

        // チャット履歴を自動スクロール
        setTimeout(() => {
            const chatContainer = this.template.querySelector('.slds-scrollable_y');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }, 100);
    }

    getContainerClass(type) {
        if (type === 'user') {
            return 'slds-m-bottom_small slds-text-align_right';
        }
        return 'slds-m-bottom_small';
    }

    getMessageClass(type) {
        const baseClass = 'slds-box slds-box_x-small slds-p-around_small';
        if (type === 'user') {
            return baseClass + ' slds-theme_shade';
        } else if (type === 'error') {
            return baseClass + ' slds-theme_error';
        }
        return baseClass;
    }

    get hasSimilarCases() {
        const result = this.similarCases && this.similarCases.length > 0;
        console.log('hasSimilarCases getter called:', {
            similarCases: this.similarCases,
            length: this.similarCases ? this.similarCases.length : 'undefined',
            result: result
        });
        return result;
    }

    get hasExternalInfo() {
        return this.externalInfo && this.externalInfo.length > 0;
    }

    get hasExternalImages() {
        return this.externalImages && this.externalImages.length > 0;
    }

    get isSendDisabled() {
        return this.isSending || !this.currentMessage.trim();
    }
}