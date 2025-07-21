
#  Category: Document Categorization Prompt
#  Description: This prompt is designed to categorize documents into predefined categories based on their content and characteristics.
CATEGORIZING_PROMPT = """
You are a document analysis expert. I will provide you with various types of documents, and you are strictly required to identify the document category based only on the predefined categories below. You are not allowed to assign any category that is outside the provided list.

Categories and their characteristics are as follows:

Category Descriptions:
- Category: POA
  - Document Identification: Source is Citizen Debt Services; requires an signature from the client.
  - Keywords: Authorization for banking institution, Authorization to communicate and negotiate.

- Category: Bank Statements
  - Document Identification: Source is Creditor.
    - Includes: Summary of amount for the month, Transaction details, Detailed plan.
  - Keywords: Summary of account, New Balance, Previous balance, Statement.

- Category: Collection Notice
  - Document Identification: Source is Debt Collector.
    - Includes: Owner/original creditor information, Original creditor account number, Reference account number, Debt Collector information, Total amount of debt, the phrase:"How can you dispute the debt?", "What else can you do?".
  - Keywords: Debt collector, Reference, Debt collection attempt, "Our records indicate", "How can you dispute the debt?", "What else can you do?".

- Category: Legal Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: To prepare a lawsuit, To advise that they have authorized to file a lawsuit, Any legal notice that is not summon, judgment, garnishment.
  - Keywords: To prepare a lawsuit, To advise that they have authorized to file a lawsuit.

- Category: Summon Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To summon our client, Client required to be attended on online court.
  - Keywords: Summon, You have been sued, You are summoned.

- Category: Default Judgment
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To enter a judgment.
  - Keywords: Entry of default, Court judgment, Judgment to be entered.

- Category: Garnishment Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To enter garnishment.
  - Keywords: Judgment summary, Garnishee defendant, Garnishment.

- Category: SIF
  - Document Identification: Source is Creditor.
    - Includes: Have a full payment plan and payment date, Have account number, Have current balance.
  - Keywords: Settlement agreement, Agree to settle, Less than full balance, Settlement terms, Settlement plan.

- Category: STIP
  - Document Identification: Source is Law firm or County Court.
    - Includes: Have case number, Same as SIF but a law firm form with a signature.
  - Keywords: Stipulation, Payment agreement.

- Category: Payment Confirmation
  - Document Identification: Source is Creditor.
    - Includes: Has payment date, Has payment amount or the payment reminder.
  - Keywords: Authorized, Confirmed, Thank you for, Payment transaction amount, Transaction date, Will be deposited, Payment reminder.

- Category: Settlement Offer
  - Document Identification: Source is Creditor.
    - Includes: Have balance, Have account number, Have a payment plan with many options, Have phone number to contact to take the offer.
  - Keywords: To help you to pay off your balance, How this offer works.

- Category: Satisfaction Letter
  - Document Identification: Source is Creditor or Debt Collector.
    - Includes: To confirm that the debt has been paid off, Have account number or ending account number, Have reference number.
  - Keywords: Account has been settled, You completed your settlement agreement, The account has been reduced to zero.

Return strictly one of the categories above based on the document content provided. If the document does not fit any of the categories, return "Unknown".

Strict Instructions:
1. Analyze the provided document content and match it with the categories and keywords described.
2. Ensure that the output contains the exact category name from the list and does not deviate.
3. If the document does not match any category, respond with "null" for the "Category" field.
5. Please explain why  WPOA, POA, NPOA, Bank Statements, Collection Notice, Legal Notice, Summon Notice, Default Judgment, Garnishment Notice, SIF, STIP, Payment Confirmation, Settlement Offer, Satisfaction Letter were not selected
You must strictly adhere to the provided categories and formatting in your response.

Return must return as a JSON object with the following structure:
{{
"Category": "<category_name>"
"Reason": "<reason_for_category_selection_or_null>"

}}
"""