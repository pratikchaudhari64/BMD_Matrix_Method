import pandas as pd
import numpy as np


def new_interest_rates(df):
  df["Interest Rate"] = df["Interest Rate"] * \
      (df["Net Invoice Value USD"] / df["Advanced Value USD"])
  df["Step-up Interest Rate"] = df["Step-up Interest Rate"] * \
      (df["Net Invoice Value USD"] / df["Advanced Value USD"])
  return df


def rename_expected_to_actual(df):
  df.rename(
      columns={"Expected Outstanding Tenor": "Actual Outstanding Tenor",
               "Expected  Total Fees + Interest USD (Excluding Setup Fees)": "Actual  Total Fees + Interest USD (Excluding Setup Fees)"
               },
      inplace=True
  )
  return df


#------------------------------------------READING FILES-----------------------------------------------------------------------------
df_open_India = pd.read_csv('loan-tape-open_India.csv', header=3)
df_open_Mexico = pd.read_csv('loan-tape-open_Mexico.csv', header=3)
df_paid_India = pd.read_csv('loan-tape-paid_India.csv', header=3)
df_paid_Mexico = pd.read_csv('loan-tape-paid_Mexico.csv', header=3)
df_received_India = pd.read_csv('loan-tape-received_India.csv', header=3)
df_received_Mexico = pd.read_csv('loan-tape-received_Mexico.csv', header=3)


df_buyerID_name_map = pd.read_csv('buyer_ID-name_map.csv')
df_exporterID_name_map = pd.read_csv('exporter_ID-name_map.csv')
df_yield_invID_map = pd.read_csv('invoiceID-Yield_map.csv')

vasco_df = pd.read_csv(
    'VASCO Receivables and Portfolio Composition 05.03.2021 Post Buy.csv', header=16)

#---------------RENAMING 'Expected Outstanding Tenor' to 'Actual Outstanding Tenor' IN THE OPEN AND RECEIVED TAPES----------------------------
df_open_India = rename_expected_to_actual(df_open_India)
df_open_Mexico = rename_expected_to_actual(df_open_Mexico)
df_received_India = rename_expected_to_actual(df_received_India)
df_received_Mexico = rename_expected_to_actual(df_received_Mexico)

#-----------------OVERRIDE INTEREST CALCULATIONS FOR MEXICO INVOICES (13 in MANUAL)----------------------------------------------------------
df_open_Mexico = new_interest_rates(df_open_Mexico)
df_paid_Mexico = new_interest_rates(df_paid_Mexico)
df_received_Mexico = new_interest_rates(df_received_Mexico)

#---------------------------------MERGE THE 6 DATA TAPES TOGETHER---------------------------------------------------------------------------
df_loan_tape = pd.concat([df_open_India, df_open_Mexico, df_paid_Mexico, df_paid_India, df_received_Mexico, df_received_India],
                         ignore_index=True)


#------FINAL POSITION OF COLUMNS AFTER ALL MOVEMENTS DROPS (2-8 in Manual)-------------------------------------------------------------------------
df_loan_tape = df_loan_tape[["ID", "Reference", "Exporter", "Buyer", "Exporter Country", "Exporter ID",  "Buyer ID", "Buyer Country",
                             "Buyer Grade", "Product Exported Description/  HS Code",   "Currency", "Product Operations Category",
                             "Product Category", "Insurable Flag", "Net Invoice Value USD", "Anchor Event for Step Up Date",
                             "Expected Tenor from Anchor Event Date", "Grace Period", "Invoice Date", "Anchor Event Date",
                             "First Advance Date", "Due Date", "Step-up Interest Rate Start Date (Post Grace Period) including Holiday Grace",
                             "Principal Payment Date",   "Actual Outstanding Tenor",   "Expected Tenor Including Grace Period",
                             "Step-up Interest Rate Tenor including Holiday Grace",  "Comments for 30+DPD RF Invoices",  "Advance Rate",
                             "Factoring Commission", "Interest Rate",    "Step-up Interest Rate",    "Advanced Value USD",
                             "Payment Received USD", "Release Net Payment to Exporter USD",  "Factoring Fees USD",   "Interest Charges USD",
                             "Step-up Interest Charges USD", "Setup Fee booked on this invoice", "Other Adjustments USD",
                             "Total Fees + Interest USD (Including Setup Fee)",  "Actual  Total Fees + Interest USD (Excluding Setup Fees)",
                             "Comments (Other Adjustments)", "stage",    "Set offs", "Set offs Comments",    "Wtd. Avg Invoice Duration",
                             "Invoice IRR (excluding setup fee) based on Wtd. Duration", "Sum of daily outstanding balance", "Full Payment Date",
                             "BL Date",  "HS Code Description",  "Total LTM",    "Approved LTM", "Net Invoice Value",    "Advanced Value",
                             "Payment Received"]]

df_loan_tape = df_loan_tape.drop(["Product Operations Category", "Expected Tenor Including Grace Period", "Comments for 30+DPD RF Invoices",
                                  "Comments (Other Adjustments)", "Set offs", "Set offs Comments", "Sum of daily outstanding balance", "Net Invoice Value",
                                  "Advanced Value", "Payment Received", "Approved LTM", "Wtd. Avg Invoice Duration",
                                  "Invoice IRR (excluding setup fee) based on Wtd. Duration"], axis=1)

#------------------------------CREATE 'IN VASCO' COLUMN (9.A IN MANUAL)--------------------------------------------------------

vasco_df.drop(["*"], axis=1, inplace=True)

vasco_inv = vasco_df["Invoice ID"].to_numpy()

In_Vasco = []
for i in range(df_loan_tape["ID"].size):
  if (df_loan_tape.iloc[i, 0] in vasco_inv):
    In_Vasco.append("Yes")
  else:
    In_Vasco.append("No")

In_Vasco_series = pd.Series(In_Vasco)
df_loan_tape.insert(2, "In Vasco?", In_Vasco_series)

#-------------RENAME EXISTING ADVANCE RATE COLUMN TO 'MAX ADVANCE RATE'--------------------------------------------------------
df_loan_tape.rename(
    columns={"Advance Rate": "Max. Advance Rate"},
    inplace=True)

#------------------------ADVANCE RATE(ACTUAL) COLUMN (9.B IN MANUAL)-----------------------------------------------------------------
adv_rate_series = df_loan_tape["Advanced Value USD"] / \
    df_loan_tape["Net Invoice Value USD"]
df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD"), "Advance Rate", adv_rate_series)

#--------------------ADDING OPEN OR REPAID FLAG (9.C IN MANUAL)-------------------------------------------------------------------
open_repaid = []
for i in range(df_loan_tape["stage"].size):
  i_stage = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("stage")]
  if((i_stage == "Settled") or (i_stage == "Pending Settlement") or (i_stage == "Auto Settled")):
    open_repaid.append("Repaid")
  else:
    open_repaid.append("Open")

df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Total LTM") + 1, "Open or Repaid flag", open_repaid)

#-----------------------------REPLACE BLANKS WITH '0' FROM PAYMENT RECEIVED COLUMN (9.D IN MANUAL)---------------------------------------
df_loan_tape["Payment Received USD"] = df_loan_tape["Payment Received USD"].replace(
    np.nan, 0)

#-----------------------CALCULATE AND ADD INVOICE VALUE AND ADVANCE RECEIVED COLUMNS (9.F & 9.G IN MANUAL)-------------------------------------------------------------
invoice_val_rcvd = []
adv_val_rcvd = []
for i in range(df_loan_tape["Payment Received USD"].size):
  i_pymnt_rcvd = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Payment Received USD")]
  i_inv_val = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Net Invoice Value USD")]
  i_adv_val = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Advanced Value USD")]
  invoice_val_rcvd.append(min(i_pymnt_rcvd, i_inv_val))
  adv_val_rcvd.append(min(i_pymnt_rcvd, i_adv_val))

df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 1, "Invoice Value Received USD", invoice_val_rcvd)

df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 2, "Advanced Value Received USD", adv_val_rcvd)

#----------------------CALCULATE AND ADD DILUTION ON INV. AND DILUTION ON ADV. VALUE COLUMNS (9.H & 9.I IN MANUAL)----------------------------
dil_inv_val = []
dil_adv_val = []
for i in range(df_loan_tape["ID"].size):
  if (df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Open or Repaid flag")] == "Repaid"):
    dilution_inv = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Net Invoice Value USD")] - df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Invoice Value Received USD")]
    dilution_adv = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Advanced Value USD")] - df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Advanced Value Received USD")]
  else:
    dilution_inv = 0
    dilution_adv = 0
  dil_inv_val.append(dilution_inv)
  dil_adv_val.append(dilution_adv)

df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 3, "Dilution on Invoice Value USD", dil_inv_val)

df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 4, "Dilution on Advanced Value USD", dil_adv_val)

#------CALCULATE AND ADD OUTSTANDING INVOICE AND OUTSTANDING ADVANCE VALUE COLUMNS (9.J & 9.K IN MANUAL)----------------------------------------
os_inv_val = []
os_adv_val = []
for i in range(df_loan_tape["ID"].size):
  net_inv_val = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Net Invoice Value USD")]
  inv_val_rec = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Invoice Value Received USD")]
  inv_val_dil = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Dilution on Invoice Value USD")]
  os_inv_val.append(net_inv_val - inv_val_rec - inv_val_dil)

  adv_val = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Advanced Value USD")]
  adv_val_rec = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Advanced Value Received USD")]
  adv_val_dil = df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
      "Dilution on Advanced Value USD")]
  os_adv_val.append(adv_val - adv_val_rec - adv_val_dil)


df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 5, "Outstanding Invoice Value USD", os_inv_val)
df_loan_tape.insert(df_loan_tape.columns.get_loc(
    "Payment Received USD") + 6, "Outstanding Advanced Value USD", os_adv_val)

#----------CORRECTED BUYER AND EXPORTER NAMES FROM SQL QUERY (10 & 11 IN MANUAL)---------------------------------------
old_buyer_ID = df_loan_tape["Buyer ID"]
old_buyer_ID.rename("id", inplace=True)

correct_buyer_mapping = pd.merge(
    old_buyer_ID, df_buyerID_name_map, on='id', how='left')
correct_exporter_mapping = pd.merge(
    df_loan_tape["Exporter ID"], df_exporterID_name_map, on='Exporter ID', how='left')

df_loan_tape["Buyer"] = correct_buyer_mapping["company"]
df_loan_tape["Exporter"] = correct_exporter_mapping["Exporter Name"]

#------------FILL INVOICE YIELD FROM SQL QUERY AND MAKE "NA" FOR "OPEN" INVOICES (14 & 14.A IN MANUAL)--------------------------
old_inv_ID = df_loan_tape["ID"]
old_inv_ID.rename("id", inplace=True)
invoice_yield = pd.merge(old_inv_ID, df_yield_invID_map[[
                         "id", "effective_interest_rate"]], on='id', how='left')
df_loan_tape["Invoice Yield"] = invoice_yield['effective_interest_rate'] / 100

for i in range(df_loan_tape["Open or Repaid flag"].size):
  if(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Open or Repaid flag")] == "Open"):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Invoice Yield")] = "NA"

#-------------MAKE TOTAL LTM "NA" WHEREVER "0" (19 IN MANUAL) -------------------------------
for i in range(df_loan_tape["ID"].size):
  if(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Total LTM")] == 0):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Total LTM")] = "NA"

#-------------BUYER GRADE 11 AS "PENDING" AND BLANK AS "NA" (ONLY 23 IN MANUAL)----------------------------
for i in range(df_loan_tape["ID"].size):
  if(pd.isnull(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Buyer Grade")])):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Buyer Grade")] = "NA"
  if(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Buyer Grade")] == 11):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Buyer Grade")] = "Pending"

#-------------------INSURABLE FLAG AS BLANK FOR IF (24 IN MANUAL)-------------------------------
for i in range(df_loan_tape["ID"].size):
  if(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Product Category")] == "IF"):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Insurable Flag")] = ""

#----------------FACTORING FEE "NA" FOR "OPEN" INVOICES (26 IN MANUAL)---------------------------------------------
for i in range(df_loan_tape["ID"].size):
  if(df_loan_tape.iloc[i, df_loan_tape.columns.get_loc("Open or Repaid flag")] == "Open"):
    df_loan_tape.iloc[i, df_loan_tape.columns.get_loc(
        "Factoring Fees USD")] = "NA"


df_loan_tape.to_excel('tape_v1_05.03.2021.xlsx')
