public with sharing class SupportAssistantController {
    private static final String API_ENDPOINT = System.Label.SupportAssistantAPIEndpoint + '/dev/agent'; // APIエンドポイントを設定

    @AuraEnabled
    public static String analyzeCaseAndGetSupport(String caseId, String question) {
        try {
            // API リクエストボディの構築
            Map<String, Object> requestBody = new Map<String, Object>{
                'case_id' => caseId,
                'question' => question
            };

            HttpRequest req = new HttpRequest();
            req.setEndpoint(API_ENDPOINT);
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');
            req.setBody(JSON.serialize(requestBody));
            req.setTimeout(120000); // 2分のタイムアウト

            Http http = new Http();
            HttpResponse res = http.send(req);

            if (res.getStatusCode() == 200) {
                // 生のJSON文字列をそのまま返す
                return res.getBody();
            } else {
                throw new AuraHandledException('API Error: ' + res.getStatusCode() + ' - ' + res.getBody());
            }
        } catch (Exception e) {
            throw new AuraHandledException('Error analyzing case: ' + e.getMessage());
        }
    }


    @AuraEnabled
    public static Case getCaseDetails(String caseId) {
        try {
            return [
                SELECT Id, CaseNumber, Subject, Description, Status, Priority,
                       ContactId, Contact.Name, AccountId, Account.Name
                FROM Case
                WHERE Id = :caseId
                LIMIT 1
            ];
        } catch (Exception e) {
            throw new AuraHandledException('Error fetching case details: ' + e.getMessage());
        }
    }
}