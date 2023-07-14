from datetime import datetime, timedelta
from time import time

from web_app_4dk.tools import send_bitrix_request


def check_similar_tasks_this_hour(task_info, company_id):
    users_id = [task_info['createdBy'], '1']
    if task_info['groupId'] not in ['1', '7']:
        return
    group_names = {
        '1': 'ТЛП',
        '7': 'ЛК',
    }
    end_time_filter = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time_filter = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    similar_tasks = send_bitrix_request('tasks.task.list', {
        'filter': {
            '!ID': task_info['id'],
            '>=CREATED_DATE': start_time_filter,
            '<CREATED_DATE': end_time_filter,
            'GROUP_ID': task_info['groupId'],
            'UF_CRM_TASK': ['CO_' + company_id]
        }
    })
    if similar_tasks:
        similar_tasks = similar_tasks['tasks']
    else:
        return
    similar_tasks_url = '\n'.join(tuple(map(lambda x: f"https://vc4dk.bitrix24.ru/workgroups/group/{task_info['groupId']}/tasks/task/view/{x['id']}/", similar_tasks)))
    if similar_tasks:
        for user_id in users_id:
            send_bitrix_request('im.notify.system.add', {
                'USER_ID': user_id,
                'MESSAGE': f"Для текущей компании в группе {group_names[task_info['groupId']]} уже были поставлены задачи за прошедший час\n"
                           f"Новая задача: https://vc4dk.bitrix24.ru/workgroups/group/{task_info['groupId']}/tasks/task/view/{task_info['id']}/\n\n"
                           f"Поставленные ранее:\n {similar_tasks_url}"
            })


def task_registry(task_info):
    task_status = {
        "2": 343,
        "-1": 345,
        "-3": 347,
        "3": 349,
        "4": 351,
        "5": 353,
        "6": 355,
    }
    tags = send_bitrix_request('task.item.gettags', {'taskId': '187531'})
    if tags:
        tags = ', '.join(tags)
    else:
        tags = ''
    registry_element = send_bitrix_request('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '107',
        'FILTER': {
            'PROPERTY_517': task_info['id'],
        }
    })
    if registry_element:
        registry_element = registry_element[0]
        send_bitrix_request('lists.element.update', {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "107",
            "ELEMENT_ID": registry_element['ID'],
            "FIELDS": {
                "NAME": task_info["title"],
                "PROPERTY_517": task_info['id'],
                "PROPERTY_495": task_status[task_info['status']],
                "PROPERTY_499": registry_element['PROPERTY_499'] if 'PROPERTY_499' in registry_element else '',
                "PROPERTY_501": registry_element['PROPERTY_501'] if 'PROPERTY_501' in registry_element else '',
                "PROPERTY_537": registry_element['PROPERTY_537'] if 'PROPERTY_537' in registry_element else '',
                "PROPERTY_505": task_info["createdDate"],
                "PROPERTY_507": task_info["closedDate"],
                "PROPERTY_509": task_info["createdBy"],
                "PROPERTY_511": task_info["responsibleId"],
                "PROPERTY_515": tags,
                "PROPERTY_513": task_info["durationFact"],
            }})
    else:
        groups = send_bitrix_request('sonet_group.get')
        group_name = list(filter(lambda x: task_info['groupId'] == x['ID'], groups))[0]['NAME']
        company_id = ''
        contact_id = ''
        if 'ufCrmTask' in task_info and task_info['ufCrmTask']:
            ufCrmCompany = list(filter(lambda x: 'CO_' in x, task_info['ufCrmTask']))
            if ufCrmCompany:
                company_id = ufCrmCompany[0]
            ufCrmContact = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
            if ufCrmContact:
                contact_id = ufCrmContact[0]
        send_bitrix_request('lists.element.add', {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "107",
            "ELEMENT_CODE": time(),
            "FIELDS": {
                "NAME": task_info["title"],
                "PROPERTY_517": task_info['id'],
                "PROPERTY_495": task_status[task_info['status']],
                "PROPERTY_499": company_id,
                "PROPERTY_501": contact_id,
                "PROPERTY_537": group_name,
                "PROPERTY_505": task_info["createdDate"],
                "PROPERTY_507": task_info["closedDate"],
                "PROPERTY_509": task_info["createdBy"],
                "PROPERTY_511": task_info["responsibleId"],
                "PROPERTY_515": tags,
                "PROPERTY_513": task_info["durationFact"],
            }})


def fill_task_title(req, event):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = send_bitrix_request('tasks.task.get', {
        'taskId': task_id,
        'select': ['*', 'UF_*']
    })
    if not task_info or 'task' not in task_info or not task_info['task']:
        return
    task_info = task_info['task']
    task_registry(task_info)
    '''
    if task_info['closedDate'] and task_info['ufAuto934103382947'] != '1':
        send_notification(task_info, 'Завершение')
    '''

    if 'ufCrmTask' not in task_info or not task_info['ufCrmTask']:
        return

    company_crm = list(filter(lambda x: 'CO' in x, task_info['ufCrmTask']))
    uf_crm_task = []
    if not company_crm:
        contact_crm = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
        if not contact_crm:
            return
        contact_crm = contact_crm[0][2:]
        contact_companies = list(map(lambda x: x['COMPANY_ID'], send_bitrix_request('crm.contact.company.items.get', {'id': contact_crm})))
        if not contact_companies:
            return
        contact_companies_info = send_bitrix_request('crm.company.list', {
            'select': ['UF_CRM_1660818061808'],     # Вес сделок
            'filter': {
                'ID': contact_companies,
            }
        })
        if contact_companies_info:
            for i in range(len(contact_companies_info)):
                if not contact_companies_info[i]['UF_CRM_1660818061808']:
                    contact_companies_info[i]['UF_CRM_1660818061808'] = 0
            best_value_company = list(sorted(contact_companies_info, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID']
            uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm]
            company_id = best_value_company
    else:
        company_id = company_crm[0][3:]

    if event == 'ONTASKADD':
        check_similar_tasks_this_hour(task_info, company_id)


    company_info = send_bitrix_request('crm.company.get', {
        'ID': company_id,
    })
    if company_info and company_info['TITLE'].strip() in task_info['title']:
        return

    if not uf_crm_task:
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
            }})
    else:
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                'UF_CRM_TASK': uf_crm_task,
            }})
    return task_info


def send_notification(task_info, notification_type):
    users_notification_list = ['339', '311']
    if not task_info or not task_info['auditors']:
        return
    auditors = task_info['auditors']
    task_id = task_info['id']
    flag = False
    for user in users_notification_list:
        if user in auditors:
            if notification_type == 'Создание':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '311',
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
            elif notification_type == 'Завершение':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '311',
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                if not flag:
                    send_bitrix_request('tasks.task.update', {'taskId': task_info['id'], 'fields': {'UF_AUTO_934103382947': '1'}})
                    flag = True


def task_handler(req, event=None):
    task_info = fill_task_title(req, event)
    '''
    send_notification(task_info, 'Создание')
    '''
