import xlwt
import csv

def write_excel(target):
    workbook = xlwt.Workbook(encoding = 'utf-8')
    worksheet = workbook.add_sheet('data')
    excelfilename = 'data.xls'

    csvfilename = target + '.csv'
    csvfile = open(csvfilename, 'r')
    reader = csv.reader(csvfile)

    worksheet.write(0,0,'ID')
    worksheet.write(0,1,'TITLE')
    worksheet.write(0,2,'DOI')
    worksheet.write(0,3,'URL')
    worksheet.write(0,4,'AUTHORS')
    worksheet.write(0,5,'KEYWORDS')
    worksheet.write(0,6,'ABSTRACT')

    i = 1
    for item in reader:
        if item[1] == '':
            continue
        for j in range(0,7):
            worksheet.write(i,j,item[j])
        i += 1

    workbook.save(excelfilename)
    csvfile.close()

if __name__ == '__main__':
    write_excel('20180801154036')