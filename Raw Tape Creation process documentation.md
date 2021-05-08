## Drip Monthly Data Tape Preparation

1.	Download  all system generated data tapes from the auto-email sent on month end. 
3.	Concatenate all the tapes together to form “Drip All”. 
4.	Move “Exporter Country” field from end of tape to between “Buyer” and “Buyer Country”.
5.	Move “Exporter ID” and “Buyer ID” fields from end of tape to between “Buyer” and “Exporter Country”
6.	Move “Buyer Grade” field from end of tape to between “Buyer Country” and “Product Exported Desc”.
7.	Move ‘Invoice Date’ field from end to between ‘Grace Period’ and ‘Anchor Event Date’
8.	Move “Other Adjustments” between “Setup Fee Charged” and “Total Fees” 
9.	Remove following unnecessary columns from “Drip All”:
	- Product Operation Category
	- Expected Tenor including Grace Period
	- Comments for 30+ DPD RF invoices
	- Comments (Other adjustments)
	- Set Offs
	- Set off comments
	- Sum of daily outstanding balance
	- Native values - Invoice value, Advance value, Payment Received
	- Approved LTM
	- Weighted Average Invoice Duration
	- Invoice IRR (Column to be added later from metabase query)

9.	Add in following new derived columns to “Drip All”:
	- Create In Vasco? column
	  - Between ‘Reference’ and ‘Exporter Name’ 
	  - Fill In Vasco? by vlookup from Vasco tracker
    - Advance Rate (Actual) = Advanced Value USD / Net Invoice Value USD
      - Between ‘Advanced Value USD’ and ‘Payment Received USD’ 
    - Open or Repaid Flag
      - Base it on invoice stage, not outstanding balance [Categorisation – All except “Settled”, “Pending Settlement” and "Auto-Settled" are open]
      - Between ‘LTM’ and ‘IRR’/’Yield’ *
    - Check “Payment Received USD” for blanks and make 0
    - The below 6 after 'Payment Received USD' : 
      - Invoice Value Received USD = MIN(Payment Received USD, Net Invoice Value USD) 
      - Principal/Advance Value Received USD = MIN(Payment Received USD, Advance Value USD) 
      - Dilution on Invoice Value USD = IF(Open,0,Net Invoice Value – Invoice Value Received) 
      - Advance Value Dilution = IF(Open,0,Advanced Value USD – Advanced Value Received)
      - Outstanding Invoice Value USD = (Net Invoice Value USD - Invoice Value Received USD – Dilution on Invoice Value USD) 
      - Outstanding Principal Balance USD = (Advance Value Received USD – Advanced Value USD – Dilution on Advance Balance USD) 
     - Create Invoice Yield at the very end 
     - Add “Modified Due Date Flag” field after “Insurable Flag” field
     - Add “Modified Due Date” and “New Due Date” fields after “Due Date” field
       - Lookup "Modified Due Date" from last data tape, AND
       - Check mails for any new extension agreements

10. Delete repeated invoice ID 72 (Keep the one with the NAs) 
11. VLOOKUP CORRECT BUYER NAMES FROM IDs USING this [query](https://data.dripcapital.com/question/2208) 
12.	VLOOKUP CORRECT EXPORTER NAMES FROM IDs USING this [query](https://data.dripcapital.com/question/1804)
13.	Make invoice ID 49 Flag “Repaid” and Stage as “Settled” 
14.	For Mx invoices, override Interest Rate and Step-up Interest Rate as: 
    - New Interest Rate = Old Interest Rate * (Net Invoice Value USD / Advanced Value USD) 
    - New Step Up Interest Rate = Old Step Up Interest Rate * (Net Invoice Value USD / Advanced Value USD) 

14.	Fill In Invoice Yield by Metabase [query](https://data.dripcapital.com/question/1685) (effective_interest_rate) followed by vlookup and division by 100 
    - Make Yield = NA for “Open” invoices 
15.	For invoices in “Pending Settlement” and “Auto-Settled” stage, change NAs in Fees and Interest (using metabase [query](https://data.dripcapital.com/question/1703)) 
16.	Check for cases where factoring fee rate / interest rate / step-up interest rate is non-zero but corresponding actual $ value charged is 0 and vice-versa. (keeping in mind outstanding tenor, size etc.)
    - Change Factoring Commission of invoices 18948, 17650,13196,11300, 11299, 9300, 9298, 3620, 2398 using this [query](https://data.dripcapital.com/question/1978). And dividing by 100 
    - Sometimes for Repaid invoices show an interest/factoring fee charged and then increase adjustment amount (eg: 17421, 1757) 
17.	Make Invoice ID 9610 as ‘Repaid’ (stage = “Settled”, Yields = 0%) 
18.	Correct invoice dates of following invoices by reducing by 1 month: 
    - Test failed: Invoice Date > First Advance Date
      - 4937
      - 4779
      - 4378
      - 4319
      - 3270
      - 3257
      - 3256
      - 2672
      - 1137
      - 948
      - 10793 – NO CHANGE be made
19.	Make Total LTM as ‘NA’ where 0 
20.	Change stage from NPA to Overdue where <90 and >0 days DQ from Due Date (New)
21.	Change stage from NPA/Overdue to Advanced/ETD Check /GUD Check where <=0 days DQ from Due Date (New)
    - Do ETD Check if Anchor Event is Discharge Date and dashboard agent check date > data tape date
    - Do GUD Check if Anchor Event is GUD and dashboard agent check date > data tape date
22.	Change Stage from “Advanced/GUD/ETD” to “Partial Payment” if Open, not DQ and Payment >0 
23.	Make Buyer Grade = “Pending” where Buyer Grade = 11 and “NA” where Blank 
    - If existing old NPA buyer, then 11 might need to become NA and not “Pending” (Eg: Bambino, East Ocean, Pure Life Foods)  
24.	Make Insurable Flag Blank where IF 
25.	Override columns Total Interest + Fees (With and Without Setup Fee) with summation formulae  
    - Factoring + Interest + Step Up Interest + Setup + Adjustments 
    - Make NA for Open Invoices 
26.	Make Factoring Fee as ‘NA’ for invoices in stage “Open” 
27.	Manually populate Anchor Event Date where blank
    - Lookup From prev. tape, OR
    - Due Date - Expected tenor from anchor event date 
29.	Override Full Payment Date and Actual Outstanding Tenor for following two invoices:
    - 2364: Full Payment Date = 10/25/2018, Actual Outstanding Tenor = 51
    - 7694: Full Payment Date = 09/23/2019, Actual Outstanding Tenor = 132
30.	Override column “Step Up Interest Rate Tenor including Holiday Grace” with below formula from dictionary:
    - “NA” for Open
    - Max(0, Outstanding Tenor – (Due Date (Old) – First Advance Date + Grace Period)) for “Repaid” 
31.	Rename currencies as usd -> USD, euro -> EUR and so on 
32.	Make “Release Net Payment to Exporter” and “Actual Outstanding Tenor” as NA (and not ‘-‘) for all “Open” invoices. 
33.	Make “Stage” as “Principal Repaid”, and populate Principal Payment Date from dashboard for invoices where principal is fully repaid but interest + fees in pending. 
34.	Add “Expected Tenor From Invoice Date” and “Expected Tenor From Advance Date” fields (Due Date (New) – Invoice Date / First Advance Date ) 
35.	In the “Credit Limit” sheet:
    - Keep only “Insured Limit”
    - Delete IF (Delete rows where “Insured Limit” is blank
    - Add in Buyer ID column 
    - Remove “Andre Prost Inc” and “Hathi Foods” (UAE invoice buyers) 
    - Correct Sl Nos by dragging and autofill 

35.	Run the following tests on the data: 
a.	Ranges of all columns
b.	Nulls and negatives (refer to  the google sheet)
c.	Date chronology 
d.	Nothing in the future
e.	Total count of invoices, Mx/Ind split, RF/IF split with dashboard/metabase
f.	Anchor Event Dates when Anchor Event is BL/Invoice Date
g.	Fees/Interest, Yield, Outstanding Balance, Stage when invoice is “Open”
h.	Quick cross checks with past formatted data tapes to see increase/decrease etc. 

36.	Change formatting by copying pasting into latest “Formatted Tape Skeleton” file 

37.	In the “Cashflow Statement” sheet, add in:

a.	Cashflow USD = Cashflow*Conversion
b.	Cashflow Month = EOMONTH(Cashflow Date,-1)+1
c.	Origination Month = EOMONTH(First Invoice Advanced Date,-1)+1






