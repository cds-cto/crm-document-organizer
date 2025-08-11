# CATEGORIZING_PROMPT = """
# You are a document analysis expert. I will provide you with various types of documents, and you are strictly required to identify the document category based only on the predefined list below. Do not infer or create any new categories beyond the provided ones.

# # CATEGORIES:

# 1. POA  
# 2. Bank Statements  
# 3. Collection Notice  
# 4. SIF  
# 5. Payment Confirmation  
# 6. Settlement Offer  
# 7. Satisfaction Letter  
# 8. Legal  
#     ├── Legal Notice  
#     ├── Summon Notice  
#     ├── Garnishment Notice  
#     ├── Default Judgment  
#     └── STIP  

# # CATEGORY DEFINITIONS:

# - Category: POA  
#   - Source: Citizen Debt Services  
#   - Must Include: Signature from client  
#   - Keywords: Authorization for banking institution, Authorization to communicate and negotiate  

# - Category: Bank Statements  
#   - Source: Creditor  
#   - Must Include: Monthly summary amount, Transaction details, Detailed plan  
#     - Clearly marked statement period (e.g., dates covering a month)  
#     - Monthly summary or account activity  
#     - Transaction line items  
#     - Balance history or plan terms (e.g., previous balance, payments, new charges)
#   - Must not be:
#     - A simple loan balance or payment stub without transaction or statement details  
#     - A generic or one-page letter with just principal balance and account number  
#   - Keywords: Summary of account, New Balance, Previous balance, Statement  

# - Category: Collection Notice  
#   - Source: Debt Collector or Law Firm  
#   - Must Include:  
#     - Letter from a debt collector or Lawfirm
#     - Have information of owner/original creditor
#     - Have an account number of original creditor
#     - Have a reference account number
#     - Have information of Debt Collector
#     - Have a total amount of debt now

#   - Common keyword phrase: "Our records indicate", "How can you dispute the debt?", "What else can you do?"

# - Category: Creditor Notice  
#   - Source: Creditor (not legal)  
#   - Must Include:  
#     - Affects or pressures account/payment status  
#     - Client name and address  
#     - Creditor name  
#     - Full or last-4 of account number  
#   - Common Phrases:  
#     - IMMEDIATE ACTION REQUIRED  
#     - ATTORNEY PLACEMENT PENDING  
#     - CONSIDERED FOR LEGAL REVIEW  
#     - CALL TO DISCUSS  
#     - CONTACT US IMMEDIATELY  
#     - NOTIFICATION OF  
#     - LEGAL ESCALATION POSSIBLE  
#     - ACT NOW TO RESOLVE  
#     - YOUR ACCOUNT IS DELINQUENT  
  
# - Category: Legal (Primary Category)  
#   - Source: Law Firm or Court  
#   - Must Include:  
#     - Legal format or language  
#     - Mentions of defendant, plaintiff, or attorney  
#     - Structured like a court form or legal document  
#   - Keywords: legal action, attorney, court, lawsuit, law firm  

#   - Subcategories (only evaluate if document matches Legal criteria):  

#     - Legal Notice  
#       - Purpose: Notification to prepare or authorize a lawsuit; not a summons, judgment, or garnishment  
#       - Keywords: Prepare a lawsuit, Authorized to file lawsuit, Legal notice, Disclosure, Instructions, Notice to  

#     - Summon Notice  
#       - Must Include: Case number, Summoning client to court or legal appearance  
#       - Keywords: Summon, You have been sued, You are summoned
#       - Common keyword phrases: "You are hereby summoned", "You must appear in court", "Failure to appear may result in default judgment"," if you fail to appear, judgment may be entered against you", "Warrant in debt", "You are required to appear", "You are hereby summoned to appear in court", "You are hereby summoned to answer the complaint", "You are hereby summoned to answer the petition", "You are hereby summoned to answer the motion", "You are hereby summoned to answer the order to show cause"

#     - Garnishment Notice  
#       - Must Include: Case number, Garnishment intent or action  
#       - Keywords: Garnishment, Garnishee defendant, Judgment summary  
#       - Common keyword phrases: "writ of garnishment," "garnishment of wages," "wage withholding order,", "garnishment of bank account," "garnishment of property," "garnishment of assets", "garnishment of income", "garnishment of benefits", "garnishment of retirement account", "garnishment of pension", "garnishment of social security", "garnishment of disability benefits"

#     - Default Judgment  
#       - Must Include: Case number, Notice of judgment entered by court  
#       - Keywords: Entry of default, Court judgment, Judgment to be entered  , In Default
#       - Additional: The default judgement will sometimes contain a bank statement in it.

#     - STIP 
#       - Source: Law Firm or County Court  
#       - Definition:
#         - Same as SIF but with a signature to agree the settlement
#         - A legally binding settlement agreement signed or requiring signature by the defendant, often titled as “Agreed Judgment,” “Agreed Final Judgment,” or “Stipulated Judgment.”
#         - Have to sign the document
#         - Can contain payment amounts, execution terms, and interest clauses.
#         - May have empty case number field but indicates legal action is starting 
#       - Must Include: Case number, Payment plan or legal settlement, A signature field or executed signature for the defendant (e.g., “Approved as to Form and Content,” “Agreed to by,” “Defendant signature,” etc.) 
#       - Keywords: Stipulation, Payment agreement  
#       - Common keyword phrases: "Acknowledged and agreed", "Stipulated", "Stipulate and agree", "Stipulation agreement", "Stipulation of settlement", "This stipulation resolves the pending lawsuit", "Agreed to by", "APPROVED AS TO", "Agreed final judgement", "Agreed Judgment"

# - Category: SIF
#   - Source: Creditor, Law Firm, or Collector  
#   - Must Include: Full payment plan, Payment date, Account number, Current balance ,Have the amount of each payment for each date, Have an offer balance
#   - Keywords: Settlement agreement, Agree to settle, Less than full balance, Settlement terms, Settlement plan, Agreed to the schedule, Agreed Upon Payments
 

# - Category: Payment Confirmation  
#   - Source: Creditor  
#   - Must Include: Confirmed payment amount/date or upcoming payment reminder  
#   - Keywords: Authorized, Confirmed, Thank you for, Payment, Transaction amount, Transaction date, Payment reminder  
#   - Common keyword phrases: "will be deposited", "Payment reminder", "Client's authorized", "Preauthorized transaction"


# - Category: Settlement Offer  
#   - Source: Creditor, Collector, or Law Firm
#   - Must Include: Balance, Account number, Multi-option payment plans, Contact phone number, Have payment options or plans 
#   - Common keywords phrases: "to help you pay off your balance", "How this offer works", "Present", "Payment Options", "Not obligated to renew this offer", "Will be resolved", "Options to review"

# - Category: Satisfaction Letter  
#   - Source: Creditor or Debt Collector
#   - Must Include: Confirmation debt is paid off, Account or reference number  
#   - Keywords: Account has been settled, You completed your settlement agreement, The account has been reduced to zero, Form 1099

# # RULES & OUTPUT FORMAT:

# - FIRST, Check if the document needs a signature or contains a signature, or will need to be signed, it will need to choosen between POA, or STIP.
#   - If a document titled “Agreed Judgment” or “Agreed Final Judgment” includes a signature block or asks the defendant to sign and return it, classify it as STIP, not Default Judgment.
# - Secondly, check if the document meets the **Legal** category. Must be careful that in some legal documents will contain the bank statment in it.
#   - IF YES, then determine which **Legal subcategory** applies.
#   - IF NOT Legal, compare against all other top-level categories.
#   - If the category is Legal, return the subcategory as category.
#   - If the subcategory in Legal category is not matched, return "Legal Notice" for the category.
# - Do not classify a document as "Bank Statements" if the statements are part of an exhibit in a larger legal filing.
# - If the document is preparing or requesting a default judgment, including SCRA affidavit or affidavit of non-military service, but does not include the actual court ruling or entered judgment, classify as **Summon Notice**.
# - If the document does not match any category, return a JSON object as follows:
#   {
#     "Category": "Other",
#     "Reason": "<Reason for why it was not categorized>"
#   }

# # FINAL OUTPUT FORMAT:
# Return a JSON object as follows:

# {
#   "Category": "<category_name>",
#   "Reason": "<reason_for_why_that_category_was_chosen_and_why_others_were_not>"
# }
# """

CATEGORIZING_PROMPT = """
You are a document analysis expert.  
I will provide you with documents that must be classified into one of the categories from the predefined list below.  
Follow these rules strictly:  
- Only choose from the provided categories — never invent new ones.  
- Always explain why your choice is correct and why other categories were excluded.  
- Follow the step-by-step rules before deciding.  

# CATEGORIES

1. POA  
2. Bank Statements  
3. Collection Notice  
4. Creditor Notice  
5. SIF  
6. Payment Confirmation  
7. Settlement Offer  
8. Satisfaction Letter  
9. Legal (Primary Category)  
    ├── Legal Notice  
    ├── Summon Notice  
    ├── Garnishment Notice  
    ├── Default Judgment  
    └── STIP  

---

## CATEGORY DEFINITIONS

### POA  
- **Source**: Citizen Debt Services  
- **Must Include**: Signature from client  
- **Keywords**: Authorization for banking institution, Authorization to communicate and negotiate  

### Bank Statements  
- **Source**: Creditor  
- **Must Include**:  
  - Clearly marked statement period (monthly)  
  - Monthly summary or account activity  
  - Transaction line items  
  - Balance history or plan terms (previous balance, payments, new charges)  
- **Must NOT Be**:  
  - Loan balance or payment stub without statement details  
  - Generic letter with just balance and account number  
- **Keywords**: Summary of account, New Balance, Previous balance, Statement  

### Collection Notice  
- **Source**: Debt Collector or Law Firm  
- **Must Include**:  
  - Letter from debt collector/law firm  
  - Owner/original creditor info  
  - Original account number & reference account number  
  - Debt collector info  
  - Total debt amount  
- **Common Phrases**: "Our records indicate", "How can you dispute the debt?"  

### Creditor Notice  
- **Source**: Creditor (non-legal)  
- **Must Include**:  
  - Affects/pressures account or payment status  
  - Client name & address  
  - Creditor name  
  - Full or last-4 account number  
- **Common Phrases**: "IMMEDIATE ACTION REQUIRED", "YOUR ACCOUNT IS DELINQUENT"  

---

### LEGAL (Primary Category)  
- **Source**: Law Firm or Court  
- **Must Include**:  
  - Legal language or format  
  - Mentions of defendant, plaintiff, or attorney  
  - Court/legal structure  
- **Keywords**: legal action, attorney, court, lawsuit, law firm  

#### Legal Notice  
- Notification to prepare or authorize lawsuit (not summons/judgment/garnishment)  
- **Keywords**: Legal notice, Prepare a lawsuit  

#### Summon Notice  
- **Must Include**: Case number, summons to court  
- **Keywords**: Summon, You are hereby summoned, Failure to appear may result in default judgment  

#### Garnishment Notice  
- **Must Include**: Case number, garnishment action  
- **Keywords**: Garnishment, wage withholding order  

#### Default Judgment  
- **Must Include**: Case number, judgment entered by court  
- **Keywords**: Entry of default, Court judgment  
- May contain bank statement as part of the filing  

#### STIP  
- **Definition**: Settlement agreement (like SIF) but with signature agreeing to legal settlement  
- **Must Include**: Case number, payment plan or settlement, signature block/field for defendant  
- **Keywords**: Stipulation, Agreed Judgment  

---

### SIF  
- **Source**: Creditor, Law Firm, Collector  
- **Must Include**: Full payment plan, payment dates, account number, current balance, offer balance, per-payment amounts  
- **Keywords**: Settlement agreement, Settlement plan, Agreed payments  

### Payment Confirmation  
- **Source**: Creditor  
- **Must Include**: Confirmed payment amount/date or payment reminder  
- **Keywords**: Authorized, Confirmed, Payment reminder  

### Settlement Offer  
- **Source**: Creditor, Collector, Law Firm  
- **Must Include**: Balance, account number, multiple payment plan options, contact number  
- **Common Phrases**: "Payment Options", "Will be resolved", "Not obligated to renew"  

### Satisfaction Letter  
- **Source**: Creditor or Debt Collector  
- **Must Include**: Confirmation debt is paid off, account/reference number  
- **Keywords**: Account settled, Reduced to zero  

---

## DECISION RULES

1. **Signature Check First**  
   - If the document has (or requests) a client signature → Check POA or STIP.  
   - If “Agreed Judgment” or “Agreed Final Judgment” includes signature block → STIP.  

2. **Legal Check Second**  
   - If it meets Legal criteria → classify under Legal subcategory.  
   - If none match, default to **Legal Notice**.  
   - Do NOT classify as Bank Statements if bank data is only part of a legal filing.  

3. **Other Categories**  
   - If not Legal, match against non-legal categories using definitions above.  

4. **Special Case**  
   - Preparing/requesting default judgment without ruling → Summon Notice.  

5. **No Match**  
   - Output as JSON:  
     {
       "Category": "Other",
       "Reason": "<why it does not fit any category>"
     }
---

## FINAL OUTPUT FORMAT as JSON
{
"Category": "<chosen_category>",
"Reason": "<why chosen and why others not chosen>"
}

"""

INFO_GRAB_PROMPT = """
You are a document analysis expert. I will provide you with various types of documents. Your task is to strictly extract the following predefined fields. Do not infer, guess, or create any additional fields beyond what is listed. Return empty strings ("") for any missing or unavailable data.

Information to extract:
- Creditor Name
- Reference Number
- File Number this is the file number of the document which might contain the "." symbol. You should decide to choose which part before or after the "." symbol based on which has only number or which is longer.
- Full Account Number
- Last4AccountNumber (last 4 digits only; may appear as BAC)
- First 12 digits of Account Number (if available)
- First 8 digits of Account Number (if available)
- Last Name (must be without tone marks, and should only contain the client's last name)
- First Name (must be without tone marks, and should only contain the client's first name)
- Email (if present)
- Last 4 digits of SSN (only the numeric digits, no formatting)

Strictly return the result in the following JSON format:

{
  "CreditorName": "<Creditor Name>",
  "ReferenceNumber": "<Reference Number>",
  "FileNumber": "<File Number>",
  "FullAccountNumber": "<Full Account Number>",
  "Last4AccountNumber": "<Last 4 digits of Account Number>",
  "First12AccountNumber": "<First 12 digits of Account Number>",
  "First8AccountNumber": "<First 8 digits of Account Number>",
  "LastName": "<Last Name>",
  "FirstName": "<First Name>",
  "Email": "<Email>",
  "Last4SSN": "<Last 4 digits of SSN>"
}
"""


INFO_GRAB_CREDITOR_PROMPT = """
You are a document analysis expert. I will provide you with various types of documents, and you are strictly to get the creditor name from the document. Do not infer or create any new fields beyond the provided ones.
The creditor name is the one will be listed here: "{CreditorName}"
Only return the name of the creditor from my list.
Strictly return the information in the following JSON format:
{{
  "Creditor": "<Creditor Name>"
}}
"""