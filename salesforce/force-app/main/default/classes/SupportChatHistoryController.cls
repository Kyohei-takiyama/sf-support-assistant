public with sharing class SupportChatHistoryController {

    @AuraEnabled
    public static void saveChatMessage(String caseId, String messageText, String messageType) {
        try {
            // チャット履歴をケースコメントとして保存
            CaseComment comment = new CaseComment();
            comment.ParentId = caseId;
            comment.CommentBody = '[' + messageType.toUpperCase() + '] ' + messageText;
            comment.IsPublished = false; // 内部コメントとして保存

            insert comment;
        } catch (Exception e) {
            throw new AuraHandledException('Error saving chat message: ' + e.getMessage());
        }
    }

    @AuraEnabled
    public static List<ChatMessage> getChatHistory(String caseId) {
        try {
            List<ChatMessage> chatHistory = new List<ChatMessage>();

            // ケースコメントからチャット履歴を取得
            List<CaseComment> comments = [
                SELECT Id, CommentBody, CreatedDate, CreatedBy.Name
                FROM CaseComment
                WHERE ParentId = :caseId
                AND (CommentBody LIKE '[USER]%' OR CommentBody LIKE '[ASSISTANT]%' OR CommentBody LIKE '[SYSTEM]%')
                ORDER BY CreatedDate ASC
            ];

            for (CaseComment comment : comments) {
                ChatMessage chatMsg = new ChatMessage();
                chatMsg.id = comment.Id;
                chatMsg.timestamp = comment.CreatedDate.format('HH:mm');

                // メッセージタイプを判定
                if (comment.CommentBody.startsWith('[USER]')) {
                    chatMsg.type = 'user';
                    chatMsg.text = comment.CommentBody.substring(6).trim();
                    chatMsg.isUser = true;
                } else if (comment.CommentBody.startsWith('[ASSISTANT]')) {
                    chatMsg.type = 'assistant';
                    chatMsg.text = comment.CommentBody.substring(11).trim();
                    chatMsg.isUser = false;
                } else if (comment.CommentBody.startsWith('[SYSTEM]')) {
                    chatMsg.type = 'system';
                    chatMsg.text = comment.CommentBody.substring(8).trim();
                    chatMsg.isUser = false;
                }

                chatMsg.containerClass = getContainerClass(chatMsg.type);
                chatMsg.messageClass = getMessageClass(chatMsg.type);

                chatHistory.add(chatMsg);
            }

            return chatHistory;
        } catch (Exception e) {
            throw new AuraHandledException('Error fetching chat history: ' + e.getMessage());
        }
    }

    private static String getContainerClass(String type) {
        if (type == 'user') {
            return 'slds-m-bottom_small slds-text-align_right';
        }
        return 'slds-m-bottom_small';
    }

    private static String getMessageClass(String type) {
        String baseClass = 'slds-box slds-box_x-small slds-p-around_small';
        if (type == 'user') {
            return baseClass + ' slds-theme_shade';
        } else if (type == 'error') {
            return baseClass + ' slds-theme_error';
        }
        return baseClass;
    }

    // チャットメッセージのラッパークラス
    public class ChatMessage {
        @AuraEnabled public String id;
        @AuraEnabled public String type;
        @AuraEnabled public String text;
        @AuraEnabled public String timestamp;
        @AuraEnabled public Boolean isUser;
        @AuraEnabled public String containerClass;
        @AuraEnabled public String messageClass;
    }
}