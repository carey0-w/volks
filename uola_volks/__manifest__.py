{
    "name" : "Uola Prima Sejahtera",
    "author" : "admin",
    "summary" : "Office System Management",
    "depends" : ['mail', 'base', 'project', 'sale', 'account', 'product'],
    "sequence" : -1000,
    "data" : [
            "security/ir.model.access.csv",
            "data/sequence.xml",
            "views/menu.xml",
            "views/sales.xml",
            "views/invoice.xml",
            "views/invoice_content.xml",
            "views/sales_main.xml",
            "reports/report.xml",
        ],
    
    'application' : True,
    'installable' : True,
    'autoinstal' : False,
}