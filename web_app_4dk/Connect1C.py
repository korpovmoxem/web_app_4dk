import json

from fast_bitrix24 import Bitrix
import dateutil.parser
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

from web_app_4dk.authentication import authentication

b = Bitrix(authentication('Bitrix'))

# Словарь кодов 1с-коннект

connect_codes = {
1: 'Текстовое сообщение',
17: 'Оценка работы специалиста',
20: 'Начало звонка с открытием обращения',
21: 'Начало звонка без открытия обращения',
22: 'Удачное завершение звонка',
23: 'Неудачное завершение звонка. Вызов отменен инициатором',
24: 'Неудачное завершение звонка. Абонент не ответил',
25: 'Неудачное завершение звонка. Нет свободных специалистов',
26: 'Неудачное завершение звонка. Вызов отклонен адресатом',
27: 'Перевод звонка на специалиста',
28: 'Перевод звонка в компанию вендора',
30: 'Перевод звонка без завершения (когда абонент не взял трубку, а сразу перевел звонок)',
31: 'Перевод звонка без завершения на вендора (когда абонент не взял трубку, а сразу перевел звонок)',
32: 'Нет соединения с голосовым сервером',
36: 'Неудачное завершение. У абонента нет аудио устройства',
38: 'Недоступная линия по звонку (нерабочее время)',
70: 'Файл',
50: 'Начало сеанса удаленного доступа с сервисным специалистом',
51: 'Начало сеанса удаленного доступа без сервисного специалиста (Специалист принудительно назначается пользователю сеансом удаленного доступа)',
52: 'Окончание сеанса удаленного доступа с передачей файлов',
53: 'Окончание сеанса удаленного доступа без передачей файлов',
54: 'Неудачное завершение удаленного доступа. Сеанс отменен инициатором',
55: 'Неудачное завершение удаленного доступа. Сеанс отклонен принимающим',
56: 'Неудачное завершение удаленного доступа. Сеанс не состоялся по таймауту',
57: 'Неудачное завершение удаленного доступа',
59: 'Неудачное завершение - устаревшая версия службы',
60: 'Неудачное завершение - служба не установлена',
61: 'Неудачное завершение - устаревшие версии компонентов',
62: 'Неудачное завершение - отсутствуют файлы компонентов УД',
80: 'Начало обращения. Инициатор пользователь',
81: 'Начало обращения. Инициатор специалист',
82: 'Завершение работы специалиста (Закрытие обращения)',
83: 'Обращение поступило в очередь. Нет свободных специалистов',
84: 'Перевод обращения на специалиста',
85: 'Перевод обращения в компанию вендора',
86: 'Для обращения в очереди появился свободный специалист',
87: 'Недоступность линии (нерабочее время)',
88: 'Недоступность линии по переводу. При переводе обращения в компанию вендора попали в нерабочее время',
89: 'Перевод в другую линию поддержки',
90: 'Обращение закрыто автоматически по отсутствию активности в чате',
91:  'Обращение закрыто автоматически, т.к. удалена линия поддержки',
92: 'Обращение закрыто автоматически, т.к. удалена подписка пользователя',
93: 'Обращение закрыто автоматически, т.к. удален пользователь',
200: 'Перевод обращения специалистом на бота',
}


def time_handler(time: str) -> str:
    time = dateutil.parser.isoparse(time)
    message_time = f"{time.hour}:{time.minute}:{time.second} {time.day}.{time.month}.{time.year}"
    return message_time


def get_employee_id(name: str) -> str:
    name = name.split()
    employee_id = b.get_all('user.get', {'filter': {'NAME': name[0], 'LAST_NAME':name[1]}})
    try:
        return employee_id[0]['ID']
    except:
        return '311'


def get_event_info(event: dict) -> str:
    if event['message_type'] == 1:
        return f"{event['text']}\n"
    if event['message_type'] == 70:
        return f"{event['file']['file_name']}\n{event['file']['file_path']}\n"
    if event['message_type'] == 82:
        return f"Длительность обращения: {event['treatment']['treatment_duration']}\n"
    return f"\n"


def get_name(user_id):
    session = Session()
    session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
    client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                    transport=Transport(session=session))

    specialists = client.service.SpecialistRead('Params')
    for specialist in specialists[1]['Value']['row']:
        if user_id == specialist['Value'][0]:
            user_name = f"{specialist['Value'][3]} {specialist['Value'][4]}"
            return [user_name]
    company_users = client.service.ClientUserRead('Params')
    companies = client.service.ClientRead('Params')
    for user in company_users[1]['Value']['row']:
        if user_id == user['Value'][0]:
            company_id = user['Value'][1]
            user_name = f"{user['Value'][4]} {user['Value'][5]}"
            for company in companies[1]['Value']['row']:
                if company_id == company['Value'][0]:
                    inn = company['Value'][4]
                    try:
                        company_id = b.get_all('crm.company.list', {'select': ['ID'], 'filter': {'UF_CRM_1656070716': inn}})[0]['ID']
                    except:
                        b.call('tasks.task.add', {
                            'fields': {
                                'TITLE': '1С:Коннект Не найдена компания по ИНН',
                                'DESCRIPTION': f"ID компании: {company_id}\nИНН: {inn}",
                                'CREATED_BY': '173',
                                'RESPONSIBLE_ID': '311',
                                'GROUP_ID': '13',
                            }})
                        company_id = '12'
                    return [user_name, company_id]



def connect_1c(req):
    # Запись события в логи
    with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'r') as file:
        data = json.load(file)
        data.append(req)
        with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    # Начало обращения. Создание задачи
    if req['message_type'] in [80, 81]:

        # Проверка была ли задача уже создана
        is_task_created = b.get_all('tasks.task.list', {
            'select': ['ID'],
            'filter': {
                'UF_AUTO_499889542776': req['treatment_id']}})
        if is_task_created:
            return

        task_text = ''
        with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'r') as file:
            data = json.load(file)
        for event in data:
            if event['treatment_id'] == req['treatment_id'] and event['message_type'] == 1:
                task_text = event['text']
                break
        message_time = time_handler(req['message_time'])
        user_info = get_name(req['user_id'])
        support_info = get_name(req['author_id'])
        support_id = get_employee_id(support_info[0])

        b.call('tasks.task.add', {'fields': {
            'TITLE': f"Коннект",
            'DESCRIPTION': f"{message_time} {user_info[0]}\n{task_text}",
            'GROUP_ID': '13',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': '311',
            'UF_CRM_TASK': [f"CO_{user_info[1]}"],
            'UF_AUTO_499889542776': req['treatment_id']
        }})

    # Смена ответственного
    elif req['message_type'] in [84]:
        pass

    # Завершение обращения. Закрытие задачи
    elif req['message_type'] in [82, 90]:
        task_text = ''
        treatment_id = req['treatment_id']
        user_info = get_name(req['user_id'])
        support_info = get_name(req['author_id'])
        user_names = {
            req['user_id']: user_info[0],
            req['author_id']: support_info[0],
        }

        with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'r') as file:
            data = json.load(file)
        event_count = 0
        for event in data:
            if event['treatment_id'] == treatment_id and event['message_type'] not in [80, 81]:
                event_count += 1
                if event_count < 2:
                    continue
                task_text += f"{time_handler(event['message_time'])} {user_info[event['author_id']]}\n{connect_codes[event['message_type']]}\n\n"
                task_text += f"{get_event_info(event)}\n"



        task_to_update = b.get_all('tasks.task.list', {
            'select': ['ID', 'RESPONSIBLE_ID'],
            'filter': {
                'UF_AUTO_499889542776': req['treatment_id']}})

        if task_to_update:
            task_to_update = task_to_update[0]
            b.call('tasks.task.update', {'taskId': task_to_update['id'], 'fields': {'STATUS': '3'}})
            b.call('task.commentitem.add', [task_to_update['id'], {'POST_MESSAGE': task_text, 'AUTHOR_ID': task_to_update['responsibleId']}], raw=True)




