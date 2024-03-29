import base64
import os
from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix
import openpyxl

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_company_without_connect_report(req):
    date_filter_end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    filter_month = str(datetime.now().month - int(req['months']))
    if len(filter_month) == 1:
        filter_month = '0' + filter_month
    date_filter_start = f'{datetime.now().year}-{filter_month}-01'

    tasks = b.get_all('tasks.task.list', {
        'select': ['GROUP_ID', 'UF_CRM_TASK'],
        'filter': {
            'GROUP_ID': ['7', '1'],
            '>=CREATED_DATE': date_filter_start,
            '<CREATED_DATE': date_filter_end,
            '!UF_CRM_TASK': False,
        }})

    contacts = b.get_all('crm.contact.list', {
        'select': ['ID', 'COMPANY_ID', 'NAME', 'SECOND_NAME', 'LAST_NAME'],
        'filter': {
            'UF_CRM_1666098408': ['0', None],
        }})

    companies = b.get_all('crm.company.list', {
        'select': ['ID', 'TITLE'],
        'filter': {
            'ID': list(map(lambda x: x['COMPANY_ID'], contacts))
        }})

    data_to_write = [
        [f'Выбрано месяцев: {req["months"]} (с {date_filter_start} по {date_filter_end})'],
        ['Контакт', 'Компания', 'Обращения на ЛК', 'Обращения на ТЛП']
    ]

    for contact in contacts:
        fio = f'{contact["LAST_NAME"]} {contact["NAME"]} {contact["SECOND_NAME"]}'.strip('None').strip()
        lk_tasks_count = len(list(filter(lambda x: x['groupId'] == '7' and 'C_' + contact['ID'] in x['ufCrmTask'], tasks)))
        tlp_tasks_count = len(list(filter(lambda x: x['groupId'] == '1' and 'C_' + contact['ID'] in x['ufCrmTask'], tasks)))

        if any([lk_tasks_count, tlp_tasks_count]):
            company_name = list(filter(lambda x: contact['COMPANY_ID'] == x['ID'], companies))
            if company_name:
                company_name = company_name[0]['TITLE']
            else:
                company_name = ''
            data_to_write.append([fio, company_name, lk_tasks_count, tlp_tasks_count])

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for data in data_to_write:
        worksheet.append(data)
    create_time = datetime.now().strftime('%d-%m-%Y-%f')
    report_name = f'Отчет_по_обращениям_контактов_без_Коннекта_{create_time}.xlsx'
    workbook.save(report_name)

    bitrix_folder_id = '443345'
    with open(report_name, 'rb') as file:
        report_file = file.read()
    report_file_base64 = str(base64.b64encode(report_file))[2:]
    upload_report = b.call('disk.folder.uploadfile', {
        'id': bitrix_folder_id,
        'data': {'NAME': report_name},
        'fileContent': report_file_base64
    })
    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'Отчет по обращениям контактов без Коннекта сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)
