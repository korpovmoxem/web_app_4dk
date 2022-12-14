from datetime import datetime
from calendar import monthrange

from fast_bitrix24 import Bitrix
import requests

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def create_deals_rpd(req):
    ignore_company_list = []
    months = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь',
    }
    current_month = months[datetime.now().month]
    current_year = datetime.now().year
    current_monthrange = monthrange(current_year, datetime.now().month)[1]

    # Получение массива сделок
    if req['employees'] == '':
        deals = b.get_all('crm.deal.list', {
            'select': ['ID', 'COMPANY_ID', 'ASSIGNED_BY_ID', 'TITLE'],
            'filter': {
                'UF_CRM_1657878818384': '859',
                'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6'],
                '!TYPE_ID': 'UC_GZFC63',
                'CATEGORY_ID': '1',
            }})
    else:
        id_list = set()
        id_employees = req['employees'].split(', ')  # Строка с сотрудниками и отделами в список
        for id in id_employees:
            if 'user' in id:  # Если в массиве найден id сотрудника
                id_list.add(id[5:])
            elif 'group' in id:  # Если в массиве найден id отдела
                department_users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': id[8:]}})
                for user in department_users:
                    id_list.add(user['ID'])
        id_list = list(id_list)
        deals = b.get_all('crm.deal.list', {
            'select': ['ID', 'COMPANY_ID', 'ASSIGNED_BY_ID', 'TITLE'],
            'filter': {
                'UF_CRM_1657878818384': '859',
                'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6'],
                'ASSIGNED_BY_ID': id_list,
                '!TYPE_ID': 'UC_GZFC63',
                'CATEGORY_ID': '1',
            }})

    # Разделение ID сделок по ответственному
    employees = {}
    for deal in deals:
        if deal['COMPANY_ID'] in ignore_company_list:
            continue
        data = {
            'filter': {
                'COMPANY_ID': deal['COMPANY_ID'],
                'TYPE_ID': 'UC_GZFC63'
            }}
        company_deals = requests.post(f"{webhook}crm.deal.list", json=data).json()['result']
        if company_deals:
            ignore_company_list.append(deal['COMPANY_ID'])
            continue
        employee = deal['ASSIGNED_BY_ID']   # Ответственный
        if employee not in employees:
            # Создание ключа с ID сотрудника и значение:
            # 0: ID сделки
            # 1: Название сделки
            # 2: ID компании
            employees.setdefault(employee, [[deal['ID'], deal['TITLE'], deal['COMPANY_ID']]])
        else:
            # Добавление ID сделки к значению dct
            employees[employee].append([deal['ID'], deal['TITLE'], deal['COMPANY_ID']])

    # Создание сделок
    for employee in employees:
        if employee not in ['None', None]:
            for deal in employees[employee]:
                company_id = deal[2]
                data = {
                    'select': ['ID'],
                    'filter': {'CATEGORY_ID': '13',
                               'COMPANY_ID': company_id
                               }}
                is_deal_exists = requests.post(f"{webhook}crm.deal.list", json=data).json()['result']
                if not is_deal_exists:

                    data = {
                        'fields': {
                            'TITLE': f"Работа с РПД (СМ)",
                            'ASSIGNED_BY_ID': employee,
                            'CREATED_BY': '173',
                            'COMPANY_ID': company_id,
                            'CATEGORY_ID': '13',
                            'CLOSEDATE': '2022-11-30',
                            'TYPE_ID': 'UC_4N16O3'
                        }}
                    requests.post(url=f"{webhook}crm.deal.add", json=data)



    b.call('im.notify.system.add', {'USER_ID': req['user_id'][5:], 'MESSAGE': f'Сделки на РПД созданы'})

