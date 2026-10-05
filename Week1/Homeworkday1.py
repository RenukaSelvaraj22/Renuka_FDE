import csv

totalinvoicesread=0
invoices_over100000=0
invoices_invalidamount=0
with open(r'C:\Users\renuk\OneDrive\Desktop\FDE\WK1\homework_invoices.csv',mode='r') as file:
    reader = csv.DictReader(file)

    for row in reader:

        totalinvoicesread+=1
        vendor = row["vendor"]
        amount = row["amount"]
        status = row["status"]

        
        try:
            invoice_amount=float(row['amount'])

            if vendor != "":
                print(f'Vendor: {row["vendor"]}, Amount: {row["amount"]}, Status: {row["status"]}')

            if invoice_amount>100000:
                        print(f'Invoice amount {invoice_amount} is greater than 100,000')
                        invoices_over100000+=1


        except ValueError:
              invoices_invalidamount+=1
            
                       
        
            
print(f'Total invoices: {totalinvoicesread}')
print(f'Total invoices with amount greater than 100,000: {invoices_over100000}')
print(f'Total invoices with invalid amount:{invoices_invalidamount}')